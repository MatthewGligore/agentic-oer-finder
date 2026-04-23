"""
Flask API Backend for Agentic OER Finder
Provides REST API endpoints for the React frontend
"""
from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS
import json
import logging
import os
from queue import Empty, Queue
import sys
import re
import threading
from datetime import datetime, timezone
from .oer_agent import OERAgent
from .config import Config
from .scrapers.library_index_scraper import fetch_library_index, fetch_library_index_for_course
from .scrapers.syllabus_content_scraper import fetch_and_parse_syllabus, prepare_section_records
from .llm.supabase_client import get_supabase_client

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for API endpoints (allow requests from React frontend)
CORS(app, resources={r"/api/*": {"origins": Config.CORS_ALLOWED_ORIGINS}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agent
agent = None
COURSE_CODE_PATTERN = re.compile(r'^[A-Z]{2,6}[- ]?\d{3,4}[A-Z]?$')
DEMO_MAX_SYLLABI_PER_SCRAPE = max(1, int(getattr(Config, 'DEMO_MAX_SYLLABI_PER_SCRAPE', 10)))
DEMO_MAX_OER_PER_SEARCH = max(1, int(getattr(Config, 'DEMO_MAX_OER_PER_SEARCH', 10)))


def is_valid_course_code(course_code: str) -> bool:
    return bool(COURSE_CODE_PATTERN.match((course_code or '').strip().upper()))

def get_agent():
    """Get or create OER agent instance"""
    global agent
    # Always create a fresh agent to avoid caching issues
    try:
        agent = OERAgent()
        logger.info("Created new OER Agent instance")
    except Exception as e:
        logger.error(f"Failed to initialize OER Agent: {e}")
        raise
    return agent


def _get_saved_by_url(course_code: str) -> dict:
    sb = get_supabase_client()
    if not sb.is_available():
        return {}
    saved_rows = sb.list_saved_resources(course_code)
    return {row.get('resource_url'): row for row in saved_rows}


def _normalize_evaluated_resource(item: dict, rank: int, saved_by_url: dict) -> dict:
    resource = item.get('resource', {})
    rubric = item.get('rubric_evaluation', {}) or {}
    criteria = rubric.get('criteria_evaluations', {}) or {}
    saved_row = saved_by_url.get(resource.get('url', ''))
    return {
        'rank': rank,
        'title': resource.get('title', 'Untitled Resource'),
        'description': resource.get('description', ''),
        'source': resource.get('source') or resource.get('source_platform') or 'Unknown source',
        'license': item.get('license_check', {}).get('license_type') or resource.get('license') or 'Unknown',
        'resource_url': resource.get('url', ''),
        'final_rank_score': round(float(item.get('final_rank_score', 0) or 0), 3),
        'reasoning_summary': item.get('syllabus_relevance', {}).get('rationale')
        or rubric.get('summary')
        or 'Matched by syllabus-aware ranking.',
        'criteria_scores': {key: value.get('score') for key, value in criteria.items()},
        'criteria_explanations': {key: value.get('explanation') for key, value in criteria.items()},
        'saved': bool(saved_row),
        'saved_id': saved_row.get('id') if saved_row else None,
        'evaluation_payload': item,
    }


def _normalize_search_results(results: dict, course_code: str, term: str) -> dict:
    if not isinstance(results.get('evaluated_resources'), list):
        results['evaluated_resources'] = []

    saved_by_url = _get_saved_by_url(course_code)
    normalized_resources = []
    for idx, item in enumerate(results.get('evaluated_resources', [])[:DEMO_MAX_OER_PER_SEARCH], start=1):
        normalized_resources.append(_normalize_evaluated_resource(item, idx, saved_by_url))

    return {
        'course_code': results.get('course_code', course_code),
        'term': results.get('term', term),
        'resources_found': results.get('resources_found', len(normalized_resources)),
        'results': normalized_resources,
        'summary': results.get('summary', ''),
    }

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Agentic OER Finder API is running'}), 200

@app.route('/api/search', methods=['POST'])
def search_oer():
    """API endpoint for OER search"""
    try:
        data = request.get_json() or {}
        course_code = data.get('course_code', '').strip().upper()
        term = data.get('term', '').strip()
        
        if not course_code or not is_valid_course_code(course_code):
            return jsonify({'error': 'Malformed course code. Expected format like ENGL 1101.'}), 400
        
        logger.info(f"Search request for course: {course_code}")
        
        oer_agent = get_agent()
        results = oer_agent.find_oer_for_course(course_code, term)

        if results.get('error') == 'OLLAMA_UNAVAILABLE':
            return jsonify({
                'error': 'Ollama is configured but unavailable. Start Ollama and retry.',
                'status': 'ollama_unavailable'
            }), 503

        if results.get('course_not_found'):
            logger.info(f"Course not found after scraping: {course_code}")
            if 'scrape_ui_path' not in results:
                results['scrape_ui_path'] = '/scrape'
            return jsonify(results), 404
        if results.get('scrape_required'):
            return jsonify({
                'error': results.get('error') or f'Syllabus for {course_code} is not stored yet. Scrape syllabi first.',
                'course_code': course_code,
                'scrape_required': True,
                'scrape_ui_path': '/scrape',
            }), 409
        
        response_payload = _normalize_search_results(results, course_code, term)

        logger.info(f"Sending response with {len(response_payload.get('results', []))} ranked results")
        return jsonify(response_payload), 200
    
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/stream', methods=['POST'])
def search_oer_stream():
    """Streaming API endpoint that emits each evaluated resource as it completes."""
    data = request.get_json() or {}
    course_code = data.get('course_code', '').strip().upper()
    term = data.get('term', '').strip()

    if not course_code or not is_valid_course_code(course_code):
        return jsonify({'error': 'Malformed course code. Expected format like ENGL 1101.'}), 400

    logger.info(f"Streaming search request for course: {course_code}")

    def event_line(payload: dict) -> str:
        return json.dumps(payload) + '\n'

    @stream_with_context
    def generate():
        output_queue: Queue = Queue()
        done_event = threading.Event()

        try:
            oer_agent = get_agent()
            saved_by_url = _get_saved_by_url(course_code)
            stream_rank = 0

            def on_resource_evaluated(event: dict):
                nonlocal stream_rank
                if stream_rank >= DEMO_MAX_OER_PER_SEARCH:
                    return
                evaluated_item = event.get('evaluated_resource')
                if not evaluated_item:
                    return
                stream_rank += 1
                normalized = _normalize_evaluated_resource(evaluated_item, stream_rank, saved_by_url)
                yield_payload = {
                    'type': 'resource',
                    'course_code': course_code,
                    'term': term,
                    'progress': {
                        'evaluated_count': event.get('evaluated_count', stream_rank),
                        'total_candidates': event.get('total_candidates', stream_rank),
                    },
                    'resource': normalized,
                }
                output_queue.put(event_line(yield_payload))

            def run_search():
                try:
                    results = oer_agent.find_oer_for_course(
                        course_code,
                        term,
                        on_resource_evaluated=on_resource_evaluated,
                    )

                    if results.get('error') == 'OLLAMA_UNAVAILABLE':
                        output_queue.put(event_line({
                            'type': 'error',
                            'status': 'ollama_unavailable',
                            'error': 'Ollama is configured but unavailable. Start Ollama and retry.',
                        }))
                        return

                    if results.get('course_not_found'):
                        if 'scrape_ui_path' not in results:
                            results['scrape_ui_path'] = '/scrape'
                        output_queue.put(event_line({'type': 'not_found', **results}))
                        return

                    if results.get('scrape_required'):
                        output_queue.put(event_line({
                            'type': 'error',
                            'error': results.get('error') or f'Syllabus for {course_code} is not stored yet. Scrape syllabi first.',
                            'course_code': course_code,
                            'scrape_required': True,
                            'scrape_ui_path': '/scrape',
                        }))
                        return

                    final_payload = _normalize_search_results(results, course_code, term)
                    output_queue.put(event_line({'type': 'complete', **final_payload}))
                except Exception as e:
                    logger.error(f"Error in stream search endpoint: {e}", exc_info=True)
                    output_queue.put(event_line({'type': 'error', 'error': str(e)}))
                finally:
                    done_event.set()

            worker = threading.Thread(target=run_search, daemon=True)
            worker.start()

            while not done_event.is_set() or not output_queue.empty():
                try:
                    chunk = output_queue.get(timeout=0.5)
                    yield chunk
                except Empty:
                    continue
        except Exception as e:
            logger.error(f"Error in stream search endpoint: {e}", exc_info=True)
            yield event_line({'type': 'error', 'error': str(e)})

    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get usage statistics"""
    try:
        oer_agent = get_agent()
        stats = oer_agent.get_usage_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape-syllabi', methods=['POST'])
def scrape_syllabi_for_course():
    """Scrape syllabus library for a specific course code and store missing rows in Supabase."""
    try:
        data = request.get_json() or {}
        course_code = data.get('course_code', '').strip().upper()
        term = data.get('term', '').strip()
        if not course_code or not is_valid_course_code(course_code):
            return jsonify({'error': 'Malformed course code. Expected format like ENGL 1101.'}), 400

        sb = get_supabase_client()
        if not sb.is_available():
            return jsonify({'error': 'Supabase is not configured or unavailable'}), 500

        logger.info(f"Syllabus scrape request: course={course_code}, term={term or 'any'}")

        discovered = fetch_library_index_for_course(course_code)
        if not discovered:
            logger.info("Targeted syllabus discovery returned 0 rows for %s; falling back to full index crawl", course_code)
            discovered = fetch_library_index()

        def norm_term(value: str) -> str:
            return (value or '').lower().replace(' ', '').replace('_', '-').replace('--', '-')

        def norm_course(value: str) -> str:
            return ''.join(ch for ch in (value or '').upper() if ch.isalnum())

        def norm_course_relaxed(value: str) -> str:
            """
            Relaxed normalization for source data that drops trailing lab suffixes.
            Example: CHEM 1211K -> CHEM1211
            """
            compact = norm_course(value)
            return re.sub(r'([A-Z]+)(\d{3,4})[A-Z]$', r'\1\2', compact)

        normalized_target = norm_course(course_code)
        relaxed_target = norm_course_relaxed(course_code)

        matches = [
            row for row in discovered
            if norm_course(row.get('course_code', '')) == normalized_target
        ]
        if not matches:
            matches = [
                row for row in discovered
                if norm_course_relaxed(row.get('course_code', '')) == relaxed_target
            ]
        if term:
            target_term = norm_term(term)
            matches = [row for row in matches if target_term in norm_term(row.get('term', ''))]

        if not matches:
            prefix = ''.join(ch for ch in course_code.upper() if ch.isalpha())
            number = ''.join(ch for ch in course_code if ch.isdigit())
            suggestions = []
            for row in discovered:
                code = (row.get('course_code') or '').upper()
                if not code:
                    continue
                code_prefix = ''.join(ch for ch in code if ch.isalpha())
                code_number = ''.join(ch for ch in code if ch.isdigit())
                if code_prefix == prefix or (number and code_number == number):
                    suggestions.append(code)

            suggestions = sorted(set(suggestions))[:12]

            return jsonify({
                'course_code': course_code,
                'term': term,
                'course_not_found': True,
                'status': 'not_found',
                'message': (
                    f'No syllabi found for {course_code} in the currently discovered library index. '
                    'Try scraping a different term, re-running later, or verifying the course code format.'
                ),
                'discovered_count': len(discovered),
                'matched_count': 0,
                'inserted_syllabuses': 0,
                'inserted_sections': 0,
                'skipped_existing': 0,
                'failed': 0,
                'suggested_course_codes': suggestions,
            }), 404

        if len(matches) > DEMO_MAX_SYLLABI_PER_SCRAPE:
            logger.info(
                "Demo cap applied: limiting scrape candidates from %s to %s",
                len(matches),
                DEMO_MAX_SYLLABI_PER_SCRAPE,
            )
            matches = matches[:DEMO_MAX_SYLLABI_PER_SCRAPE]

        inserted_syllabuses = 0
        inserted_sections = 0
        skipped_existing = 0
        failed = 0

        for item in matches:
            url = item.get('syllabus_url', '')
            if not url:
                failed += 1
                continue

            if sb.fetch_syllabus_by_url(url):
                skipped_existing += 1
                continue

            record = {
                'course_code': item.get('course_code', course_code),
                'course_title': item.get('card_title') or item.get('course_title') or item.get('course_code') or course_code,
                'term': item.get('term'),
                'section_number': item.get('section_number'),
                'course_id': item.get('course_id'),
                'instructor_name': item.get('instructor_name'),
                'syllabus_url': url,
                'scraped_at': datetime.now(timezone.utc).isoformat(),
            }

            inserted = sb.insert_syllabus(record)
            if not inserted:
                failed += 1
                continue

            sections = fetch_and_parse_syllabus(url)
            payload = prepare_section_records(inserted['id'], sections)
            if payload:
                inserted_sections += sb.insert_sections_batch(payload)

            inserted_syllabuses += 1

        final_db_rows = sb.fetch_syllabuses_by_course_code(course_code, term or None)
        return jsonify({
            'course_code': course_code,
            'term': term,
            'discovered_count': len(discovered),
            'matched_count': len(matches),
            'inserted_syllabuses': inserted_syllabuses,
            'inserted_sections': inserted_sections,
            'skipped_existing': skipped_existing,
            'failed': failed,
            'db_total_for_course': len(final_db_rows),
            'message': f'Finished scraping {course_code}. Inserted {inserted_syllabuses} syllabi and {inserted_sections} sections.'
        }), 200

    except Exception as e:
        logger.error(f"Error scraping syllabi: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/saved-resources', methods=['GET'])
def list_saved_resources():
    """List saved resources for all courses or one course code."""
    course_code = request.args.get('course_code', '').strip().upper()
    if course_code and not is_valid_course_code(course_code):
        return jsonify({'error': 'Malformed course code. Expected format like ENGL 1101.'}), 400

    sb = get_supabase_client()
    if not sb.is_available():
        return jsonify({'error': 'Supabase is not configured or unavailable'}), 500

    rows = sb.list_saved_resources(course_code or None)
    return jsonify({'saved_resources': rows}), 200


@app.route('/api/saved-resources', methods=['POST'])
def save_resource():
    """Save (or update) a resource snapshot."""
    data = request.get_json() or {}
    required = ['course_code', 'resource_url', 'title']
    missing = [field for field in required if not str(data.get(field, '')).strip()]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    course_code = str(data.get('course_code', '')).strip().upper()
    if not is_valid_course_code(course_code):
        return jsonify({'error': 'Malformed course code. Expected format like ENGL 1101.'}), 400

    sb = get_supabase_client()
    if not sb.is_available():
        return jsonify({'error': 'Supabase is not configured or unavailable'}), 500

    row = {
        'course_code': course_code,
        'resource_url': str(data.get('resource_url', '')).strip(),
        'title': str(data.get('title', '')).strip(),
        'description': data.get('description') or '',
        'source': data.get('source') or '',
        'license': data.get('license') or '',
        'final_rank_score': data.get('final_rank_score') or 0,
        'reasoning_summary': data.get('reasoning_summary') or '',
        'evaluation_payload': data.get('evaluation_payload') or {},
    }
    saved = sb.upsert_saved_resource(row)
    if not saved:
        return jsonify({'error': 'Unable to save resource'}), 500
    return jsonify(saved), 200


@app.route('/api/saved-resources/<resource_id>', methods=['DELETE'])
def delete_saved_resource(resource_id):
    """Delete saved resource by id."""
    sb = get_supabase_client()
    if not sb.is_available():
        return jsonify({'error': 'Supabase is not configured or unavailable'}), 500
    deleted = sb.delete_saved_resource(resource_id)
    if not deleted:
        return jsonify({'error': 'Saved resource not found'}), 404
    return jsonify({'deleted': True, 'id': resource_id}), 200

@app.route('/api/courses', methods=['GET'])
def get_required_courses():
    """Get list of required courses for testing"""
    config = Config()
    return jsonify({'courses': config.REQUIRED_COURSES})

def _warn_on_python_version() -> None:
    """Print a compatibility warning for Python runtimes newer than tested range."""
    if sys.version_info >= (3, 14):
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print("⚠️  Compatibility warning:")
        print(f"   Detected Python {version}")
        print("   Recommended version for this project: Python 3.10–3.13")
        print("   Some native dependencies may fail or behave unexpectedly on 3.14+\n")

if __name__ == '__main__':
    _warn_on_python_version()
    # Get port from environment variable (for deployment platforms like Render, Railway)
    port = int(os.environ.get('PORT', getattr(Config, 'PORT', 5000)))
    print("\n" + "="*60)
    print("🚀 Agentic OER Finder API Server")
    print("="*60)
    print(f"Starting on: http://0.0.0.0:{port}")
    print(f"API Endpoint: http://localhost:{port}/api/search")
    print(f"Health Check: http://localhost:{port}/api/health")
    print(f"Debug Mode: {getattr(Config, 'DEBUG', True)}")
    print("="*60 + "\n")
    app.run(debug=getattr(Config, 'DEBUG', True), port=port, host='0.0.0.0')
