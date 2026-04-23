"""
Web scraper for Open ALG Library
Scrapes open educational resources from alg.manifoldapp.org
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ALGScraper:
    """Scraper for Open ALG Library"""

    CONNECT_TIMEOUT_SECONDS = 3
    READ_TIMEOUT_SECONDS = 4
    SEARCH_CONNECT_TIMEOUT_SECONDS = 2
    SEARCH_READ_TIMEOUT_SECONDS = 3
    DETAIL_CONNECT_TIMEOUT_SECONDS = 2
    DETAIL_READ_TIMEOUT_SECONDS = 3
    MAX_SEARCH_SECONDS = 18
    MAX_DISCOVERY_PAGES = 10
    MAX_PAGINATION_LINKS_PER_PAGE = 4
    MAX_DETAIL_ENRICHMENTS = 6

    INDEX_PAGES = [
        '/',
        '/projects/all',
        '/projects/project-collection/textbooks',
        '/projects/project-collection/ancillary',
    ]

    SUBJECT_KEYWORDS = {
        'engl': ['english', 'writing', 'composition', 'rhetoric', 'literacy', 'first-year writing'],
        'itec': ['information systems', 'technology', 'programming', 'software', 'computer', 'web', 'database', 'network'],
        'comp': ['computer', 'programming', 'software', 'web', 'database', 'network'],
        'cs': ['computer', 'programming', 'software', 'web', 'database', 'network'],
        'biol': ['biology', 'biological', 'anatomy', 'physiology', 'cell', 'genetics'],
        'chem': ['chemistry', 'chemical', 'organic chemistry', 'general chemistry'],
        'hist': ['history', 'government', 'politics', 'american history', 'world history'],
        'math': ['math', 'algebra', 'calculus', 'precalculus', 'statistics'],
        'arts': ['art', 'design', 'visual', 'media'],
        'psych': ['psychology', 'behavior', 'cognition'],
    }
    
    def __init__(self, base_url='https://alg.manifoldapp.org'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_resources(self, query: str, course_code: str = None) -> List[Dict]:
        """
        Search for OER resources in Open ALG Library
        
        Args:
            query: Search query (course name, topic, etc.)
            course_code: Optional course code for context
        
        Returns:
            List of OER resource dictionaries
        """
        try:
            started = time.time()
            query_terms = self._build_query_terms(query, course_code)
            subject_terms = self._subject_terms(course_code)
            resources_by_url: Dict[str, Dict] = {}

            # Fast path: use the original /search endpoint approach first.
            fast_results = self._search_via_search_endpoint(query, course_code)
            for candidate in fast_results:
                resource_url = candidate.get('url', '')
                if not resource_url:
                    continue
                score = self._score_candidate(candidate, query_terms, subject_terms)
                if score <= 0:
                    continue
                candidate['_score'] = score
                existing = resources_by_url.get(resource_url)
                if not existing or score > existing.get('_score', 0):
                    resources_by_url[resource_url] = candidate

            if resources_by_url:
                logger.info("ALG fast search returned %s candidates for query: %s", len(resources_by_url), query)
                ranked = sorted(
                    resources_by_url.values(),
                    key=lambda item: (item.get('_score', 0), len(item.get('title', ''))),
                    reverse=True,
                )
                clean = []
                for item in ranked[:20]:
                    out = dict(item)
                    out.pop('_score', None)
                    clean.append(out)
                logger.info(f"Found {len(clean)} resources for query: {query}")
                return clean

            # Crawl stable project index and collection pages instead of the JS-only search shell.
            page_urls = self._discover_index_pages()

            for page_url in page_urls:
                if (time.time() - started) >= self.MAX_SEARCH_SECONDS:
                    logger.info("ALG crawl timed out at %.2fs; returning partial results", time.time() - started)
                    break
                try:
                    response = self.session.get(
                        page_url,
                        timeout=(self.CONNECT_TIMEOUT_SECONDS, self.READ_TIMEOUT_SECONDS),
                    )
                    response.raise_for_status()
                except requests.RequestException as exc:
                    logger.debug(f"Skipping ALG page {page_url}: {exc}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                for candidate in self._extract_project_candidates(soup, page_url):
                    resource_url = candidate.get('url', '')
                    if not resource_url:
                        continue

                    score = self._score_candidate(candidate, query_terms, subject_terms)
                    if score <= 0:
                        continue

                    existing = resources_by_url.get(resource_url)
                    if not existing or score > existing.get('_score', 0):
                        candidate['_score'] = score
                        resources_by_url[resource_url] = candidate

            resources = sorted(
                resources_by_url.values(),
                key=lambda item: (item.get('_score', 0), len(item.get('title', ''))),
                reverse=True,
            )

            # Enrich the best matches with detail pages so callers get usable titles, descriptions, and URLs.
            enriched_resources: List[Dict] = []
            for resource in resources[:self.MAX_DETAIL_ENRICHMENTS]:
                if (time.time() - started) >= self.MAX_SEARCH_SECONDS:
                    logger.info("ALG detail enrichment timed out at %.2fs; returning current results", time.time() - started)
                    break
                detail = self.get_resource_details(resource.get('url', '')) or {}
                merged = {
                    'title': detail.get('title') or resource.get('title', ''),
                    'url': resource.get('url', ''),
                    'description': detail.get('description') or resource.get('description', ''),
                    'author': detail.get('author') or resource.get('author', ''),
                    'license': detail.get('license') or resource.get('license', ''),
                    'tags': detail.get('subjects') or resource.get('tags', []),
                    'source': 'Open ALG Library',
                    'query': query,
                }
                enriched_resources.append(merged)

            # Keep additional ranked candidates without detail fetch to avoid long waits.
            for resource in resources[self.MAX_DETAIL_ENRICHMENTS:20]:
                enriched_resources.append({
                    'title': resource.get('title', ''),
                    'url': resource.get('url', ''),
                    'description': resource.get('description', ''),
                    'author': resource.get('author', ''),
                    'license': resource.get('license', ''),
                    'tags': resource.get('tags', []),
                    'source': 'Open ALG Library',
                    'query': query,
                })

            logger.info(f"Found {len(enriched_resources)} resources for query: {query}")
            return enriched_resources
            
        except requests.RequestException as e:
            logger.error(f"Error scraping ALG Library for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in ALG scraper: {e}")
            return []

    def _search_via_search_endpoint(self, query: str, course_code: str = None) -> List[Dict]:
        """Quickly parse the ALG /search endpoint using the legacy strategy."""
        search_url = f"{self.base_url}/search"
        params = {'q': query}
        if course_code:
            params['course'] = course_code

        try:
            response = self.session.get(
                search_url,
                params=params,
                timeout=(self.SEARCH_CONNECT_TIMEOUT_SECONDS, self.SEARCH_READ_TIMEOUT_SECONDS),
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.info(f"ALG fast search endpoint unavailable for '{query}': {exc}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        resources: List[Dict] = []

        resource_items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'resource|project|book|item', re.I))
        for item in resource_items:
            resource_info = self._extract_resource_info(item, query)
            if resource_info:
                resources.append(resource_info)

        if not resources:
            links = soup.find_all('a', href=re.compile(r'/projects/|/resources/|/books/', re.I))
            for link in links[:20]:
                href = link.get('href', '')
                if href and ('/projects/all' in href.lower() or '/all' in href.lower()):
                    continue
                resource_info = self._extract_from_link(link, query)
                if resource_info and resource_info.get('title') and resource_info.get('title').lower() != 'projects':
                    resources.append(resource_info)

        return resources

    def _discover_index_pages(self) -> List[str]:
        """Discover stable ALG index pages and pagination links to crawl."""
        pages = []
        seen = set()

        def add_page(url: str) -> None:
            if url not in seen:
                seen.add(url)
                pages.append(url)

        for path in self.INDEX_PAGES:
            add_page(urljoin(self.base_url, path))

        # Expand pagination from the main index and collection pages with a hard cap
        # so Step 2 cannot grow into an unbounded crawl.
        crawl_queue = list(pages)
        while crawl_queue and len(pages) < self.MAX_DISCOVERY_PAGES:
            page_url = crawl_queue.pop(0)
            try:
                response = self.session.get(
                    page_url,
                    timeout=(self.CONNECT_TIMEOUT_SECONDS, self.READ_TIMEOUT_SECONDS),
                )
                response.raise_for_status()
            except requests.RequestException:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            added_from_page = 0
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if not href.startswith('/projects/'):
                    continue
                if '?page=' not in href:
                    continue
                if any(skip in href.lower() for skip in ['/projects/all', '/project-collection']) or 'page=' not in href:
                    # Keep pagination pages only for the stable collection/index pages.
                    pass

                full_url = urljoin(self.base_url, href)
                if full_url not in seen:
                    add_page(full_url)
                    crawl_queue.append(full_url)
                    added_from_page += 1
                    if added_from_page >= self.MAX_PAGINATION_LINKS_PER_PAGE:
                        break

        if len(pages) >= self.MAX_DISCOVERY_PAGES:
            logger.info(
                "ALG discovery capped at %s pages to keep search responsive",
                self.MAX_DISCOVERY_PAGES,
            )

        return pages

    def _extract_project_candidates(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract project candidates from a page of ALG content."""
        candidates: List[Dict] = []
        seen = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if not href.startswith('/projects/'):
                continue
            if any(skip in href.lower() for skip in ['/projects/all', '/project-collection', '/search', '/subscriptions', '/privacy']):
                continue
            if href in seen:
                continue

            title = self._normalize_text(link.get_text(' ', strip=True))
            if not title or self._is_generic_title(title):
                continue

            seen.add(href)
            parent_text = self._normalize_text(link.parent.get_text(' ', strip=True)) if link.parent else ''
            candidates.append({
                'title': title,
                'url': urljoin(self.base_url, href),
                'description': parent_text[:350],
                'author': '',
                'license': '',
                'source_page': page_url,
                'tags': [],
            })

        return candidates

    def _build_query_terms(self, query: str, course_code: str = None) -> List[str]:
        terms = []
        raw = f"{query or ''} {course_code or ''}"
        for token in re.split(r'[^a-zA-Z0-9]+', raw.lower()):
            token = token.strip()
            if len(token) >= 2:
                terms.append(token)
        return list(dict.fromkeys(terms))

    def _subject_terms(self, course_code: str = None) -> List[str]:
        if not course_code:
            return []

        subject = course_code.split()[0].lower() if course_code.split() else course_code.lower()
        return self.SUBJECT_KEYWORDS.get(subject, [])

    def _normalize_text(self, text: str) -> str:
        return ' '.join((text or '').split()).strip()

    def _is_generic_title(self, title: str) -> bool:
        generic = {'projects', 'resources', 'books', 'all', 'browse', 'search', 'home', 'library', 'prev', 'next'}
        return title.lower() in generic or len(title) < 4

    def _score_candidate(self, candidate: Dict, query_terms: List[str], subject_terms: List[str]) -> int:
        text = f"{candidate.get('title', '')} {candidate.get('description', '')}".lower()
        score = 0

        for term in query_terms:
            if not term:
                continue
            if term in text:
                score += 3 if len(term) > 3 else 1

        for term in subject_terms:
            if term in text:
                score += 2

        # Strong boosts for course-code-like matches.
        if any(term.isdigit() and term in text for term in query_terms):
            score += 4
        if any(term in {'engl', 'english', 'writing', 'composition'} for term in query_terms) and any(word in text for word in ['writing', 'composition', 'rhetoric', 'english', 'literacy']):
            score += 4
        if any(term in {'itec', 'cs', 'comp', 'programming', 'computer', 'technology'} for term in query_terms) and any(word in text for word in ['programming', 'computer', 'software', 'technology', 'database', 'web']):
            score += 4

        return score
    
    def _extract_resource_info(self, element, query: str) -> Optional[Dict]:
        """Extract resource information from HTML element"""
        try:
            # Extract title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|name', re.I))
            if not title_elem:
                title_elem = element.find('a', class_=re.compile(r'title|name', re.I))
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            if not title:
                return None
            
            # Extract link
            link_elem = element.find('a', href=True) if element.name != 'a' else element
            link = link_elem.get('href', '') if link_elem else ''
            if link and not link.startswith('http'):
                link = f"{self.base_url}{link}"
            
            # Extract description
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary|abstract', re.I))
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract author/creator
            author_elem = element.find(['span', 'div'], class_=re.compile(r'author|creator|by', re.I))
            author = author_elem.get_text(strip=True) if author_elem else ''
            
            # Extract license information
            license_elem = element.find(['span', 'div'], class_=re.compile(r'license', re.I))
            license_text = license_elem.get_text(strip=True) if license_elem else ''
            
            # Extract subjects/tags
            tags = []
            tag_elems = element.find_all(['span', 'a'], class_=re.compile(r'tag|subject|category', re.I))
            tags = [tag.get_text(strip=True) for tag in tag_elems]
            
            return {
                'title': title,
                'url': link,
                'description': description,
                'author': author,
                'license': license_text,
                'tags': tags,
                'source': 'Open ALG Library',
                'query': query
            }
        except Exception as e:
            logger.debug(f"Error extracting resource info: {e}")
            return None
    
    def _extract_from_link(self, link_elem, query: str) -> Optional[Dict]:
        """Extract resource info from a link element"""
        try:
            title = link_elem.get_text(strip=True)
            href = link_elem.get('href', '')
            
            if not title or not href:
                return None
            
            # Skip generic/listing pages
            href_lower = href.lower()
            if any(skip in href_lower for skip in ['/all', '/projects/all', '/resources/all', '/books/all', '/browse', '/search']):
                return None
            
            # Skip if title is too generic
            title_lower = title.lower()
            if title_lower in ['projects', 'resources', 'books', 'all', 'browse', 'search', 'home', 'library']:
                return None
            
            if not href.startswith('http'):
                href = f"{self.base_url}{href}"
            
            # Try to get more info from parent
            parent = link_elem.parent
            description = ''
            if parent:
                desc_elem = parent.find(['p', 'div', 'span'])
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:200]
            
            return {
                'title': title,
                'url': href,
                'description': description,
                'author': '',
                'license': '',
                'tags': [],
                'source': 'Open ALG Library',
                'query': query
            }
        except Exception as e:
            logger.debug(f"Error extracting from link: {e}")
            return None
    
    def get_resource_details(self, resource_url: str) -> Optional[Dict]:
        """Get detailed information about a specific resource"""
        try:
            response = self.session.get(
                resource_url,
                timeout=(self.DETAIL_CONNECT_TIMEOUT_SECONDS, self.DETAIL_READ_TIMEOUT_SECONDS),
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract detailed information
            details = {
                'url': resource_url,
                'title': '',
                'description': '',
                'author': '',
                'license': '',
                'subjects': [],
                'full_text': ''
            }
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                details['title'] = title_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = soup.find('meta', attrs={'name': 'description'})
            if desc_elem:
                details['description'] = desc_elem.get('content', '')
            else:
                desc_elem = soup.find(['div', 'p'], class_=re.compile(r'description|summary', re.I))
                if desc_elem:
                    details['description'] = desc_elem.get_text(strip=True)[:500]
            
            # Extract license
            license_elem = soup.find(['span', 'div'], class_=re.compile(r'license', re.I))
            if license_elem:
                details['license'] = license_elem.get_text(strip=True)
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if main_content:
                # Remove scripts and styles
                for script in main_content(["script", "style"]):
                    script.decompose()
                
                text = main_content.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                details['full_text'] = ' '.join(chunk for chunk in chunks if chunk)[:5000]  # Limit length
            
            return details
        except Exception as e:
            logger.error(f"Error getting resource details from {resource_url}: {e}")
            return None
