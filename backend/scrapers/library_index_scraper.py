"""
Scraper to discover all syllabuses from SimpleSyllabus library index
"""
import logging
import re
import os
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, parse_qs, urlparse

logger = logging.getLogger(__name__)

LIBRARY_URL = "https://ggc.simplesyllabus.com/en-US/syllabus-library"


def parse_course_code_from_url(url: str) -> Optional[str]:
    """
    Extract course code from SimpleSyllabus URL
    
    Example URL: https://ggc.simplesyllabus.com/en-US/doc/1thnk55qi/2026-Fall-ACCT-2101-Section-01-%2881797%29?mode=view
    Returns: "ACCT 2101"
    """
    try:
        # URL decode and extract the display part of the URL
        # Format is typically: /doc/{id}/{display_name}?mode=view
        # Display name is like: 2026-Fall-ACCT-2101-Section-01-(81797)
        
        # Extract the last part before ?mode=view
        path_part = url.split('?')[0].split('/doc/')[1] if '/doc/' in url else ""
        if not path_part:
            return None
        
        # Split by hyphen and look for pattern like ACCT, COURSE, MATH, etc.
        parts = path_part.split('-')
        
        # Find course code: pattern is usually [A-Z]{2,} [0-9]{3,4}
        for i in range(len(parts) - 1):
            if parts[i].isalpha() and parts[i].isupper() and len(parts[i]) >= 2:
                # Next part should be numbers
                if parts[i + 1] and parts[i + 1][:4].isdigit():
                    course_code = f"{parts[i]} {parts[i + 1][:4]}"
                    return course_code
        
        return None
    except Exception as e:
        logger.debug(f"Error parsing course code from {url}: {e}")
        return None


def extract_metadata_from_url(url: str) -> Dict[str, Any]:
    """
    Extract metadata from URL
    
    Returns: {course_code, term, section_number, display_name, course_id}
    """
    metadata: Dict[str, Any] = {}
    
    try:
        # Extract course_id
        if '/doc/' in url:
            course_id = url.split('/doc/')[1].split('/')[0]
            metadata['course_id'] = course_id
        
        # Extract display part
        if '/doc/' in url:
            display_part = url.split('/doc/')[1].split('?')[0]
            # Remove URL encoding
            display_part = display_part.split('/', 1)[1] if '/' in display_part else display_part
            metadata['display_name'] = display_part
            
            # Parse display_name format: 2026-Fall-ACCT-2101-Section-01-(81797)
            parts = display_part.split('-')
            
            # Find year-term (e.g., 2026-Fall)
            if len(parts) >= 2 and parts[0].isdigit() and len(parts[0]) == 4:
                metadata['term'] = f"{parts[0]}-{parts[1]}"
            
            # Find course code
            for i in range(len(parts)):
                if parts[i].isalpha() and parts[i].isupper() and len(parts[i]) >= 2:
                    if i + 1 < len(parts) and parts[i + 1][:4].isdigit():
                        metadata['course_code'] = f"{parts[i]} {parts[i + 1][:4]}"
                    
                    # Section number usually comes after course code
                    if i + 3 < len(parts) and parts[i + 2] == 'Section':
                        metadata['section_number'] = parts[i + 3]
                    break
    
    except Exception as e:
        logger.debug(f"Error extracting metadata from {url}: {e}")
    
    return metadata


def fetch_library_index_for_course(course_code: str, max_pages: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch syllabus-library rows filtered by course code using the page search input.

    This avoids full index crawling and is more reliable for targeted scrape requests.
    """
    results: List[Dict[str, Any]] = []
    seen_urls = set()
    driver = None

    target_norm = ''.join(ch for ch in (course_code or '').upper() if ch.isalnum())

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        import time

        logger.info("Fetching library index for %s via targeted Selenium search", course_code)

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        driver.get(LIBRARY_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        time.sleep(1.0)

        # Find the visible search input and apply course filter.
        search_input = None
        for element in driver.find_elements(By.CSS_SELECTOR, "input[type='text']"):
            if element.is_displayed() and element.is_enabled():
                placeholder = (element.get_attribute('placeholder') or '').lower()
                if 'looking' in placeholder or 'search' in placeholder or not search_input:
                    search_input = element

        if not search_input:
            logger.warning("Could not locate syllabus-library search input for targeted course scrape")
            return []

        search_input.clear()
        search_input.send_keys(course_code)
        search_input.send_keys(Keys.ENTER)
        time.sleep(2.2)

        base_url = LIBRARY_URL.rsplit('/syllabus-library', 1)[0]

        def norm_course(value: str) -> str:
            return ''.join(ch for ch in (value or '').upper() if ch.isalnum())

        def parse_page() -> int:
            added = 0
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.select("app-library-doc-card")
            for card in cards:
                link = card.find('a', href=re.compile(r'/doc/|/en-US/doc/'))
                if not link:
                    continue

                href = link.get('href', '')
                if not href:
                    continue

                full_url = urljoin(base_url, href)
                if 'mode=view' not in full_url:
                    full_url += '?mode=view'

                if full_url in seen_urls:
                    continue

                metadata = extract_metadata_from_url(full_url)
                metadata['syllabus_url'] = full_url

                term_title = card.select_one("p.doc-term-title")
                if term_title:
                    metadata['card_title'] = term_title.get_text(strip=True)

                instructor = card.select_one(".doc-editor p")
                if instructor:
                    metadata['instructor_name'] = instructor.get_text(strip=True)

                if not metadata.get('course_code'):
                    metadata['course_code'] = parse_course_code_from_url(full_url)

                if norm_course(metadata.get('course_code', '')) != target_norm:
                    continue

                seen_urls.add(full_url)
                results.append(metadata)
                added += 1

            return added

        page = 1
        stale_pages = 0
        while page <= max_pages:
            added = parse_page()
            logger.info("Targeted page %s: added %s rows for %s (total %s)", page, added, course_code, len(results))

            next_buttons = driver.find_elements(By.CSS_SELECTOR, "button.mat-paginator-navigation-next")
            clickable_next = None
            for btn in next_buttons:
                cls = (btn.get_attribute("class") or "").lower()
                disabled_attr = btn.get_attribute("disabled")
                if btn.is_displayed() and btn.is_enabled() and "disabled" not in cls and disabled_attr is None:
                    clickable_next = btn
                    break

            if not clickable_next:
                break

            try:
                driver.execute_script("arguments[0].click();", clickable_next)
                time.sleep(1.0)
            except Exception:
                break

            if added == 0:
                stale_pages += 1
            else:
                stale_pages = 0

            if stale_pages >= 3:
                break

            page += 1

        logger.info("Targeted syllabus search found %s rows for %s", len(results), course_code)
        return results

    except Exception as e:
        logger.error("Error in targeted library search for %s: %s", course_code, e)
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def fetch_library_index() -> List[Dict[str, Any]]:
    """
    Fetch the SimpleSyllabus library index and extract all syllabus links
    Uses Selenium since links are loaded dynamically via JavaScript
    
    Returns:
        List of dicts with: {url, course_code, term, section_number, course_id, display_name}
    """
    syllabuses = []
    seen_urls = set()
    driver = None
    
    try:
        logger.info(f"Fetching library index from {LIBRARY_URL} (using Selenium for JS rendering)")
        
        # Import Selenium components
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        import time
        
        # Configure Chrome options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=options)
        driver.get(LIBRARY_URL)
        
        # Wait for cards or links to load
        logger.info("Waiting for page to load...")
        WebDriverWait(driver, 20).until(
            EC.any_of(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "app-library-doc-card")),
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/doc/') or contains(@href, '/en-US/doc/')]") )
            )
        )
        time.sleep(2)  # Extra wait for dynamic content
        
        # Expand organization filters if a "Show more" button exists.
        show_more_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Show more')]")
        for btn in show_more_buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    time.sleep(0.7)
            except Exception:
                pass

        base_url = LIBRARY_URL.rsplit('/syllabus-library', 1)[0]

        def parse_current_page() -> int:
            """Parse all cards on the current page and append unique syllabus rows."""
            added = 0
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            cards = soup.select("app-library-doc-card")
            for card in cards:
                link = card.find('a', href=re.compile(r'/doc/|/en-US/doc/'))
                if not link:
                    continue

                href = link.get('href', '')
                if not href:
                    continue

                full_url = urljoin(base_url, href)
                if 'mode=view' not in full_url:
                    full_url += '?mode=view'

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                metadata = extract_metadata_from_url(full_url)
                metadata['syllabus_url'] = full_url

                term_title = card.select_one("p.doc-term-title")
                if term_title:
                    metadata['card_title'] = term_title.get_text(strip=True)

                instructor = card.select_one(".doc-editor p")
                if instructor:
                    metadata['instructor_name'] = instructor.get_text(strip=True)

                if not metadata.get('course_code'):
                    metadata['course_code'] = parse_course_code_from_url(full_url)

                if metadata.get('course_code'):
                    syllabuses.append(metadata)
                    added += 1

            # Fallback if cards are absent: parse anchors directly.
            if not cards:
                syllabus_links = soup.find_all('a', href=re.compile(r'/doc/|/en-US/doc/'))
                for link in syllabus_links:
                    href = link.get('href', '')
                    if not href:
                        continue

                    full_url = urljoin(base_url, href)
                    if 'mode=view' not in full_url:
                        full_url += '?mode=view'

                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    metadata = extract_metadata_from_url(full_url)
                    metadata['syllabus_url'] = full_url

                    if not metadata.get('course_code'):
                        metadata['course_code'] = parse_course_code_from_url(full_url)

                    if metadata.get('course_code'):
                        syllabuses.append(metadata)
                        added += 1

            return added

        # Walk paginated results.
        max_pages = int(os.getenv('SYLLABUS_INDEX_MAX_PAGES', '120'))
        max_stale_pages = int(os.getenv('SYLLABUS_INDEX_MAX_STALE_PAGES', '5'))
        page_num = 1
        stale_pages = 0

        def get_range_label() -> str:
            """Read paginator range label when available (for example, '51-100 of 3150')."""
            selectors = [
                ".mat-mdc-paginator-range-label",
                ".mat-paginator-range-label",
            ]
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = (element.text or '').strip()
                    if text:
                        return text
            return ''

        while page_num <= max_pages:
            # Some pages lazy-load cards; nudge scroll a little before parse.
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.6)

            before = len(syllabuses)
            added = parse_current_page()
            after = len(syllabuses)
            logger.info(f"Page {page_num}: added {added} unique rows (total {after})")

            next_buttons = driver.find_elements(By.CSS_SELECTOR, "button.mat-paginator-navigation-next")
            clickable_next = None
            for btn in next_buttons:
                cls = (btn.get_attribute("class") or "").lower()
                disabled_attr = btn.get_attribute("disabled")
                if btn.is_displayed() and btn.is_enabled() and "disabled" not in cls and disabled_attr is None:
                    clickable_next = btn
                    break

            if not clickable_next:
                break

            try:
                prev_label = get_range_label()
                driver.execute_script("arguments[0].click();", clickable_next)
                # Wait for paginator to move to a new range if label exists.
                moved = False
                if prev_label:
                    for _ in range(12):
                        time.sleep(0.35)
                        if get_range_label() != prev_label:
                            moved = True
                            break
                else:
                    time.sleep(1.2)
                    moved = True

                if not moved:
                    stale_pages += 1
                    logger.info(
                        "Paginator did not advance after next-click on page %s (stale %s/%s)",
                        page_num,
                        stale_pages,
                        max_stale_pages,
                    )
                else:
                    stale_pages = 0
            except Exception:
                break

            if added == 0:
                stale_pages += 1
            else:
                stale_pages = 0

            if stale_pages >= max_stale_pages:
                logger.info(
                    "Stopping library crawl after %s stale pages (no new unique rows)",
                    stale_pages,
                )
                break

            page_num += 1
        
        logger.info(f"Successfully extracted {len(syllabuses)} unique syllabuses with course codes")
        return syllabuses
    
    except Exception as e:
        logger.error(f"Error fetching library index with Selenium: {e}")
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def fetch_library_index_paginated(max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch library index with pagination support (if the library implements pagination)
    
    Args:
        max_pages: Maximum number of pages to fetch (None for all)
    
    Returns:
        List of syllabus metadata
    """
    all_syllabuses = []
    page = 1
    
    try:
        while max_pages is None or page <= max_pages:
            logger.info(f"Fetching page {page}...")
            
            # Try fetching with page parameter (common pagination pattern)
            paginated_url = f"{LIBRARY_URL}?page={page}"
            response = requests.get(paginated_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            syllabus_links = soup.find_all('a', href=re.compile(r'/en-US/doc/'))
            
            logger.info(f"Page {page}: Found {len(syllabus_links)} syllabus links")
            
            if not syllabus_links:
                # No more pages
                logger.info(f"No more syllabuses found at page {page}")
                break
            
            for link in syllabus_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                full_url = urljoin(LIBRARY_URL.split('/syllabus-library')[0], href)
                if 'mode=view' not in full_url:
                    full_url += '?mode=view'
                
                metadata = extract_metadata_from_url(full_url)
                metadata['syllabus_url'] = full_url
                
                if not metadata.get('course_code'):
                    metadata['course_code'] = parse_course_code_from_url(full_url)
                
                if metadata.get('course_code'):
                    all_syllabuses.append(metadata)
            
            page += 1
    
    except Exception as e:
        logger.error(f"Error in paginated fetch: {e}")
        logger.info(f"Retrieved {len(all_syllabuses)} syllabuses before error")
    
    return all_syllabuses


if __name__ == '__main__':
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    
    syllabuses = fetch_library_index()
    print(f"\nTotal syllabuses found: {len(syllabuses)}\n")
    
    # Print first 5 as examples
    for i, s in enumerate(syllabuses[:5], 1):
        print(f"{i}. {s.get('course_code')} - {s.get('term', 'N/A')} (Section {s.get('section_number', 'N/A')})")
        print(f"   URL: {s.get('syllabus_url')}\n")
