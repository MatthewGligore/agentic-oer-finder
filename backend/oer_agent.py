"""
Main Agentic OER Finder Engine
Orchestrates the complete workflow: syllabus analysis, OER search, evaluation, and reporting
"""
import time
import re
from typing import Callable, Dict, List, Optional
import logging
from urllib.parse import quote_plus, urlparse
from datetime import datetime, timezone

import requests

from .config import Config
from .scrapers.syllabus_scraper import SyllabusScraper
from .scrapers.alg_scraper import ALGScraper
from .scrapers.alg_selenium_scraper import ALGSeleniumScraper
from .scrapers.merlot_selenium_scraper import MerlotSeleniumScraper
from .scrapers.oer_commons_selenium_scraper import OERCommonsSeleniumScraper
from .scrapers.alg_manifold_api_scraper import ALGManifoldAPIScraper
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

    NOISE_TITLES = {
        'see more',
        'learn more',
        'details',
        'next',
        'previous',
        'home',
        'search',
        'materials',
        'material type',
        'connections',
        'go to material',
        'go to material isexternal',
    }

    EXCLUDED_FALLBACK_HOSTS = {
        'hcommons.org',
        'works.hcommons.org',
        'meshresearch.commons.msu.edu',
        'meshresearch.net',
        'hbcuaffordablelearning.org',
    }

    NON_INSTRUCTIONAL_RESOURCE_PATTERNS = (
        r'\bresearch grant\b',
        r'\bresearch report\b',
        r'\bgrant final report\b',
        r'\btransformation grant\b',
        r'\bfinal report summary\b',
        r'\bgrant summary\b',
        r'\badoption\b',
        r'\btraining\b',
        r'\bstandard operating procedures\b',
        r'\bkick[\s-]?off\b',
        r'\badvisory model\b',
        r'\bsustainability\b',
        r'\bpromotion and tenure\b',
        r'\bfaculty\b',
        r'\blibrarian advocacy\b',
    )
    
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
                from .scrapers.syllabus_scraper_selenium import SyllabusScraperSelenium
                self.syllabus_scraper = SyllabusScraperSelenium(self.config.SYLLABUS_BASE_URL)
                logger.info("Using Selenium scraper for JavaScript-rendered content")
            except ImportError:
                logger.warning("Selenium not available, falling back to regular scraper")
                self.syllabus_scraper = SyllabusScraper(self.config.SYLLABUS_BASE_URL)
        else:
            self.syllabus_scraper = SyllabusScraper(self.config.SYLLABUS_BASE_URL)
        self.alg_scraper = ALGScraper(self.config.ALG_BASE_URL)
        self.alg_manifold_api_scraper = ALGManifoldAPIScraper(self.config.ALG_BASE_URL)
        self.alg_selenium_scraper = ALGSeleniumScraper()
        self.merlot_selenium_scraper = MerlotSeleniumScraper()
        self.oer_commons_selenium_scraper = OERCommonsSeleniumScraper()
        self.platform_scraper = PlatformAggregatorScraper()
        self.llm = LLMClient(
            provider=llm_provider or self.config.DEFAULT_LLM_PROVIDER,
            model=llm_model or self.config.DEFAULT_MODEL
        )
        self.max_llm_evaluations = max(0, int(self.config.MAX_LLM_EVALUATIONS))
        self.demo_max_oer_per_search = max(1, int(getattr(self.config, 'DEMO_MAX_OER_PER_SEARCH', 10)))
        self.rubric_evaluator = RubricEvaluator(self.config.RUBRIC_CRITERIA)
        self.license_checker = LicenseChecker()
        self.logger = UsageLogger(self.config.LOG_DIR)
        self.relevance_weight = max(0.0, float(self.config.RELEVANCE_WEIGHT))
        self.rubric_weight = max(0.0, float(self.config.RUBRIC_WEIGHT))

    def _safe_scraper_search(self, scraper, scraper_name: str, query: str, course_code: str) -> List[Dict]:
        """Execute scraper search with defensive logging and stable fallback."""
        try:
            return scraper.search_resources(query, course_code) or []
        except Exception as exc:
            logger.warning("%s failed for query '%s': %s", scraper_name, query, exc)
            return []

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
            if not self._is_valid_scraped_syllabus(syllabus):
                logger.warning("Live scraper returned placeholder/invalid syllabus for %s", course_code)
                return {
                    'course_code': course_code,
                    'title': course_code,
                    'description': '',
                    'from_database': False,
                    'syllabus_found': False,
                    'scrape_required': True,
                    'not_found_reason': (
                        f"No valid syllabus found for {course_code} in Supabase or live scrape. "
                        "Use the Syllabus Scraper page to scrape and store this course in Supabase."
                    ),
                }

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
            'scrape_required': True,
            'not_found_reason': f'No syllabus found for {course_code} in the GGC syllabus library.'
        }

    def _is_valid_scraped_syllabus(self, scraped: Dict) -> bool:
        """Reject placeholder scrape results that are not a real course syllabus record."""
        if not scraped:
            return False

        note = str(scraped.get('note', '')).lower()
        if 'requires javascript rendering' in note:
            return False

        url = str(scraped.get('syllabus_url') or scraped.get('url') or '').strip().lower()
        if not url:
            return False

        # Root library URL is a placeholder, not a course syllabus record.
        if url.rstrip('/') == self.config.SYLLABUS_BASE_URL.rstrip('/').lower():
            return False

        # Prefer entries with explicit library metadata for DB insertion.
        if not scraped.get('course_id'):
            return False

        return True

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
        if not payload.get('syllabus_url') or not payload.get('course_id'):
            logger.info("Skipping Supabase insert for %s due to missing syllabus_url/course_id", course_code)
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

    def _syllabus_context_from_info(self, course_code: str, syllabus_info: Dict) -> Dict:
        """Build normalized syllabus context for query generation and relevance scoring."""
        sections = (syllabus_info or {}).get('sections') or {}
        raw_title = (syllabus_info or {}).get('course_title') or (syllabus_info or {}).get('title') or course_code
        course_title = self._normalize_course_title(raw_title, course_code)
        course_description = (syllabus_info or {}).get('description', '')

        objective_text = sections.get('objectives') or sections.get('other') or ''
        topics_text = sections.get('topics') or sections.get('course_content') or sections.get('resources') or ''

        objectives = self._extract_phrases(objective_text, limit=12)
        topics = self._extract_phrases(topics_text, limit=20)

        subject_terms = self._subject_seed_terms(course_code, course_title)

        if not topics and course_description:
            topics = self._extract_phrases(course_description, limit=12)

        if not topics:
            topics = subject_terms[:8]
        if not objectives:
            objectives = subject_terms[:6]

        search_profile = self._build_course_search_profile(
            course_code=course_code,
            course_title=course_title,
            course_description=course_description,
            objectives=objectives,
            topics=topics,
        )

        return {
            'course_code': course_code,
            'course_title': str(course_title),
            'course_description': str(course_description or ''),
            'objectives': objectives,
            'topics': topics,
            'search_profile': search_profile,
        }

    def _normalize_course_title(self, title: str, course_code: str) -> str:
        """Normalize noisy title strings from syllabus cards for query use."""
        cleaned = ' '.join(str(title or '').split()).strip()
        if not cleaned:
            return course_code

        # Many scraped records store term/section identifiers instead of descriptive titles.
        if re.search(r'\b20\d{2}\b', cleaned) and re.search(r'\bsection\b', cleaned, flags=re.IGNORECASE):
            return course_code

        return cleaned

    def _subject_seed_terms(self, course_code: str, course_title: str) -> List[str]:
        """Derive subject concept seeds when syllabus sections are sparse."""
        subject = (course_code.split()[0] if course_code.split() else course_code).lower()
        title_lower = (course_title or '').lower()

        seeds = {
            'engl': ['composition', 'argumentative writing', 'personal narrative', 'research writing', 'rhetoric'],
            'itec': ['information technology', 'computer systems', 'software', 'digital literacy', 'networking'],
            'hist': ['historical analysis', 'primary sources', 'american history', 'world history', 'civic context'],
            'biol': ['biology', 'cell structure', 'genetics', 'evolution', 'scientific method'],
            'chem': ['chemistry', 'general chemistry', 'chemical reactions', 'stoichiometry', 'atomic structure'],
            'math': ['algebra', 'functions', 'problem solving', 'quantitative reasoning', 'modeling'],
        }

        for prefix, terms in seeds.items():
            if subject.startswith(prefix) or prefix in title_lower:
                return terms

        if 'composition' in title_lower or 'english' in title_lower:
            return seeds['engl']

        return []

    def _build_course_search_profile(
        self,
        course_code: str,
        course_title: str,
        course_description: str,
        objectives: List[str],
        topics: List[str],
    ) -> Dict:
        """Infer search aliases and matching guardrails from syllabus context."""
        combined = ' '.join(
            [course_title or '', course_description or '', ' '.join(objectives or []), ' '.join(topics or [])]
        ).lower()

        profile = {
            'canonical_title': course_title if course_title and course_title != course_code else '',
            'preferred_queries': [],
            'required_terms': [],
            'excluded_terms': [],
            'boost_terms': [],
            'strict_matching': False,
        }

        if course_title and course_title != course_code:
            profile['preferred_queries'].append(course_title)

        if self._looks_like_english_composition(course_code, combined):
            profile.update({
                'canonical_title': 'English Composition',
                'preferred_queries': [
                    'english composition',
                    'english composition i',
                    'first year composition',
                    'college reading and writing',
                    'expository writing rhetoric',
                    'research writing rhetoric',
                ],
                'required_terms': ['composition', 'writing', 'rhetoric', 'essay', 'research', 'reading'],
                'excluded_terms': [
                    'elementary french',
                    'french',
                    'spanish',
                    'german',
                    'italian',
                    'calculus',
                    'chemistry',
                    'biology',
                    'physics',
                ],
                'boost_terms': [
                    'expository writing',
                    'persuasive writing',
                    'argumentative writing',
                    'rhetorical situation',
                    'writing process',
                    'audience purpose context',
                    'research writing',
                    'critical reading',
                ],
                'strict_matching': True,
            })
        elif self._looks_like_intro_information_technology(course_code, combined):
            profile.update({
                'canonical_title': 'Introduction to Information Technology',
                'preferred_queries': [
                    'introduction to computing',
                    'introduction to information technology',
                    'information technology fundamentals',
                    'computer information systems fundamentals',
                    'digital literacy and computer systems',
                    'information systems and networking basics',
                ],
                'required_terms': ['information technology', 'computer', 'software', 'systems', 'digital', 'networking'],
                'excluded_terms': [
                    'elementary french',
                    'french',
                    'spanish',
                    'german',
                    'italian',
                    'general chemistry',
                    'organic chemistry',
                    'american history',
                    'world history',
                ],
                'boost_terms': [
                    'it fundamentals',
                    'computer hardware software',
                    'operating systems basics',
                    'networking basics',
                    'cybersecurity fundamentals',
                    'digital literacy',
                    'information systems concepts',
                ],
                'strict_matching': True,
            })
        elif self._looks_like_intro_chemistry(course_code, combined):
            profile.update({
                'canonical_title': 'General Chemistry',
                'preferred_queries': [
                    'chemistry',
                    'general chemistry',
                    'introductory chemistry',
                    'college chemistry',
                    'chemistry with laboratory',
                    'chemical principles and reactions',
                ],
                'required_terms': ['chemistry', 'chemical', 'atom', 'molecule', 'reaction', 'stoichiometry', 'lab'],
                'excluded_terms': [
                    'elementary french',
                    'french',
                    'spanish',
                    'german',
                    'italian',
                    'first year composition',
                    'english composition',
                    'rhetoric',
                    'networking basics',
                    'information technology',
                ],
                'boost_terms': [
                    'general chemistry',
                    'chemical reactions',
                    'stoichiometry',
                    'atomic structure',
                    'periodic trends',
                    'chemical bonding',
                    'laboratory techniques',
                    'solutions and concentration',
                ],
                'strict_matching': True,
            })
        elif self._looks_like_us_history(course_code, combined):
            profile.update({
                'canonical_title': 'US History',
                'preferred_queries': [
                    'us history',
                    'united states history',
                    'american history',
                    'survey of us history',
                    'history of the united states',
                ],
                'required_terms': ['history', 'us', 'united states', 'american'],
                'excluded_terms': [
                    'world history',
                    'european history',
                    'ancient history',
                    'elementary french',
                    'french',
                    'spanish',
                    'german',
                    'italian',
                ],
                'boost_terms': [
                    'us history',
                    'american history',
                    'historical analysis',
                    'primary sources',
                    'civil war reconstruction',
                    'industrialization and reform',
                ],
                'strict_matching': True,
            })
        else:
            seed_terms = self._subject_seed_terms(course_code, course_title)
            profile['boost_terms'] = seed_terms[:8]

        profile['boost_terms'].extend(self._extract_search_terms(objectives + topics, limit=10))
        profile['preferred_queries'] = list(dict.fromkeys([q.strip() for q in profile['preferred_queries'] if q.strip()]))
        profile['required_terms'] = list(dict.fromkeys([q.strip().lower() for q in profile['required_terms'] if q.strip()]))
        profile['excluded_terms'] = list(dict.fromkeys([q.strip().lower() for q in profile['excluded_terms'] if q.strip()]))
        profile['boost_terms'] = list(dict.fromkeys([q.strip() for q in profile['boost_terms'] if q.strip()]))
        return profile

    def _looks_like_english_composition(self, course_code: str, combined_text: str) -> bool:
        """Detect first-year composition style courses from code and syllabus language."""
        if course_code.lower().startswith('engl'):
            return True

        english_signals = [
            'english composition',
            'first year composition',
            'college composition',
            'expository writing',
            'persuasive writing',
            'research writing',
            'rhetorical situation',
        ]
        return sum(1 for signal in english_signals if signal in combined_text) >= 2

    def _looks_like_intro_information_technology(self, course_code: str, combined_text: str) -> bool:
        """Detect intro information technology style courses from code and syllabus language."""
        subject = course_code.lower().split()[0] if course_code else ""
        if subject.startswith('itec') or subject.startswith('cis') or subject.startswith('it'):
            return True

        it_signals = [
            'information technology',
            'computer systems',
            'information systems',
            'digital literacy',
            'networking',
            'software applications',
            'it fundamentals',
        ]
        return sum(1 for signal in it_signals if signal in combined_text) >= 2

    def _looks_like_intro_chemistry(self, course_code: str, combined_text: str) -> bool:
        """Detect chemistry courses from code and syllabus language."""
        subject = course_code.lower().split()[0] if course_code else ""
        if subject.startswith('chem'):
            return True

        chem_signals = [
            'general chemistry',
            'introductory chemistry',
            'chemical concepts',
            'chemical reactions',
            'stoichiometry',
            'atomic structure',
            'periodic table',
            'chemical bonding',
            'laboratory skills',
        ]
        return sum(1 for signal in chem_signals if signal in combined_text) >= 2

    def _looks_like_us_history(self, course_code: str, combined_text: str) -> bool:
        """Detect introductory US history courses from code and syllabus language."""
        subject = course_code.lower().split()[0] if course_code else ""
        if subject.startswith('hist'):
            return True

        history_signals = [
            'us history',
            'united states history',
            'american history',
            'history of the united states',
            'civil war',
            'reconstruction',
            'industrialization',
            'historical analysis',
            'primary sources',
        ]
        return sum(1 for signal in history_signals if signal in combined_text) >= 2

    def _extract_search_terms(self, phrases: List[str], limit: int = 8) -> List[str]:
        """Convert syllabus phrases into shorter search-oriented topic strings."""
        terms: List[str] = []
        for phrase in phrases:
            cleaned = ' '.join(str(phrase or '').split()).strip(' :,.').lower()
            if not cleaned:
                continue
            cleaned = re.sub(r'\([^)]{1,24}\)', '', cleaned)
            cleaned = re.sub(r'^(upon completion of this course, students will|students will|learners will)\s*:?','', cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip(' :,.')
            if len(cleaned) < 4:
                continue
            terms.append(cleaned)
        return list(dict.fromkeys(terms))[:limit]

    def _extract_phrases(self, text: str, limit: int = 10) -> List[str]:
        """Extract concise phrase candidates from free-text syllabus sections."""
        if not text:
            return []

        lines = re.split(r'[\n\r\u2022\-\*;]+', str(text))
        phrases: List[str] = []
        for line in lines:
            cleaned = ' '.join(line.split()).strip(' :,.')
            cleaned = re.sub(r'\([^)]{1,24}\)', '', cleaned)
            cleaned = re.sub(
                r'^(upon completion of this course, students will|students will|learners will)\s*[:]?\s*',
                '',
                cleaned,
                flags=re.IGNORECASE,
            )
            if len(cleaned) < 4:
                continue
            if cleaned.lower().startswith(('week ', 'unit ', 'module ')):
                cleaned = re.sub(r'^(week|unit|module)\s*\d+\s*:?\s*', '', cleaned, flags=re.IGNORECASE)
            if cleaned:
                phrases.append(cleaned)

        # Keep stable insertion order and cap.
        uniq = list(dict.fromkeys(phrases))
        return uniq[:limit]

    def _truncate_query_terms(self, text: str) -> str:
        terms = [token for token in re.split(r'[^a-zA-Z0-9]+', (text or '').strip()) if token]
        max_terms = max(1, int(self.config.MAX_QUERY_TERMS_PER_VARIANT))
        return ' '.join(terms[:max_terms])

    def _build_syllabus_queries(self, course_code: str, syllabus_context: Dict) -> List[str]:
        """Create syllabus-driven query variants; keep course code as low-priority fallback."""
        title = syllabus_context.get('course_title', '')
        description = syllabus_context.get('course_description', '')
        objectives = syllabus_context.get('objectives', [])
        topics = syllabus_context.get('topics', [])
        search_profile = syllabus_context.get('search_profile', {}) or {}

        variants = []
        for preferred in search_profile.get('preferred_queries', [])[:3]:
            variants.append(self._truncate_query_terms(preferred))
        if title and title != course_code:
            variants.append(self._truncate_query_terms(title))
        if topics:
            variants.append(self._truncate_query_terms(' '.join(topics[:6])))
        if objectives:
            variants.append(self._truncate_query_terms(' '.join(objectives[:5])))
        if description:
            variants.append(self._truncate_query_terms(description))

        if search_profile.get('boost_terms'):
            variants.append(self._truncate_query_terms(' '.join(search_profile['boost_terms'][:6])))

        subject_seed_terms = self._subject_seed_terms(course_code, title)
        if subject_seed_terms:
            variants.append(self._truncate_query_terms(' '.join(subject_seed_terms[:6])))

        # Keep raw course code only as a backstop query variant.
        variants.append(self._truncate_query_terms(course_code))

        max_variants = max(1, int(self.config.MAX_SYLLABUS_QUERY_VARIANTS))
        deduped = [item for item in dict.fromkeys([v for v in variants if v.strip()])]

        if search_profile.get('strict_matching'):
            required_terms = [str(term).lower().strip() for term in search_profile.get('required_terms', []) if str(term).strip()]
            if required_terms:
                anchored = []
                for variant in deduped:
                    variant_lower = variant.lower()
                    if any(term in variant_lower for term in required_terms):
                        anchored.append(variant)
                if anchored:
                    deduped = anchored

        return deduped[:max_variants]

    def _search_primary_sources(self, query_variants: List[str], course_code: str, syllabus_context: Dict) -> List[Dict]:
        """Search primary libraries with dedicated scrapers."""
        collected: List[Dict] = []
        alg_requests_attempted = False
        for query in query_variants:
            alg_query_results: List[Dict] = []
            # Preferred path: use documented Manifold APIs when exposed.
            alg_query_results.extend(
                self._safe_scraper_search(
                    self.alg_manifold_api_scraper,
                    'ALG Manifold API scraper',
                    query,
                    course_code,
                )
            )
            alg_query_results.extend(
                self._safe_scraper_search(
                    self.alg_selenium_scraper,
                    'ALG Selenium scraper',
                    query,
                    course_code,
                )
            )

            # Keep the mature requests-based ALG scraper as a reliability backstop
            # only when API+Selenium paths fail to produce any candidates.
            if not alg_query_results and not alg_requests_attempted:
                alg_requests_attempted = True
                alg_query_results.extend(
                    self._safe_scraper_search(
                        self.alg_scraper,
                        'ALG requests scraper',
                        query,
                        course_code,
                    )
                )
            elif not alg_query_results and alg_requests_attempted:
                logger.debug(
                    "Skipping ALG requests scraper for query '%s'; backstop already attempted this search",
                    query,
                )
            else:
                logger.debug(
                    "Skipping ALG requests scraper for query '%s' because faster ALG paths returned %s candidates",
                    query,
                    len(alg_query_results),
                )

            collected.extend(alg_query_results)
            collected.extend(
                self._safe_scraper_search(
                    self.merlot_selenium_scraper,
                    'MERLOT Selenium scraper',
                    query,
                    course_code,
                )
            )
            collected.extend(
                self._safe_scraper_search(
                    self.oer_commons_selenium_scraper,
                    'OER Commons Selenium scraper',
                    query,
                    course_code,
                )
            )

        merged = self._merge_resources(collected, [])
        merged = [item for item in merged if self._resource_matches_course_profile(item, syllabus_context)]
        return merged[: int(self.config.MAX_PRIMARY_CANDIDATES)]

    def _search_fallback_sources(self, query_variants: List[str], course_code: str, syllabus_context: Dict) -> List[Dict]:
        """Search non-primary fallback sources using existing aggregator."""
        collected: List[Dict] = []
        for query in query_variants[:2]:
            collected.extend(
                self._safe_scraper_search(
                    self.platform_scraper,
                    'Fallback platform scraper',
                    query,
                    course_code,
                )
            )

        filtered = [
            item for item in collected
            if (item.get('source') or item.get('source_platform') or '') not in self.config.PRIMARY_OER_SOURCES
        ]
        filtered = [
            item for item in filtered
            if 'search for' not in str(item.get('title', '')).lower()
            and '/search' not in str(item.get('url', '')).lower()
        ]
        filtered = [item for item in filtered if not self._is_noise_resource(item)]
        filtered = [item for item in filtered if self._resource_matches_course_profile(item, syllabus_context)]
        return self._merge_resources(filtered, [])

    def _is_noise_resource(self, resource: Dict) -> bool:
        """Exclude obvious navigation/search artifacts and weak hosts."""
        title = str(resource.get('title', '')).strip().lower()
        url = str(resource.get('url', '')).strip().lower()
        source_page = str(resource.get('source_page', '')).strip().lower()

        if not title or len(title) < 4:
            return True
        if title in self.NOISE_TITLES and not self._has_strong_resource_url(url):
            return True
        if 'search for' in title:
            return True
        if '/search' in url and '/courseware' not in url:
            return True
        if any(skip in url for skip in ['/privacy', '/terms', '/contact', '/login', '/signin']):
            return True
        if any(collection in source_page for collection in ['/adoptions', '/research-reports', '/training-resources']):
            return True
        if self._is_non_instructional_resource(resource):
            return True

        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if host in self.EXCLUDED_FALLBACK_HOSTS:
            return True

        return False

    def _is_non_instructional_resource(self, resource: Dict) -> bool:
        """Filter ALG program metadata that is not a course material."""
        text = ' '.join([
            str(resource.get('title', '')),
            str(resource.get('description', '')),
            str(resource.get('source_page', '')),
        ]).lower()
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in self.NON_INSTRUCTIONAL_RESOURCE_PATTERNS)

    def _resource_matches_course_profile(self, resource: Dict, syllabus_context: Dict) -> bool:
        """Apply syllabus-driven guardrails before ranking and LLM evaluation."""
        if self._is_noise_resource(resource):
            return False

        profile = (syllabus_context or {}).get('search_profile', {}) or {}
        if not profile.get('strict_matching'):
            return True

        text = ' '.join([
            str(resource.get('title', '')),
            str(resource.get('description', '')),
            str(resource.get('url', '')),
            str(resource.get('query', '')),
            str(resource.get('source_search_url', '')),
            str(resource.get('source_page', '')),
        ]).lower()
        if not text.strip():
            return False

        for phrase in profile.get('preferred_queries', []):
            phrase_lower = phrase.lower().strip()
            if phrase_lower and phrase_lower in text:
                return True

        required_terms = [term for term in profile.get('required_terms', []) if term]
        excluded_terms = [term for term in profile.get('excluded_terms', []) if term]
        if any(term in text for term in excluded_terms):
            return False
        matched_terms = [term for term in required_terms if term in text]
        return len(set(matched_terms)) >= 2

    def _is_source_match(self, resource: Dict, expected_source: str) -> bool:
        """Case-insensitive source comparison across normalized source fields."""
        source = str(resource.get('source') or resource.get('source_platform') or '').strip().lower()
        return source == expected_source.strip().lower()

    def _balance_primary_source_mix(self, resources: List[Dict], limit: int) -> List[Dict]:
        """
        Keep a near 50/50 OpenALG/MERLOT mix when both sources exist.

        Selection preserves original ranking order while reserving source quotas.
        """
        if limit <= 0 or not resources:
            return []

        alg_indices = [idx for idx, item in enumerate(resources) if self._is_source_match(item, 'Open ALG Library')]
        merlot_indices = [idx for idx, item in enumerate(resources) if self._is_source_match(item, 'MERLOT')]

        if not alg_indices or not merlot_indices:
            return resources[:limit]

        per_source_quota = limit // 2
        selected_indices = set(alg_indices[:per_source_quota] + merlot_indices[:per_source_quota])

        ordered_selection = [resources[idx] for idx in range(len(resources)) if idx in selected_indices]
        if len(ordered_selection) >= limit:
            return ordered_selection[:limit]

        for idx, item in enumerate(resources):
            if idx in selected_indices:
                continue
            ordered_selection.append(item)
            if len(ordered_selection) >= limit:
                break

        return ordered_selection

    def _has_strong_resource_url(self, url: str) -> bool:
        """Detect detail/resource URLs that should be kept even with weak anchor text."""
        if not url:
            return False
        lowered = url.lower()
        if '/merlot/viewmaterial' in lowered:
            return True
        if 'materials.htm?materialid=' in lowered:
            return True
        if '/projects/' in lowered and 'alg.manifoldapp.org' in lowered:
            return True
        if '/courseware/' in lowered and 'oercommons.org' in lowered:
            return True
        return False

    def _is_primary_source(self, resource: Dict) -> bool:
        source = resource.get('source') or resource.get('source_platform') or ''
        return source in self.config.PRIMARY_OER_SOURCES

    def _compute_final_rank_score(self, relevance_score: float, rubric_score: float) -> float:
        total = self.relevance_weight + self.rubric_weight
        if total <= 0:
            return float(rubric_score)
        return (float(relevance_score) * self.relevance_weight + float(rubric_score) * self.rubric_weight) / total

    def _candidate_prefilter_score(self, resource: Dict, syllabus_context: Dict, course_code: str) -> int:
        """Cheap pre-evaluation ranking signal based on syllabus term overlap."""
        text = f"{resource.get('title', '')} {resource.get('description', '')}".lower()
        title = (resource.get('title', '') or '').lower()
        url = (resource.get('url', '') or '').lower()
        topics = [str(t).lower() for t in syllabus_context.get('topics', [])][:12]
        objectives = [str(o).lower() for o in syllabus_context.get('objectives', [])][:8]
        search_profile = syllabus_context.get('search_profile', {}) or {}

        score = 0
        for term in topics + objectives:
            if not term:
                continue
            if term in text:
                score += 3
            elif any(word and word in text for word in term.split()[:3]):
                score += 1

        code_subject = (course_code.split()[0] if course_code.split() else course_code).lower()
        if code_subject and code_subject in text:
            score += 2
        if code_subject and code_subject in title:
            score += 1

        if self._is_primary_source(resource):
            score += 2

        if self._has_strong_resource_url(url):
            score += 4
        if any(host in url for host in ['meshresearch.net', 'commons.msu.edu', 'hcommons.org']):
            score -= 3

        title_lower = (resource.get('title', '') or '').lower()
        url_lower = url
        if 'search for' in title_lower or '/search' in url_lower:
            score -= 3
        if self._is_non_instructional_resource(resource):
            score -= 8

        for phrase in search_profile.get('preferred_queries', []):
            phrase_lower = phrase.lower()
            if phrase_lower and phrase_lower in text:
                score += 6

        required_terms = [term for term in search_profile.get('required_terms', []) if term]
        excluded_terms = [term for term in search_profile.get('excluded_terms', []) if term]
        matched_required = sum(1 for term in required_terms if term in text)
        score += matched_required * 2
        if any(term in text for term in excluded_terms):
            score -= 10

        return score

    def find_oer_for_course(
        self,
        course_code: str,
        term: str = None,
        on_resource_evaluated: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
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
            if self.llm.provider == 'ollama' and not self.llm.is_ollama_reachable():
                raise RuntimeError("OLLAMA_UNAVAILABLE")
            
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
                    'scrape_required': syllabus_info.get('scrape_required', True),
                    'scrape_ui_path': '/scrape',
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
            
            # Step 2: Build syllabus-driven query variants and search primary libraries first.
            logger.info("Step 2: Building syllabus-driven queries and searching primary sources...")
            syllabus_context = self._syllabus_context_from_info(course_code, syllabus_info)
            query_variants = self._build_syllabus_queries(course_code, syllabus_context)
            logger.info("Syllabus query variants for %s: %s", course_code, query_variants)

            primary_start = time.time()
            primary_resources = self._search_primary_sources(query_variants, course_code, syllabus_context)
            logger.info(
                "Primary scrapers found %s resources for %s variants in %.2fs",
                len(primary_resources),
                len(query_variants),
                time.time() - primary_start,
            )

            fallback_resources: List[Dict] = []
            fallback_threshold = int(self.config.FALLBACK_MIN_PRIMARY_RESULTS)
            if len(primary_resources) < fallback_threshold:
                logger.info(
                    "Primary results (%s) below fallback threshold (%s); running fallback sources",
                    len(primary_resources),
                    fallback_threshold,
                )
                fallback_resources = self._search_fallback_sources(query_variants, course_code, syllabus_context)
                logger.info("Fallback sources returned %s resources", len(fallback_resources))

            all_resources = self._merge_resources(primary_resources, fallback_resources)
            all_resources = [resource for resource in all_resources if not self._is_noise_resource(resource)]

            all_resources.sort(
                key=lambda resource: self._candidate_prefilter_score(resource, syllabus_context, course_code),
                reverse=True,
            )

            selection_limit = min(int(self.config.MAX_TOTAL_CANDIDATES), self.demo_max_oer_per_search)
            all_resources = self._balance_primary_source_mix(all_resources, selection_limit)

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

            # Step 3: Prepare top candidates for evaluation.
            logger.info("Step 3: Preparing candidate resources for evaluation...")
            identified_resources = [
                {
                    'resource': resource,
                    'relevance_explanation': f'Scraper-discovered resource for {course_code}',
                    'identified_by': 'scraper'
                }
                for resource in all_resources[: min(int(self.config.MAX_PRIMARY_CANDIDATES), self.demo_max_oer_per_search)]
            ]
            
            # Step 4: Evaluate each identified resource
            logger.info("Step 4: Evaluating syllabus relevance and OER quality...")
            logger.info("Identified resources count: %s", len(identified_resources))
            evaluated_resources = []
            llm_eval_enabled = True
            
            logger.info(f"About to evaluate {len(identified_resources)} resources...")
            if not identified_resources:
                logger.error("ERROR: No identified_resources to evaluate! This should not happen.")
            
            max_relevance = min(int(self.config.MAX_RELEVANCE_EVALUATIONS), self.demo_max_oer_per_search)
            max_evaluated = min(int(self.config.MAX_EVALUATED_RESOURCES), self.demo_max_oer_per_search)
            for idx, identified in enumerate(identified_resources[:max_evaluated]):
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

                    # Syllabus-resource semantic relevance (LLM or fallback rule-based)
                    relevance_eval = {'score': 3.0, 'matched_topics': [], 'rationale': 'Relevance scoring not executed.'}
                    if idx < max_relevance:
                        relevance_eval = self.llm.evaluate_syllabus_relevance(resource, syllabus_context)
                    elif idx == max_relevance:
                        logger.info(
                            "Reached MAX_RELEVANCE_EVALUATIONS=%s; remaining resources keep default relevance",
                            max_relevance,
                        )
                    
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
                    rubric_score = float(rubric_eval.get('overall_score', 0) or 0)
                    relevance_score = float(relevance_eval.get('score', 3.0) or 3.0)
                    final_rank_score = self._compute_final_rank_score(relevance_score, rubric_score)
                    source_tier = 'primary' if self._is_primary_source(resource) else 'fallback'

                    evaluated_resource = {
                        'resource': resource,
                        'relevance_explanation': identified.get('relevance_explanation', ''),
                        'syllabus_relevance': relevance_eval,
                        'syllabus_relevance_score': relevance_score,
                        'llm_evaluation': llm_eval,
                        'rubric_evaluation': rubric_eval,
                        'rubric_score': rubric_score,
                        'final_rank_score': final_rank_score,
                        'source_tier': source_tier,
                        'matched_topics': relevance_eval.get('matched_topics', []),
                        'license_check': license_check,
                        'criterion_links': criterion_links,
                        'integration_guidance': self._generate_integration_guidance(resource, rubric_eval, license_check)
                    }
                    
                    evaluated_resources.append(evaluated_resource)
                    if on_resource_evaluated:
                        on_resource_evaluated({
                            'evaluated_resource': evaluated_resource,
                            'evaluated_count': len(evaluated_resources),
                            'total_candidates': min(len(identified_resources), max_evaluated),
                        })
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
                                'syllabus_relevance': {
                                    'score': 1.0,
                                    'matched_topics': [],
                                    'rationale': 'Evaluation failed before relevance scoring completed.'
                                },
                                'syllabus_relevance_score': 1.0,
                                'llm_evaluation': {},
                                'rubric_evaluation': {
                                    'resource': resource,
                                    'criteria_evaluations': {},
                                    'overall_score': 0,
                                    'summary': 'Evaluation failed - resource added with minimal data'
                                },
                                'rubric_score': 0.0,
                                'final_rank_score': 0.0,
                                'source_tier': 'primary' if self._is_primary_source(resource) else 'fallback',
                                'matched_topics': [],
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
                            if on_resource_evaluated:
                                on_resource_evaluated({
                                    'evaluated_resource': minimal_resource,
                                    'evaluated_count': len(evaluated_resources),
                                    'total_candidates': min(len(identified_resources), max_evaluated),
                                })
                            logger.info(f"Added resource {idx+1} with minimal evaluation: {resource.get('title', 'Unknown')}")
                    except Exception as e2:
                        logger.error(f"Failed to add resource even with minimal evaluation: {e2}")
                    continue
            
            logger.info(f"Created {len(evaluated_resources)} evaluated resources after main loop")
            
            # Sort by combined final rank score (syllabus relevance + rubric quality).
            evaluated_resources.sort(
                key=lambda x: (
                    x.get('final_rank_score', 0),
                    x.get('rubric_score', 0),
                    len((x.get('resource') or {}).get('title', '')),
                ),
                reverse=True
            )
            
            # Step 5: Compile results - NOW that we're GUARANTEED to have evaluated_resources
            processing_time = time.time() - start_time
            
            # Final check before creating results
            logger.info(
                "FINAL CHECK: %s evaluated_resources, %s primary_resources, %s fallback_resources",
                len(evaluated_resources),
                len(primary_resources),
                len(fallback_resources),
            )
            
            results = {
                'course_code': course_code,
                'term': term,
                'syllabus_info': syllabus_info,
                'resources_found': len(all_resources) if all_resources else len(evaluated_resources),
                'resources_evaluated': len(evaluated_resources),
                'query_variants': query_variants,
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

        source_aliases = {
            'oer commons': 'OER Commons Hub',
            'oer commons hub': 'OER Commons Hub',
            'merlot': 'MERLOT',
            'open alg library': 'Open ALG Library',
            'affordable learning georgia (alg)': 'Open ALG Library',
        }

        for resource in (primary or []) + (secondary or []):
            url = self._sanitize_url(resource.get('url', ''))
            if not url:
                continue

            normalized = dict(resource)
            normalized['url'] = url
            source_raw = str(normalized.get('source') or normalized.get('source_platform') or '').strip().lower()
            if source_raw in source_aliases:
                normalized['source'] = source_aliases[source_raw]
                normalized['source_platform'] = source_aliases[source_raw]

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
        
        # Average quality and ranking signals.
        avg_rubric = sum(r.get('rubric_evaluation', {}).get('overall_score', 0)
                 for r in evaluated_resources) / len(evaluated_resources)
        avg_relevance = sum(float(r.get('syllabus_relevance_score', 0) or 0)
                    for r in evaluated_resources) / len(evaluated_resources)
        summary += f"Average Quality Score: {avg_rubric:.1f}/5.0\n"
        summary += f"Average Syllabus Relevance: {avg_relevance:.1f}/5.0\n\n"
        
        # Top resources
        summary += "Top Recommended Resources:\n"
        for i, resource in enumerate(evaluated_resources[:5], 1):
            title = resource.get('resource', {}).get('title', 'Unknown')
            score = float(resource.get('final_rank_score', 0) or 0)
            summary += f"{i}. {title} (Final Rank: {score:.1f}/5.0)\n"
        
        return summary
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return self.logger.get_usage_stats()
