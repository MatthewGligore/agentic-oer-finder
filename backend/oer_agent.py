"""
Main Agentic OER Finder Engine
Orchestrates the complete workflow: syllabus analysis, OER search, evaluation, and reporting
"""
import time
import re
import os
from typing import Dict, List, Optional
import logging
from urllib.parse import quote_plus, urlparse
from datetime import datetime, timezone

import requests

from .config import Config
from .scrapers.syllabus_scraper import SyllabusScraper
from .scrapers.alg_scraper import ALGScraper
from .scrapers.platform_aggregator_scraper import PlatformAggregatorScraper
from .scrapers.library_index_scraper import fetch_library_index
from .scrapers.syllabus_content_scraper import fetch_and_parse_syllabus, prepare_section_records
from .llm.llm_client import LLMClient
from .evaluators.rubric_evaluator import RubricEvaluator
from .evaluators.license_checker import LicenseChecker
from .utils.logger import UsageLogger
from .llm.supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OERAgent:
    """Main AI agent for OER identification and evaluation"""
    
    def __init__(self, llm_provider=None, llm_model=None, use_selenium=False):
        """
        Initialize the OER Agent
        
        Args:
            llm_provider: LLM provider ('openai', 'anthropic', etc.)
            llm_model: Specific model to use
            use_selenium: If True, use Selenium scraper (requires selenium package)
        """
        self.config = Config()
        
        # Initialize Supabase client
        self.supabase_client = get_supabase_client()
        
        # Use Selenium scraper only if requested and available
        if use_selenium:
            try:
                from scrapers.syllabus_scraper_selenium import SyllabusScraperSelenium
                self.syllabus_scraper = SyllabusScraperSelenium(self.config.SYLLABUS_BASE_URL)
                logger.info("Using Selenium scraper for JavaScript-rendered content")
            except ImportError:
                logger.warning("Selenium not available, falling back to regular scraper")
                self.syllabus_scraper = SyllabusScraper(self.config.SYLLABUS_BASE_URL)
        else:
            self.syllabus_scraper = SyllabusScraper(self.config.SYLLABUS_BASE_URL)
        self.alg_scraper = ALGScraper(self.config.ALG_BASE_URL)
        self.platform_scraper = PlatformAggregatorScraper()
        self.llm = LLMClient(
            provider=llm_provider or self.config.DEFAULT_LLM_PROVIDER,
            model=llm_model or self.config.DEFAULT_MODEL
        )
        self.max_llm_evaluations = int(os.getenv('MAX_LLM_EVALUATIONS', '3'))
        self.rubric_evaluator = RubricEvaluator(self.config.RUBRIC_CRITERIA)
        self.license_checker = LicenseChecker()
        self.logger = UsageLogger(self.config.LOG_DIR)

    def _clean_field_text(self, text: str) -> str:
        """Remove common markdown/list artifacts from LLM text fields."""
        if not text:
            return ''
        cleaned = text.strip()
        cleaned = re.sub(r'^[-*]+\s*', '', cleaned)
        cleaned = re.sub(r'^\*\*\s*', '', cleaned)
        cleaned = re.sub(r'\s*\*\*$', '', cleaned)
        cleaned = re.sub(r'^(title|description|url|license|author|publisher)\s*:\s*', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _sanitize_url(self, url: str) -> str:
        """Normalize URL strings extracted from LLM output."""
        if not url:
            return ''

        cleaned = url.strip()
        cleaned = self._clean_field_text(cleaned)

        # Strip common trailing markdown and punctuation artifacts.
        cleaned = cleaned.strip('`"\'<>[](){}')
        cleaned = re.sub(r'[\.,;:!?]+$', '', cleaned)

        if cleaned.startswith('www.'):
            cleaned = f'https://{cleaned}'

        parsed = urlparse(cleaned)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            return ''

        return cleaned

    def _is_url_reachable(self, url: str) -> bool:
        """Best-effort URL check to avoid returning known-bad links."""
        if not url:
            return False

        def looks_browser_reachable(status_code: int) -> bool:
            if status_code < 400:
                return True
            # Some OER sites block automated clients but still work in a browser.
            return status_code in (401, 403, 405, 406, 429)

        try:
            head = requests.head(url, allow_redirects=True, timeout=4)
            if looks_browser_reachable(head.status_code):
                return True
            # Some sites do not support HEAD; fall back to GET.
            get_resp = requests.get(url, allow_redirects=True, timeout=4)
            return looks_browser_reachable(get_resp.status_code)
        except Exception:
            return False

    def _is_trusted_oer_url(self, url: str) -> bool:
        """Check URL shape against known OER platform patterns."""
        if not url:
            return False

        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        if 'openstax.org' in host:
            # OpenStax canonical patterns used in this project.
            return path.startswith('/details/books/') or path.startswith('/subjects')
        if 'oercommons.org' in host:
            return path.startswith('/search') or path.startswith('/courseware') or path == '/'
        if 'merlot.org' in host:
            return '/materials' in path or path == '/'
        if 'writingspaces.org' in host:
            return True
        if 'open.umn.edu' in host:
            return '/opentextbooks' in path
        if 'greenteapress.com' in host:
            return '/wp/' in path

        return True

    def _build_fallback_url(self, title: str, course_code: str, source: str) -> str:
        """Build reliable fallback URLs on established OER platforms."""
        query = quote_plus(f"{course_code} {title}".strip())
        source_lower = (source or '').lower()
        title_lower = (title or '').lower()

        if 'openstax' in source_lower or 'openstax' in title_lower:
            return 'https://openstax.org/subjects'
        if 'writing spaces' in source_lower or 'writing spaces' in title_lower:
            return 'https://writingspaces.org'
        if 'merlot' in source_lower or 'merlot' in title_lower:
            return f'https://www.merlot.org/merlot/materials.htm?keywords={query}'
        if 'oer commons' in source_lower or 'oercommons' in source_lower:
            return f'https://oercommons.org/search?search_source=site&f.search={query}'

        return f'https://oercommons.org/search?search_source=site&f.search={query}'

    def _finalize_llm_resources(self, resources: List[Dict], course_code: str) -> List[Dict]:
        """Clean, validate, and deduplicate LLM suggestions before returning."""
        finalized = []
        seen_urls = set()

        for resource in resources:
            title = self._clean_field_text(resource.get('title', ''))
            description = self._clean_field_text(resource.get('description', ''))
            author = self._clean_field_text(resource.get('author', ''))
            source = self._clean_field_text(resource.get('source', 'LLM Suggested')) or 'LLM Suggested'
            license_text = self._clean_field_text(resource.get('license', 'CC BY')) or 'CC BY'

            # Keep titles readable if the model emitted long sentence-like first lines.
            if title and len(title) > 200:
                title = title[:200].rstrip()
            if description and len(description) > 500:
                description = description[:500].rstrip()

            url = self._sanitize_url(resource.get('url', ''))
            if not self._is_trusted_oer_url(url) or not self._is_url_reachable(url):
                url = self._build_fallback_url(title or course_code, course_code, source)

            if not title:
                title = f'OER Resource for {course_code}'
            if not description:
                description = f'Open educational resource relevant to {course_code}.'
            if not author:
                author = 'Various'

            if url in seen_urls:
                continue
            seen_urls.add(url)

            finalized.append({
                'title': title,
                'description': description,
                'url': url,
                'license': license_text,
                'author': author,
                'source': source,
                'query': course_code
            })

        return finalized
    
    def _fetch_syllabus_with_fallback(self, course_code: str, term: Optional[str] = None) -> Dict:
        """
        Fetch syllabus information: try Supabase first, fall back to live scraping
        
        Args:
            course_code: Course code (e.g., 'ENGL 1101')
            term: Optional term
        
        Returns:
            Dict with syllabus info and sections from database, or scraped data if not in DB
        """
        # Try Supabase first
        if self.supabase_client.is_available():
            try:
                logger.info(f"Querying Supabase for {course_code}")
                syllabuses = self.supabase_client.fetch_syllabuses_by_course_code(course_code, term)
                
                if syllabuses:
                    logger.info(f"Found {len(syllabuses)} syllabuses in Supabase for {course_code}")
                    
                    # Use first syllabus found
                    syllabus = syllabuses[0]
                    syllabus_id = syllabus.get('id')
                    
                    # Fetch sections for this syllabus
                    if syllabus_id:
                        sections = self.supabase_client.fetch_sections_by_syllabus_id(syllabus_id)
                        
                        # Add sections to syllabus info as a dictionary
                        sections_dict = {}
                        for section in sections:
                            section_type = section.get('section_type')
                            content = section.get('section_content')
                            if section_type and content:
                                sections_dict[section_type] = content
                        
                        syllabus['sections'] = sections_dict
                        syllabus['from_database'] = True
                        syllabus['syllabus_found'] = True
                        
                        logger.info(f"Added {len(sections_dict)} sections to syllabus from database")
                    
                    return syllabus
            except Exception as e:
                logger.warning(f"Error querying Supabase: {e}. Falling back to live scraping.")
        
        # Fall back to live scraping
        logger.info(f"Fetching syllabus via live scraper for {course_code}")
        syllabi = self.syllabus_scraper.search_course(course_code, term)

        if syllabi:
            syllabus = syllabi[0]
            syllabus['from_database'] = False
            syllabus['syllabus_found'] = True

            stored = self._store_scraped_syllabus_if_possible(course_code, term, syllabus)
            if stored:
                return stored

            return syllabus

        # Last automated fallback: discover course syllabus directly from library index and store it.
        stored_from_index = self._discover_and_store_from_library_index(course_code, term)
        if stored_from_index:
            return stored_from_index
        
        # Final fallback
        logger.warning(f"No syllabus found for {course_code}")
        return {
            'course_code': course_code,
            'title': course_code,
            'description': '',
            'from_database': False,
            'syllabus_found': False,
            'not_found_reason': f'No syllabus found for {course_code} in the GGC syllabus library.'
        }

    def _normalize_term(self, value: Optional[str]) -> str:
        """Normalize term text for tolerant comparisons."""
        return (value or '').lower().replace(' ', '').replace('_', '-').replace('--', '-')

    def _build_syllabus_payload(self, course_code: str, term: Optional[str], scraped: Dict) -> Dict:
        """Create a syllabus row payload for Supabase insertion."""
        return {
            'course_code': scraped.get('course_code') or course_code,
            'course_title': scraped.get('card_title') or scraped.get('title') or scraped.get('course_title') or course_code,
            'term': scraped.get('term') or term,
            'section_number': scraped.get('section_number'),
            'course_id': scraped.get('course_id'),
            'instructor_name': scraped.get('instructor_name') or scraped.get('instructor', ''),
            'syllabus_url': scraped.get('syllabus_url') or scraped.get('url', ''),
            'scraped_at': datetime.now(timezone.utc).isoformat(),
        }

    def _store_scraped_syllabus_if_possible(self, course_code: str, term: Optional[str], scraped: Dict) -> Optional[Dict]:
        """Persist a scraped syllabus to Supabase and return a hydrated syllabus object."""
        if not self.supabase_client.is_available():
            return None

        source_url = scraped.get('syllabus_url') or scraped.get('url', '')
        if not source_url:
            return None

        existing = self.supabase_client.fetch_syllabus_by_url(source_url)
        if existing:
            sections = self.supabase_client.fetch_sections_by_syllabus_id(existing.get('id'))
            sections_dict = {
                row.get('section_type'): row.get('section_content')
                for row in sections
                if row.get('section_type') and row.get('section_content')
            }
            existing['sections'] = sections_dict
            existing['from_database'] = True
            existing['syllabus_found'] = True
            return existing

        payload = self._build_syllabus_payload(course_code, term, scraped)
        if not payload.get('syllabus_url'):
            return None

        inserted = self.supabase_client.insert_syllabus(payload)
        if not inserted:
            return None

        sections_dict: Dict = {}
        try:
            sections_dict = fetch_and_parse_syllabus(payload['syllabus_url'])
            if sections_dict:
                section_rows = prepare_section_records(inserted['id'], sections_dict)
                self.supabase_client.insert_sections_batch(section_rows)
        except Exception as exc:
            logger.warning(f"Stored syllabus but failed to parse sections for {course_code}: {exc}")

        inserted['sections'] = sections_dict
        inserted['from_database'] = True
        inserted['syllabus_found'] = True
        return inserted

    def _discover_and_store_from_library_index(self, course_code: str, term: Optional[str]) -> Optional[Dict]:
        """Discover a course in the syllabus index and store one matching syllabus automatically."""
        if not self.supabase_client.is_available():
            return None

        try:
            discovered = fetch_library_index()
        except Exception as exc:
            logger.warning(f"Library index discovery failed for {course_code}: {exc}")
            return None

        if not discovered:
            return None

        matches = [row for row in discovered if row.get('course_code') == course_code]
        if term:
            target = self._normalize_term(term)
            matches = [row for row in matches if target in self._normalize_term(row.get('term', ''))]

        if not matches:
            return None

        logger.info(f"Discovered {len(matches)} library index rows for {course_code}; storing first match")
        return self._store_scraped_syllabus_if_possible(course_code, term, matches[0])
    
    def find_oer_for_course(self, course_code: str, term: str = None) -> Dict:
        """
        Main method: Find and evaluate OER resources for a course
        
        Args:
            course_code: Course code (e.g., 'ENGL 1101')
            term: Optional term (e.g., 'Fall 2025')
        
        Returns:
            Complete results with OER recommendations and evaluations
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting OER search for {course_code}")
            
            # Step 1: Get syllabus information (try Supabase first, fall back to live scraping)
            logger.info("Step 1: Fetching syllabus information...")
            syllabus_info = self._fetch_syllabus_with_fallback(course_code, term)
            
            if not syllabus_info:
                logger.warning(f"No syllabus found for {course_code}")
                syllabus_info = {'course_code': course_code, 'title': course_code, 'description': ''}

            if not syllabus_info.get('syllabus_found', True):
                processing_time = time.time() - start_time
                message = syllabus_info.get(
                    'not_found_reason',
                    f'No syllabus found for {course_code} after scraping. Please verify the course code and try again.'
                )

                logger.warning(f"Course not found after scraping: {course_code}")
                self.logger.log_query(
                    course_code=course_code,
                    query_type='oer_search',
                    results=[],
                    processing_time=processing_time,
                    status='not_found'
                )

                return {
                    'course_code': course_code,
                    'term': term,
                    'course_not_found': True,
                    'error': message,
                    'syllabus_info': syllabus_info,
                    'resources_found': 0,
                    'resources_evaluated': 0,
                    'evaluated_resources': [],
                    'summary': message,
                    'processing_time_seconds': processing_time
                }
            
            # Log whether we got data from database or live scrape
            source = "database" if syllabus_info.get('from_database') else "live scrape"
            logger.info(f"Using syllabus information from {source}")
            
            # Step 2: Search across OER platforms (ALG + partner repositories).
            logger.info("Step 2: Searching OER platforms...")
            search_query = f"{course_code} {syllabus_info.get('title', '')}"
            alg_start = time.time()
            alg_resources = self.alg_scraper.search_resources(search_query, course_code)
            logger.info(
                "ALG scraper found %s resources for query: %s (%.2fs)",
                len(alg_resources),
                search_query,
                time.time() - alg_start,
            )

            platform_start = time.time()
            platform_resources = self.platform_scraper.search_resources(search_query, course_code)
            logger.info(
                "Multi-platform scraper found %s resources for query: %s (%.2fs)",
                len(platform_resources),
                search_query,
                time.time() - platform_start,
            )
            
            if not alg_resources:
                logger.warning(f"No resources found in ALG Library for {course_code}")
                if platform_resources:
                    logger.info(
                        "Skipping broader ALG retry because multi-platform scraper already returned %s resources",
                        len(platform_resources),
                    )
                else:
                    subject = course_code.split()[0] if ' ' in course_code else course_code
                    alg_resources = self.alg_scraper.search_resources(subject, course_code)
                    logger.info(f"Broader search found {len(alg_resources)} resources")

                if not platform_resources:
                    platform_resources = self.platform_scraper.search_resources(subject, course_code)
                    logger.info(f"Broader multi-platform search found {len(platform_resources)} resources")

            all_resources = self._merge_resources(alg_resources, platform_resources)

            if not all_resources:
                logger.warning(f"No scraper resources found across platforms for {course_code}; trying LLM suggestions")
                all_resources = self._get_llm_suggested_resources(course_code, syllabus_info)

            if not all_resources:
                logger.warning(f"No resources found by scraper/LLM for {course_code}")
                processing_time = time.time() - start_time
                empty_results = {
                    'course_code': course_code,
                    'term': term,
                    'syllabus_info': syllabus_info,
                    'resources_found': 0,
                    'resources_evaluated': 0,
                    'evaluated_resources': [],
                    'summary': f'No OER resources found across the configured source platforms for {course_code}.',
                    'processing_time_seconds': processing_time,
                }

                self.logger.log_query(
                    course_code=course_code,
                    query_type='oer_search',
                    results=[],
                    processing_time=processing_time,
                    status='not_found',
                )

                return empty_results

            # Step 3: Rank scraper-discovered resources without LLM discovery.
            logger.info("Step 3: Ranking scraper-discovered OER resources...")
            identified_resources = [
                {
                    'resource': resource,
                    'relevance_explanation': f'Scraper-discovered resource for {course_code}',
                    'identified_by': 'scraper'
                }
                for resource in all_resources[:12]
            ]
            
            # Step 4: Evaluate each identified resource
            logger.info("Step 4: Evaluating OER quality...")
            logger.info(f"Identified resources count: {len(identified_resources)}, ALG resources count: {len(alg_resources)}")
            evaluated_resources = []
            llm_eval_enabled = True
            
            logger.info(f"About to evaluate {len(identified_resources)} resources...")
            if not identified_resources:
                logger.error("ERROR: No identified_resources to evaluate! This should not happen.")
            
            for idx, identified in enumerate(identified_resources[:10]):  # Limit to top 10
                try:
                    logger.info(f"Processing resource {idx+1}/{len(identified_resources)}")
                    resource = identified.get('resource', {})
                    
                    # Skip if resource is empty
                    if not resource:
                        logger.warning(f"Skipping empty resource at index {idx}")
                        continue
                    
                    # Ensure resource has at least a title or URL
                    if not resource.get('title') and not resource.get('url'):
                        logger.warning(f"Skipping resource with no title or URL: {resource}")
                        continue
                    
                    # Set default title if missing
                    if not resource.get('title'):
                        resource['title'] = resource.get('url', 'Untitled Resource')
                        logger.info(f"Set default title for resource: {resource['title']}")
                    
                    # Get detailed resource information if needed
                    if not resource.get('description') and resource.get('url'):
                        try:
                            details = self.alg_scraper.get_resource_details(resource['url'])
                            if details:
                                resource.update(details)
                        except Exception as e:
                            logger.debug(f"Could not get details for {resource.get('url')}: {e}")
                    
                    # LLM evaluation
                    llm_eval = {}
                    if llm_eval_enabled and idx < self.max_llm_evaluations:
                        try:
                            llm_eval = self.llm.evaluate_oer_quality(
                                resource,
                                self.config.RUBRIC_CRITERIA,
                                syllabus_info,
                            )
                        except Exception as e:
                            logger.warning(f"LLM evaluation failed for {resource.get('title', 'Unknown')}: {e}")
                            # Circuit breaker: if local Ollama times out, skip LLM calls for remaining resources.
                            if 'timed out' in str(e).lower() and getattr(self.llm, 'client', None) == 'ollama':
                                llm_eval_enabled = False
                                logger.info("Disabling LLM evaluation for remaining resources due to Ollama timeout")
                    elif idx == self.max_llm_evaluations:
                        logger.info(
                            "Reached MAX_LLM_EVALUATIONS=%s; remaining resources use rule-based rubric evaluation",
                            self.max_llm_evaluations,
                        )
                    
                    # Rubric evaluation (always works, doesn't need LLM)
                    try:
                        rubric_eval = self.rubric_evaluator.evaluate(resource, llm_eval)
                    except Exception as e:
                        logger.error(f"Rubric evaluation failed: {e}")
                        # Create minimal evaluation
                        rubric_eval = {
                            'criteria_evaluations': {},
                            'overall_score': 0,
                            'summary': 'Evaluation incomplete'
                        }

                    criterion_links = self._build_criterion_links(resource, rubric_eval)
                    
                    # License check
                    try:
                        license_check = self.license_checker.check_license(resource)
                    except Exception as e:
                        logger.error(f"License check failed: {e}")
                        license_check = {
                            'has_open_license': False,
                            'license_type': 'Unknown',
                            'confidence': 'low',
                            'evidence': 'License check failed',
                            'details': ''
                        }
                    
                    # Combine evaluations
                    evaluated_resource = {
                        'resource': resource,
                        'relevance_explanation': identified.get('relevance_explanation', ''),
                        'llm_evaluation': llm_eval,
                        'rubric_evaluation': rubric_eval,
                        'license_check': license_check,
                        'criterion_links': criterion_links,
                        'integration_guidance': self._generate_integration_guidance(resource, rubric_eval, license_check)
                    }
                    
                    evaluated_resources.append(evaluated_resource)
                    logger.info(f"Successfully evaluated resource {idx+1}: {resource.get('title', 'Unknown')}")
                    
                except Exception as e:
                    logger.error(f"Error processing resource {idx+1}: {e}", exc_info=True)
                    # Even if evaluation fails, try to add resource with minimal data
                    try:
                        logger.info(f"Attempting to add resource {idx+1} with minimal evaluation")
                        resource = identified.get('resource', {})
                        if resource:
                            minimal_resource = {
                                'resource': resource,
                                'relevance_explanation': identified.get('relevance_explanation', f'Resource for {course_code}'),
                                'llm_evaluation': {},
                                'rubric_evaluation': {
                                    'resource': resource,
                                    'criteria_evaluations': {},
                                    'overall_score': 0,
                                    'summary': 'Evaluation failed - resource added with minimal data'
                                },
                                'license_check': {
                                    'has_open_license': False,
                                    'license_type': 'Unknown',
                                    'confidence': 'low',
                                    'evidence': 'Could not evaluate',
                                    'details': ''
                                },
                                'criterion_links': self._build_criterion_links(resource, {}),
                                'integration_guidance': f'Resource URL: {resource.get("url", "N/A")}\nNote: Full evaluation could not be completed.'
                            }
                            evaluated_resources.append(minimal_resource)
                            logger.info(f"Added resource {idx+1} with minimal evaluation: {resource.get('title', 'Unknown')}")
                    except Exception as e2:
                        logger.error(f"Failed to add resource even with minimal evaluation: {e2}")
                    continue
            
            logger.info(f"Created {len(evaluated_resources)} evaluated resources after main loop")
            
            # Sort by overall quality score
            evaluated_resources.sort(
                key=lambda x: x['rubric_evaluation'].get('overall_score', 0),
                reverse=True
            )
            
            # Step 5: Compile results - NOW that we're GUARANTEED to have evaluated_resources
            processing_time = time.time() - start_time
            
            # Final check before creating results
            logger.info(f"FINAL CHECK: {len(evaluated_resources)} evaluated_resources, {len(alg_resources)} alg_resources")
            
            results = {
                'course_code': course_code,
                'term': term,
                'syllabus_info': syllabus_info,
                'resources_found': len(all_resources) if all_resources else len(evaluated_resources),
                'resources_evaluated': len(evaluated_resources),
                'evaluated_resources': evaluated_resources,
                'summary': self._generate_summary(evaluated_resources),
                'processing_time_seconds': processing_time
            }
            
            # Debug: Log what we're returning
            logger.info(f"RETURNING: {len(evaluated_resources)} evaluated_resources")
            if evaluated_resources:
                logger.info(f"First resource title: {evaluated_resources[0].get('resource', {}).get('title', 'N/A')}")
            else:
                logger.error("CRITICAL ERROR: Returning 0 evaluated_resources after all checks!")
            
            # Log the query
            self.logger.log_query(
                course_code=course_code,
                query_type='oer_search',
                results=evaluated_resources,
                processing_time=processing_time,
                status='success'
            )
            
            logger.info(f"Completed OER search for {course_code} in {processing_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Error in OER search for {course_code}: {e}", exc_info=True)
            processing_time = time.time() - start_time
            
            # Log error
            self.logger.log_query(
                course_code=course_code,
                query_type='oer_search',
                results=[],
                processing_time=processing_time,
                status='error'
            )
            
            return {
                'course_code': course_code,
                'error': str(e),
                'processing_time_seconds': processing_time
            }

    def _merge_resources(self, primary: List[Dict], secondary: List[Dict]) -> List[Dict]:
        """Merge and deduplicate resource candidates from multiple source scrapers."""
        by_url: Dict[str, Dict] = {}

        for resource in (primary or []) + (secondary or []):
            url = self._sanitize_url(resource.get('url', ''))
            if not url:
                continue

            normalized = dict(resource)
            normalized['url'] = url

            existing = by_url.get(url)
            if not existing:
                by_url[url] = normalized
                continue

            # Prefer richer descriptions/titles while preserving known source metadata.
            if len(normalized.get('description', '')) > len(existing.get('description', '')):
                existing['description'] = normalized.get('description', '')
            if len(normalized.get('title', '')) > len(existing.get('title', '')):
                existing['title'] = normalized.get('title', '')
            if not existing.get('source_search_url') and normalized.get('source_search_url'):
                existing['source_search_url'] = normalized.get('source_search_url')
            if not existing.get('source_platform') and normalized.get('source_platform'):
                existing['source_platform'] = normalized.get('source_platform')

        merged = list(by_url.values())
        merged.sort(key=lambda item: (item.get('source', ''), len(item.get('title', ''))), reverse=True)
        return merged

    def _build_criterion_links(self, resource: Dict, rubric_eval: Dict) -> Dict[str, str]:
        """Build criterion-level evidence links so UI can provide click-through context."""
        criteria = (rubric_eval or {}).get('criteria_evaluations', {}) or {}
        resource_url = resource.get('url', '')
        search_url = resource.get('source_search_url', '')

        links: Dict[str, str] = {}
        for criterion in self.config.RUBRIC_CRITERIA:
            links[criterion] = resource_url or search_url

            criterion_data = criteria.get(criterion, {})
            evidence = criterion_data.get('evidence', []) if isinstance(criterion_data, dict) else []
            if isinstance(evidence, list):
                for ev in evidence:
                    if isinstance(ev, dict) and ev.get('url'):
                        links[criterion] = ev['url']
                        break

        return links
    
    def _generate_integration_guidance(self, resource: Dict, rubric_eval: Dict, license_check: Dict) -> str:
        """Generate guidance for instructors on how to integrate the resource"""
        guidance = []
        
        # License information
        if license_check.get('has_open_license'):
            guidance.append(f"✓ Open License Confirmed: {license_check.get('license_type', 'Open')}")
        else:
            guidance.append(f"⚠ License Status: {license_check.get('license_type', 'Unknown')} - Verify before use")
        
        # Quality score
        overall_score = rubric_eval.get('overall_score', 0)
        if overall_score >= 4:
            guidance.append(f"✓ High Quality Resource (Score: {overall_score:.1f}/5.0)")
        elif overall_score >= 3:
            guidance.append(f"○ Moderate Quality Resource (Score: {overall_score:.1f}/5.0)")
        else:
            guidance.append(f"⚠ Lower Quality Resource (Score: {overall_score:.1f}/5.0) - Review carefully")
        
        # Strengths from evaluation
        if 'llm_evaluation' in rubric_eval and 'strengths' in rubric_eval['llm_evaluation']:
            strengths = rubric_eval['llm_evaluation']['strengths']
            if strengths:
                guidance.append(f"Key Strengths: {', '.join(strengths[:3])}")
        
        # Integration suggestions
        guidance.append(f"Resource URL: {resource.get('url', 'N/A')}")
        guidance.append("Consider: Review the resource content to determine best integration approach for your specific course needs.")
        
        return '\n'.join(guidance)
    
    def _get_llm_suggested_resources(self, course_code: str, syllabus_info: Dict) -> List[Dict]:
        """Use LLM to suggest OER resources when scrapers fail"""
        system_prompt = """You are an expert in open educational resources (OER). 
Suggest relevant OER resources for courses. Provide realistic resource suggestions with titles, 
descriptions, and URLs to common OER platforms like OpenStax, OER Commons, MERLOT, etc."""
        
        prompt = f"""Course: {course_code}
Title: {syllabus_info.get('title', course_code)}
Description: {syllabus_info.get('description', '')[:500]}

Suggest 5-10 relevant OER resources for this course. For each resource, provide:
1. Title
2. Brief description
3. URL (use a realistic OER platform URL like openstax.org, oercommons.org, etc.)
4. License type (e.g., CC BY, CC BY-SA)
5. Author/Publisher

Format as a numbered list."""
        
        try:
            response = self.llm.generate(prompt, system_prompt, max_tokens=2000)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Return some default suggestions
            return self._get_default_suggestions(course_code)
        
        if not response:
            return self._get_default_suggestions(course_code)
        
        # Parse LLM response into resource format
        resources = []
        lines = response.split('\n')
        current_resource = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Look for numbered items
            if re.match(r'^\d+[\.\)]', line):
                if current_resource:
                    resources.append(current_resource)
                current_resource = {
                    'title': '',
                    'description': '',
                    'url': '',
                    'license': 'CC BY',
                    'author': '',
                    'source': 'LLM Suggested',
                    'query': course_code
                }
                # Extract title (remove number)
                title = re.sub(r'^\d+[\.\)]\s*', '', line)
                current_resource['title'] = self._clean_field_text(title[:200])
            
            elif current_resource:
                line_lower = line.lower()
                if 'url' in line_lower or 'http' in line_lower:
                    # Extract URL
                    url_match = re.search(r'https?://[^\s]+', line)
                    if url_match:
                        current_resource['url'] = self._sanitize_url(url_match.group(0))
                    else:
                        possible_url = self._clean_field_text(line)
                        current_resource['url'] = self._sanitize_url(possible_url)
                elif 'license' in line_lower or 'cc' in line_lower:
                    # Extract license
                    license_match = re.search(r'CC\s*[A-Z\-]+', line, re.IGNORECASE)
                    if license_match:
                        current_resource['license'] = self._clean_field_text(license_match.group(0))
                elif 'author' in line_lower or 'publisher' in line_lower:
                    # Extract author
                    author = re.sub(r'^(author|publisher):\s*', '', line, flags=re.IGNORECASE)
                    current_resource['author'] = self._clean_field_text(author[:100])
                else:
                    # Add to description
                    if current_resource['description']:
                        current_resource['description'] += ' ' + line
                    else:
                        current_resource['description'] = line
                    current_resource['description'] = self._clean_field_text(current_resource['description'][:500])
        
        if current_resource:
            resources.append(current_resource)
        
        # If parsing failed, create at least one resource with the response
        if not resources:
            resources.append({
                'title': f'OER Resources for {course_code}',
                'description': response[:500],
                'url': 'https://alg.manifoldapp.org',
                'license': 'CC BY',
                'author': 'Various',
                'source': 'LLM Suggested',
                'query': course_code
            })
        
        resources = self._finalize_llm_resources(resources, course_code)

        if not resources:
            return self._get_default_suggestions(course_code)

        logger.info(f"LLM suggested {len(resources)} resources")
        return resources
    
    def _get_default_suggestions(self, course_code: str) -> List[Dict]:
        """Get default OER suggestions when LLM fails"""
        subject = course_code.split()[0] if ' ' in course_code else course_code
        course_num = course_code.split()[1] if ' ' in course_code else ''
        
        # Map common subjects to relevant OER platforms
        subject_lower = subject.lower()
        
        # Course-specific suggestions based on subject
        default_resources = []
        
        # Biology courses
        if 'biol' in subject_lower:
            if '1101' in course_num or '1102' in course_num:
                default_resources.extend([
                    {
                        'title': 'Biology 2e - OpenStax',
                        'description': f'Free, peer-reviewed biology textbook covering principles of biology, cell structure, genetics, evolution, and ecology. Suitable for {course_code}.',
                        'url': 'https://openstax.org/details/books/biology-2e',
                        'license': 'CC BY',
                        'author': 'OpenStax',
                        'source': 'OpenStax',
                        'query': course_code
                    },
                    {
                        'title': 'Concepts of Biology - OpenStax',
                        'description': f'Introductory biology textbook covering basic biological concepts. Perfect for {course_code}.',
                        'url': 'https://openstax.org/details/books/concepts-biology',
                        'license': 'CC BY',
                        'author': 'OpenStax',
                        'source': 'OpenStax',
                        'query': course_code
                    }
                ])
        
        # English courses
        elif 'engl' in subject_lower:
            if '1101' in course_num:
                default_resources.extend([
                    {
                        'title': 'Writing Guide with Handbook - OpenStax',
                        'description': f'Comprehensive writing guide for composition courses. Covers academic writing, research, and citation. Suitable for {course_code}.',
                        'url': 'https://openstax.org/details/books/writing-guide',
                        'license': 'CC BY',
                        'author': 'OpenStax',
                        'source': 'OpenStax',
                        'query': course_code
                    },
                    {
                        'title': 'Writing Spaces: Readings on Writing',
                        'description': f'Open textbook series on writing, rhetoric, and composition. Free peer-reviewed essays for {course_code}.',
                        'url': 'https://writingspaces.org',
                        'license': 'CC BY-NC-SA',
                        'author': 'Writing Spaces',
                        'source': 'Writing Spaces',
                        'query': course_code
                    }
                ])
            elif '1102' in course_num:
                default_resources.extend([
                    {
                        'title': 'Writing and Literature - Open Textbook Library',
                        'description': f'Literature and composition textbook for second-semester English courses. Suitable for {course_code}.',
                        'url': 'https://open.umn.edu/opentextbooks/textbooks/writing-and-literature',
                        'license': 'CC BY',
                        'author': 'Various',
                        'source': 'Open Textbook Library',
                        'query': course_code
                    }
                ])
        
        # History courses
        elif 'hist' in subject_lower:
            if '2111' in course_num:
                default_resources.extend([
                    {
                        'title': 'U.S. History - OpenStax',
                        'description': f'Comprehensive U.S. History textbook covering from pre-Columbian times to present. Suitable for {course_code}.',
                        'url': 'https://openstax.org/details/books/us-history',
                        'license': 'CC BY',
                        'author': 'OpenStax',
                        'source': 'OpenStax',
                        'query': course_code
                    }
                ])
            elif '2112' in course_num:
                default_resources.extend([
                    {
                        'title': 'U.S. History - OpenStax',
                        'description': f'U.S. History textbook covering Reconstruction to present. Suitable for {course_code}.',
                        'url': 'https://openstax.org/details/books/us-history',
                        'license': 'CC BY',
                        'author': 'OpenStax',
                        'source': 'OpenStax',
                        'query': course_code
                    }
                ])
        
        # IT/Computing courses
        elif 'itec' in subject_lower or 'comp' in subject_lower or 'cs' in subject_lower:
            if '1001' in course_num:
                default_resources.extend([
                    {
                        'title': 'Introduction to Computer Science - OpenStax',
                        'description': f'Introduction to computer science covering programming fundamentals, algorithms, and data structures. Suitable for {course_code}.',
                        'url': 'https://openstax.org/details/books/introduction-computer-science',
                        'license': 'CC BY',
                        'author': 'OpenStax',
                        'source': 'OpenStax',
                        'query': course_code
                    },
                    {
                        'title': 'Think Python 2e',
                        'description': f'Free introduction to programming using Python. Perfect for {course_code}.',
                        'url': 'https://greenteapress.com/wp/think-python-2e/',
                        'license': 'CC BY-NC',
                        'author': 'Allen Downey',
                        'source': 'Green Tea Press',
                        'query': course_code
                    }
                ])
        
        # Arts courses
        elif 'arts' in subject_lower:
            default_resources.extend([
                {
                    'title': 'Art History - OpenStax',
                    'description': f'Art history textbook covering major art movements and works. Suitable for {course_code}.',
                    'url': 'https://openstax.org/details/books/art-history',
                    'license': 'CC BY',
                    'author': 'OpenStax',
                    'source': 'OpenStax',
                    'query': course_code
                }
            ])
        
        # If no course-specific suggestions, add general ones
        if not default_resources:
            default_resources = [
                {
                    'title': f'OpenStax {subject} Resources',
                    'description': f'Free, peer-reviewed textbooks for {course_code} from OpenStax. OpenStax provides high-quality, peer-reviewed, openly licensed textbooks.',
                    'url': f'https://openstax.org/subjects/{subject_lower}',
                    'license': 'CC BY',
                    'author': 'OpenStax',
                    'source': 'OpenStax',
                    'query': course_code
                },
                {
                    'title': f'OER Commons {course_code} Resources',
                    'description': f'Open educational resources for {course_code} from OER Commons. Search for materials by subject, education level, and material type.',
                    'url': f'https://oercommons.org/search?search_source=site&f.search={course_code.replace(" ", "+")}',
                    'license': 'CC BY',
                    'author': 'OER Commons',
                    'source': 'OER Commons',
                    'query': course_code
                },
                {
                    'title': f'MERLOT {course_code} Materials',
                    'description': f'Educational materials for {course_code} from MERLOT. MERLOT provides curated online learning and support materials.',
                    'url': f'https://www.merlot.org/merlot/materials.htm?keywords={course_code.replace(" ", "+")}',
                    'license': 'CC BY',
                    'author': 'MERLOT',
                    'source': 'MERLOT',
                    'query': course_code
                }
            ]

        default_resources = self._finalize_llm_resources(default_resources, course_code)
        
        logger.info(f"Created {len(default_resources)} course-specific default suggestions for {course_code}")
        return default_resources
    
    def _generate_summary(self, evaluated_resources: List[Dict]) -> str:
        """Generate summary of evaluation results"""
        if not evaluated_resources:
            return "No OER resources found for this course. The web scrapers may need to be customized for the actual website structures. Check the logs for more details."
        
        summary = f"Found {len(evaluated_resources)} evaluated OER resources.\n\n"
        
        # Count by license status
        open_licensed = sum(1 for r in evaluated_resources 
                          if r.get('license_check', {}).get('has_open_license', False))
        summary += f"Open Licensed Resources: {open_licensed}/{len(evaluated_resources)}\n"
        
        # Average quality score
        avg_score = sum(r.get('rubric_evaluation', {}).get('overall_score', 0) 
                       for r in evaluated_resources) / len(evaluated_resources)
        summary += f"Average Quality Score: {avg_score:.1f}/5.0\n\n"
        
        # Top resources
        summary += "Top Recommended Resources:\n"
        for i, resource in enumerate(evaluated_resources[:5], 1):
            title = resource.get('resource', {}).get('title', 'Unknown')
            score = resource.get('rubric_evaluation', {}).get('overall_score', 0)
            summary += f"{i}. {title} (Score: {score:.1f}/5.0)\n"
        
        return summary
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return self.logger.get_usage_stats()
