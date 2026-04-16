"""
Selenium scraper for MERLOT search results.
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus
import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MerlotSeleniumScraper:
    """Dedicated Selenium scraper for MERLOT."""

    BASE_URL = 'https://www.merlot.org'
    SEARCH_URL = 'https://www.merlot.org/merlot/materials.htm?keywords={query}'

    def __init__(self, timeout_seconds: int = 12) -> None:
        self.timeout_seconds = timeout_seconds

    def search_resources(self, query: str, course_code: str = '') -> List[Dict]:
        query_text = (query or course_code or '').strip()
        if not query_text:
            return []

        search_url = self.SEARCH_URL.format(query=quote_plus(query_text))
        html = self._fetch_with_selenium(search_url)
        if not html:
            return []

        return self._parse_search_results(html, search_url, query_text)

    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
        except Exception:
            logger.warning("Selenium is unavailable for MERLOT scraper")
            return None

        driver = None
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1600,1200')

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout_seconds)
            driver.get(url)

            WebDriverWait(driver, self.timeout_seconds).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            return driver.page_source
        except Exception as exc:
            logger.info("MERLOT Selenium request failed for %s: %s", url, exc)
            return None
        finally:
            if driver:
                driver.quit()

    def _parse_search_results(self, html: str, search_url: str, query_text: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        resources: List[Dict] = []
        seen = set()

        for link in soup.find_all('a', href=True):
            href = (link.get('href') or '').strip()
            text = self._clean_text(link.get_text(' ', strip=True))
            if not href or not text or len(text) < 2:
                continue

            full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
            if full_url in seen:
                continue
            if not self._is_material_link(full_url, text):
                continue

            title = text
            if self._is_generic_title(title):
                title = self._extract_context_title(link) or title
            if len(title) < 3:
                continue

            seen.add(full_url)
            resources.append({
                'title': title[:180],
                'url': full_url,
                'description': f'MERLOT result for {query_text}.',
                'author': 'MERLOT',
                'license': 'Varies',
                'source': 'MERLOT',
                'source_platform': 'MERLOT',
                'source_search_url': search_url,
                'query': query_text,
            })

            if len(resources) >= 12:
                break

        return resources

    def _is_material_link(self, url: str, text: str) -> bool:
        path = url.lower()
        text_lower = text.lower()

        if any(skip in path for skip in ['/login', '/privacy', '/terms', '/contact']):
            return False
        if any(skip in text_lower for skip in ['sign in', 'login', 'privacy', 'terms']):
            return False

        if '/merlot/viewmaterial' in path:
            return True
        if '/materials.htm?materialid=' in path:
            return True

        # Prefer explicit material detail targets only.
        if '/materials.htm' in path and 'materialid=' in path:
            return True

        return False

    def _clean_text(self, text: str) -> str:
        return ' '.join((text or '').split()).strip()

    def _extract_context_title(self, link) -> str:
        """Try to recover a useful title from nearby card/container headings."""
        # Walk up a few parents and search for heading-like text.
        current = link
        for _ in range(4):
            current = getattr(current, 'parent', None)
            if current is None:
                break
            heading = current.find(['h1', 'h2', 'h3', 'h4'])
            if heading:
                text = self._clean_text(heading.get_text(' ', strip=True))
                if text and not self._is_generic_title(text):
                    return text

        # Fallback to parent block text first sentence.
        current = link.parent
        if current is not None:
            text = self._clean_text(current.get_text(' ', strip=True))
            if text:
                text = text.split(' . ')[0][:180]
                if text and not self._is_generic_title(text):
                    return text
        return ''

    def _is_generic_title(self, text: str) -> bool:
        lower = text.lower().strip()
        banned = {
            'go to material',
            'go to material isexternal',
            'material type',
            'connections',
            'humanities',
            'next',
            'previous',
            'view details',
        }
        return lower in banned
