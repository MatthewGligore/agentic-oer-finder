"""
Selenium scraper for OER Commons search results.
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus
import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class OERCommonsSeleniumScraper:
    """Dedicated Selenium scraper for OER Commons."""

    BASE_URL = 'https://www.oercommons.org'
    SEARCH_URL = 'https://www.oercommons.org/search?f.search={query}&search_source=site'

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
            logger.warning("Selenium is unavailable for OER Commons scraper")
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
            logger.info("OER Commons Selenium request failed for %s: %s", url, exc)
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
            if not href or not text or len(text) < 4:
                continue
            if self._is_generic_title(text):
                continue

            full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
            if full_url in seen:
                continue
            if not self._is_courseware_link(full_url):
                continue

            seen.add(full_url)
            resources.append({
                'title': text[:180],
                'url': full_url,
                'description': f'OER Commons result for {query_text}.',
                'author': 'OER Commons',
                'license': 'Varies',
                'source': 'OER Commons Hub',
                'source_platform': 'OER Commons Hub',
                'source_search_url': search_url,
                'query': query_text,
            })

            if len(resources) >= 12:
                break

        return resources

    def _is_courseware_link(self, url: str) -> bool:
        lower = url.lower()
        if any(skip in lower for skip in ['/login', '/privacy', '/terms', '/about', '/groups']):
            return False
        return '/courseware/' in lower or '/authoring/' in lower

    def _clean_text(self, text: str) -> str:
        return ' '.join((text or '').split()).strip()

    def _is_generic_title(self, text: str) -> bool:
        lower = text.lower().strip()
        generic = {
            'see more',
            'learn more',
            'details',
            'next',
            'previous',
            'view all',
            'search',
        }
        return lower in generic
