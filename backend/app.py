"""
Flask API Backend for Agentic OER Finder
Provides REST API endpoints for the React frontend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import sys
from datetime import datetime, timezone
from .oer_agent import OERAgent
from .config import Config
from .scrapers.library_index_scraper import fetch_library_index
from .scrapers.syllabus_content_scraper import fetch_and_parse_syllabus, prepare_section_records
from .llm.supabase_client import get_supabase_client

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for API endpoints (allow requests from React frontend)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000", "http://127.0.0.1:8000"]}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agent
agent = None

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

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Agentic OER Finder API is running'}), 200

@app.route('/api/search', methods=['POST'])
def search_oer():
    """API endpoint for OER search"""
    try:
        data = request.get_json()
        course_code = data.get('course_code', '').strip().upper()
        term = data.get('term', '').strip()
        
        if not course_code:
            return jsonify({'error': 'Course code is required'}), 400
        
        logger.info(f"Search request for course: {course_code}")
        
        oer_agent = get_agent()
        results = oer_agent.find_oer_for_course(course_code, term)

        if results.get('course_not_found'):
            logger.info(f"Course not found after scraping: {course_code}")
            return jsonify(results), 404
        
        # Debug logging
        evaluated_count = len(results.get('evaluated_resources', []))
        resources_found = results.get('resources_found', 0)
        logger.info(f"API Response - Resources found: {resources_found}, Evaluated: {evaluated_count}")
        logger.info(f"Results keys: {list(results.keys())}")
        
        # Ensure evaluated_resources is always a list
        if 'evaluated_resources' not in results:
            logger.warning("evaluated_resources key missing! Adding empty list.")
            results['evaluated_resources'] = []
        elif not isinstance(results['evaluated_resources'], list):
            logger.warning(f"evaluated_resources is not a list! Type: {type(results['evaluated_resources'])}")
            results['evaluated_resources'] = []
        
        # Verify we can serialize
        try:
            import json
            json_str = json.dumps(results, default=str, ensure_ascii=False)
            logger.info(f"JSON serialization successful. Length: {len(json_str)}, Evaluated resources in JSON: {json_str.count('evaluated_resources')}")
        except Exception as e:
            logger.error(f"JSON serialization failed: {e}", exc_info=True)
        
        # Log first resource if exists
        if evaluated_count > 0:
            first_resource = results['evaluated_resources'][0]
            logger.info(f"First resource title: {first_resource.get('resource', {}).get('title', 'N/A')}")
            logger.info(f"First resource keys: {list(first_resource.keys())}")
        else:
            logger.warning("WARNING: Returning 0 evaluated_resources to frontend!")
        
        # CRITICAL: Double-check before sending
        final_evaluated_count = len(results.get('evaluated_resources', []))
        logger.info(f"BEFORE jsonify: {final_evaluated_count} evaluated_resources in results dict")
        
        # Ensure evaluated_resources exists and is a list
        if 'evaluated_resources' not in results:
            logger.error("CRITICAL: evaluated_resources key missing in results!")
            results['evaluated_resources'] = []
        elif not isinstance(results['evaluated_resources'], list):
            logger.error(f"CRITICAL: evaluated_resources is not a list! Type: {type(results['evaluated_resources'])}")
            results['evaluated_resources'] = list(results['evaluated_resources']) if results['evaluated_resources'] else []
        
        # Create response
        response = jsonify(results)
        
        # Verify response data
        try:
            response_data = response.get_json()
            response_evaluated_count = len(response_data.get('evaluated_resources', []))
            logger.info(f"AFTER jsonify: {response_evaluated_count} evaluated_resources in response")
            if response_evaluated_count != final_evaluated_count:
                logger.error(f"DATA LOST! Had {final_evaluated_count} but response has {response_evaluated_count}")
        except:
            pass
        
        logger.info(f"Sending response with {final_evaluated_count} evaluated_resources")
        return response
    
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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
        limit = int(data.get('limit') or 0)

        if not course_code:
            return jsonify({'error': 'Course code is required'}), 400

        sb = get_supabase_client()
        if not sb.is_available():
            return jsonify({'error': 'Supabase is not configured or unavailable'}), 500

        logger.info(f"Syllabus scrape request: course={course_code}, term={term or 'any'}")
        discovered = fetch_library_index()

        def norm_term(value: str) -> str:
            return (value or '').lower().replace(' ', '').replace('_', '-').replace('--', '-')

        matches = [row for row in discovered if row.get('course_code') == course_code]
        if term:
            target_term = norm_term(term)
            matches = [row for row in matches if target_term in norm_term(row.get('term', ''))]

        if not matches:
            return jsonify({
                'course_code': course_code,
                'term': term,
                'course_not_found': True,
                'error': f'No syllabi found for {course_code} in the syllabus library.',
                'discovered_count': len(discovered),
                'matched_count': 0,
                'inserted_syllabuses': 0,
                'inserted_sections': 0,
                'skipped_existing': 0,
                'failed': 0,
            }), 404

        if limit > 0:
            matches = matches[:limit]

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

@app.route('/api/courses', methods=['GET'])
def get_required_courses():
    """Get list of required courses for testing"""
    config = Config()
    return jsonify({'courses': config.REQUIRED_COURSES})

@app.route('/api/test-search', methods=['GET', 'POST'])
def test_search():
    """Test endpoint to debug search results"""
    try:
        logger.info("Test search endpoint called")
        oer_agent = get_agent()
        results = oer_agent.find_oer_for_course("ITEC 1001")
        
        evaluated_count = len(results.get('evaluated_resources', []))
        resources_found = results.get('resources_found', 0)
        
        logger.info(f"Test search - Found: {resources_found}, Evaluated: {evaluated_count}")
        
        # Return raw results for debugging
        response_data = {
            'debug': True,
            'status': 'success',
            'resources_found': resources_found,
            'resources_evaluated': results.get('resources_evaluated', 0),
            'evaluated_resources_count': evaluated_count,
            'has_evaluated_resources': 'evaluated_resources' in results,
            'evaluated_resources_is_list': isinstance(results.get('evaluated_resources', []), list),
        }
        
        # Add first resource info if available
        if evaluated_count > 0:
            first_resource = results.get('evaluated_resources', [{}])[0]
            response_data['first_resource_title'] = first_resource.get('resource', {}).get('title', 'N/A')
            response_data['first_resource_url'] = first_resource.get('resource', {}).get('url', 'N/A')
        else:
            response_data['first_resource_title'] = 'N/A'
            response_data['first_resource_url'] = 'N/A'
        
        # Include full results (but this might be large)
        response_data['full_results'] = results
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in test search: {e}", exc_info=True)
        return jsonify({'error': str(e), 'debug': True}), 500

@app.route('/test', methods=['GET'])
def simple_test():
    """Simple test endpoint"""
    return jsonify({'status': 'ok', 'message': 'Flask is running!'})


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
