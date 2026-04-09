"""
Multi-platform OER source scraper.
Collects candidate resources across major OER platforms, then normalizes results.
"""

from typing import Dict, List
from urllib.parse import quote_plus, urljoin, urlparse
import logging
import re
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PlatformAggregatorScraper:
    """Scrape/search multiple OER platforms with a resilient fallback strategy."""

    CONNECT_TIMEOUT_SECONDS = 2
    READ_TIMEOUT_SECONDS = 3
    MAX_SEARCH_SECONDS = 12

    PLATFORMS = [
        {
            'name': 'Affordable Learning Georgia (ALG)',
            'base_url': 'https://alg.manifoldapp.org',
            'search_url': 'https://alg.manifoldapp.org/search?q={query}',
            'priority': 10,
        },
        {
            'name': 'MERLOT',
            'base_url': 'https://www.merlot.org',
            'search_url': 'https://www.merlot.org/merlot/materials.htm?keywords={query}',
            'priority': 10,
        },
        {
            'name': 'HBCU Affordable Learning Community Portal',
            'base_url': 'https://hbcuaffordablelearning.org',
            'search_url': 'https://hbcuaffordablelearning.org/?s={query}',
            'priority': 9,
        },
        {
            'name': 'LibreTexts Campus Bookshelf',
            'base_url': 'https://libretexts.org',
            'search_url': 'https://query.libretexts.org/?query={query}',
            'priority': 10,
        },
        {
            'name': 'Pressbooks Directory',
            'base_url': 'https://directory.pressbooks.com',
            'search_url': 'https://directory.pressbooks.com/?s={query}',
            'priority': 8,
        },
        {
            'name': 'OER Commons Hub',
            'base_url': 'https://www.oercommons.org',
            'search_url': 'https://www.oercommons.org/search?f.search={query}&search_source=site',
            'priority': 10,
        },
        {
            'name': 'Knowledge Commons Works',
            'base_url': 'https://works.hcommons.org',
            'search_url': 'https://works.hcommons.org/?s={query}',
            'priority': 8,
        },
        {
            'name': 'GeneralSpace (GGC)',
            'base_url': 'https://generalspace.ggc.edu',
            'search_url': 'https://generalspace.ggc.edu/?s={query}',
            'priority': 7,
        },
    ]

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def search_resources(self, query: str, course_code: str = '') -> List[Dict]:
        """Search all configured platforms and return normalized candidate resources."""
        query_text = (query or course_code or '').strip()
        if not query_text:
            return []

        query_terms = self._tokenize(f"{query_text} {course_code}")
        collected: List[Dict] = []
        started = time.time()

        for platform in self.PLATFORMS:
            if (time.time() - started) >= self.MAX_SEARCH_SECONDS:
                logger.info("Platform aggregator timed out at %.2fs; returning partial results", time.time() - started)
                break

            source_name = platform['name']
            search_url = platform['search_url'].format(query=quote_plus(query_text))
            priority = int(platform.get('priority', 5))

            page_resources = self._scrape_platform_page(platform, search_url, query_text, query_terms)

            if not page_resources:
                # Always include a searchable source entry so users can click through.
                page_resources = [
                    {
                        'title': f"{source_name} search for {course_code or query_text}",
                        'url': search_url,
                        'description': f"Open this curated search on {source_name} for {query_text}.",
                        'author': source_name,
                        'license': 'Varies',
                        'source': source_name,
                        'source_platform': source_name,
                        'source_search_url': search_url,
                        'query': query_text,
                        '_priority': priority,
                        '_score': priority,
                    }
                ]

            collected.extend(page_resources)

        deduped = self._dedupe_and_rank(collected)
        logger.info(f"Platform aggregator found {len(deduped)} resources for query: {query_text}")
        return deduped

    def _scrape_platform_page(
        self,
        platform: Dict,
        search_url: str,
        query_text: str,
        query_terms: List[str],
    ) -> List[Dict]:
        """Fetch a platform search page and extract likely resource links."""
        source_name = platform['name']
        base_url = platform['base_url']
        priority = int(platform.get('priority', 5))

        try:
            response = self.session.get(
                search_url,
                timeout=(self.CONNECT_TIMEOUT_SECONDS, self.READ_TIMEOUT_SECONDS),
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.info(f"Skipping platform {source_name} due to request issue: {exc}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        candidates: List[Dict] = []
        seen = set()

        for link in soup.find_all('a', href=True):
            href = (link.get('href') or '').strip()
            text = self._clean_text(link.get_text(' ', strip=True))
            if not href or not text:
                continue

            full_url = urljoin(response.url, href)
            if full_url in seen:
                continue
            if not self._is_resource_like_link(full_url, text):
                continue

            haystack = f"{text} {full_url}".lower()
            score = priority + self._score_match(haystack, query_terms)
            if score <= priority:
                continue

            seen.add(full_url)
            candidates.append({
                'title': text[:180],
                'url': full_url,
                'description': f"Candidate resource from {source_name} for {query_text}.",
                'author': source_name,
                'license': 'Varies',
                'source': source_name,
                'source_platform': source_name,
                'source_search_url': search_url,
                'query': query_text,
                '_priority': priority,
                '_score': score,
            })

            if len(candidates) >= 4:
                break

        return candidates

    def _dedupe_and_rank(self, resources: List[Dict]) -> List[Dict]:
        """Dedupe resources by URL and return the strongest matches first."""
        by_url: Dict[str, Dict] = {}

        for resource in resources:
            url = resource.get('url', '').strip()
            if not url:
                continue

            existing = by_url.get(url)
            if not existing or resource.get('_score', 0) > existing.get('_score', 0):
                by_url[url] = resource

        ranked = sorted(
            by_url.values(),
            key=lambda item: (item.get('_score', 0), item.get('_priority', 0), len(item.get('title', ''))),
            reverse=True,
        )

        clean = []
        for item in ranked:
            out = dict(item)
            out.pop('_priority', None)
            out.pop('_score', None)
            clean.append(out)
        return clean

    def _tokenize(self, text: str) -> List[str]:
        tokens = []
        for token in re.split(r'[^a-zA-Z0-9]+', (text or '').lower()):
            token = token.strip()
            if len(token) >= 2:
                tokens.append(token)
        return list(dict.fromkeys(tokens))

    def _score_match(self, haystack: str, query_terms: List[str]) -> int:
        score = 0
        for term in query_terms:
            if term in haystack:
                score += 3 if len(term) > 3 else 1
        if any(term.isdigit() and term in haystack for term in query_terms):
            score += 2
        return score

    def _is_resource_like_link(self, url: str, text: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False

        path_lower = (parsed.path or '').lower()
        text_lower = (text or '').lower()
        generic_text = {
            'skip to main',
            'skip to main content',
            'search site',
            'browse',
            'members',
            'bookmark collections',
            'add oer',
            'home',
            'menu',
        }

        if any(skip in path_lower for skip in ['/login', '/signin', '/signup', '/privacy', '/terms', '/contact']):
            return False
        if any(skip in text_lower for skip in ['login', 'sign in', 'privacy policy', 'terms of use', 'cookie']):
            return False
        if text_lower in generic_text:
            return False
        if len(text_lower) < 4:
            return False
        # Avoid obvious navigation-only targets.
        if path_lower in {'/', '/home', '/search'} and '?' not in (parsed.query or ''):
            return False

        return True

    def _clean_text(self, text: str) -> str:
        return ' '.join((text or '').split()).strip()
