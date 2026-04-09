"""
Scraper to fetch and parse syllabus content into structured sections
"""
import logging
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

logger = logging.getLogger(__name__)

# Section type patterns for matching
SECTION_PATTERNS = {
    'objectives': [
        r'course\s+outcomes',
        r'(?:course\s+)?objectives',
        r'learning\s+outcomes',
        r'course\s+goals',
        r'course\s+description',
        r'learning\s+goals'
    ],
    'topics': [
        r'(?:course\s+)?content',
        r'topics',
        r'weekly\s+schedule',
        r'(?:course\s+)?outline',
        r'course\s+schedule',
        r'(?:unit|module|chapter)\s+(?:topics|outlines?)'
    ],
    'grading': [
        r'grading',
        r'grading\s+(?:rubric|scale)',
        r'(?:grade\s+)?distribution',
        r'assessment\s+weight',
        r'scoring'
    ],
    'prerequisites': [
        r'prerequisites',
        r'(?:course\s+)?requirements',
        r'prerequisite\s+courses?'
    ],
    'resources': [
        r'(?:required\s+)?materials',
        r'textbooks?',
        r'(?:required\s+)?resources',
        r'books?',
        r'(?:course\s+)?materials'
    ],
    'assessment': [
        r'assignments?',
        r'(?:quizzes?|exams?)',
        r'projects?',
        r'(?:tests?|assessments?)',
        r'(?:participation|activities)',
        r'(?:final\s+)?exam'
    ],
    'policies': [
        r'(?:course\s+)?policies',
        r'attendance',
        r'academic\s+integrity',
        r'(?:classroom\s+)?conduct',
        r'(?:participation\s+)?policy',
        r'(?:late\s+)?submission'
    ]
}

HEADING_TO_SECTION = {
    'course outcomes': 'objectives',
    'course objectives': 'objectives',
    'learning outcomes': 'objectives',
    'course goals': 'objectives',
    'grading': 'grading',
    'grading policy': 'grading',
    'course content': 'topics',
    'course schedule': 'topics',
    'required materials': 'resources',
    'textbook': 'resources',
    'prerequisites': 'prerequisites',
    'course policies': 'policies',
    'attendance policy': 'policies',
    'academic integrity': 'policies',
}


def clean_text(text: str) -> str:
    """
    Clean extracted text:
    - Remove HTML tags (if any remained)
    - Normalize whitespace
    - Remove excessive line breaks
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace (multiple spaces to single space)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Reduce multiple newlines to max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_sections_from_html(html_content: str) -> Dict[str, str]:
    """
    Parse HTML content and extract syllabus sections
    
    Returns:
        Dict mapping section_type to section_content    
    """
    sections: Dict[str, str] = {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for tag in soup(['script', 'style']):
        tag.decompose()

    # First pass: extract structured content from named component blocks.
    component_sections = _extract_component_sections(soup)
    if component_sections:
        return component_sections
    
    # Get all text
    text = soup.get_text(separator='\n')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    # Try to identify sections based on heading patterns
    for section_type, patterns in SECTION_PATTERNS.items():
        # Search for each pattern in the text (case-insensitive)
        for pattern in patterns:
            # Find all heading matches
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                start_pos = match.start()
                
                # Find next section heading or end of document
                next_heading_pos = len(text)
                
                # Look for common heading patterns
                remaining_text = text[start_pos + len(match.group()):]
                heading_pattern = re.search(r'\n(?:^|\n)[A-Z][A-Za-z\s\d]{5,}:?', remaining_text)
                if heading_pattern:
                    next_heading_pos = start_pos + len(match.group()) + heading_pattern.start()
                
                # Extract section content (up to 2000 chars or next heading)
                section_content = text[start_pos:next_heading_pos]
                section_content = clean_text(section_content)
                
                if len(section_content) > 50:  # Only keep if we have substantial content
                    if section_type not in sections or len(section_content) > len(sections[section_type]):
                        sections[section_type] = section_content
                
                # Once we find a match for this section type, move on
                break

            if section_type in sections:
                break
    
    # Fallback: If no sections found with patterns, try to extract all text
    # and split heuristically
    if not sections:
        logger.warning("No sections identified by pattern matching; storing full content as 'other'")
        sections['other'] = clean_text(text[:3000])  # Store first 3000 chars
    
    return sections


def _extract_component_sections(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract sections from the Angular component blocks that include explicit headings."""
    sections: Dict[str, str] = {}

    wrappers = soup.select('div.component-wrapper')
    for wrapper in wrappers:
        heading_el = wrapper.select_one('h2.component-name, h2.app-name-view')
        body_el = wrapper.select_one('div.component-body')

        if not heading_el or not body_el:
            continue

        heading_text = clean_text(heading_el.get_text(' ', strip=True)).lower()
        body_text = clean_text(body_el.get_text('\n', strip=True))
        if not body_text or len(body_text) < 30:
            continue

        section_type = _map_heading_to_section_type(heading_text)
        if not section_type:
            section_type = 'other'

        existing = sections.get(section_type, '')
        if len(body_text) > len(existing):
            sections[section_type] = body_text

    return sections


def _map_heading_to_section_type(heading_text: str) -> Optional[str]:
    """Map heading text to one of the supported section types."""
    if heading_text in HEADING_TO_SECTION:
        return HEADING_TO_SECTION[heading_text]

    # Fuzzy contains mapping for heading variants.
    for key, value in HEADING_TO_SECTION.items():
        if key in heading_text:
            return value

    return None


def _has_meaningful_syllabus_content(html_content: str) -> bool:
    """Detect whether fetched HTML contains actual syllabus content instead of shell markup."""
    soup = BeautifulSoup(html_content, 'html.parser')

    if soup.select('div.component-wrapper h2.component-name, div.component-wrapper h2.app-name-view'):
        return True

    text = clean_text(soup.get_text('\n', strip=True)).lower()
    signals = ['course outcomes', 'learning outcomes', 'grading', 'course policies', 'required materials']
    return any(sig in text for sig in signals)


def fetch_syllabus_with_requests(url: str) -> Optional[str]:
    """
    Fetch syllabus using requests library
    Works for static HTML content
    """
    try:
        logger.debug(f"Fetching with requests: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.debug(f"Requests failed for {url}: {e}")
        return None


def fetch_syllabus_with_selenium(url: str) -> Optional[str]:
    """
    Fetch syllabus using Selenium + Chrome (for JavaScript-rendered content)
    Falls back if requests fails
    """
    driver = None
    try:
        logger.debug(f"Fetching with Selenium: {url}")
        
        # Configure Chrome options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Initialize Chrome driver (assumes chromedriver installed)
        driver = webdriver.Chrome(options=options)
        
        driver.get(url)
        
        # Wait for content to load (max 10 seconds)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait a bit for dynamic content
        time.sleep(2)
        
        # Get page source
        html = driver.page_source
        return html if html else None
    
    except Exception as e:
        logger.debug(f"Selenium failed for {url}: {e}")
        return None
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def fetch_and_parse_syllabus(url: str) -> Dict[str, str]:
    """
    Fetch a syllabus from URL and parse it into sections
    
    Args:
        url: Syllabus URL
    
    Returns:
        Dict of {section_type: section_content}
        Returns empty dict if fetch fails
    """
    html_content = None
    
    # Try requests first (faster)
    html_content = fetch_syllabus_with_requests(url)
    
    # Fall back to Selenium if requests failed or returned shell-only HTML.
    if not html_content or not _has_meaningful_syllabus_content(html_content):
        logger.info(f"Attempting Selenium for {url}")
        html_content = fetch_syllabus_with_selenium(url)
    
    if not html_content:
        logger.error(f"Failed to fetch content from {url}")
        return {}
    
    try:
        # Parse HTML into sections
        sections = extract_sections_from_html(html_content)
        logger.info(f"Extracted {len(sections)} sections from {url}")
        return sections
    except Exception as e:
        logger.error(f"Error parsing syllabus from {url}: {e}")
        return {}


def get_section_title_from_type(section_type: str) -> str:
    """Get a nice title for a section type"""
    titles = {
        'objectives': 'Course Objectives & Learning Outcomes',
        'topics': 'Course Content & Schedule',
        'grading': 'Grading & Assessment',
        'prerequisites': 'Prerequisites & Requirements',
        'resources': 'Required Materials & Resources',
        'assessment': 'Assessments & Assignments',
        'policies': 'Course Policies',
        'other': 'Course Information'
    }
    return titles.get(section_type, section_type.title())


def prepare_section_records(
    syllabus_id: str,
    sections_dict: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Convert parsed sections into database records
    
    Args:
        syllabus_id: UUID of the syllabus
        sections_dict: Dict of {section_type: section_content}
    
    Returns:
        List of records ready to insert into syllabus_sections table
    """
    records = []
    
    for order, (section_type, content) in enumerate(sections_dict.items(), start=1):
        record = {
            'syllabus_id': syllabus_id,
            'section_type': section_type if section_type in SECTION_PATTERNS.keys() else 'other',
            'section_title': get_section_title_from_type(section_type),
            'section_content': content[:5000],  # Truncate to 5000 chars (DB limit)
            'order': order
        }
        records.append(record)
    
    return records


if __name__ == '__main__':
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    
    # Test with an example URL
    test_url = "https://ggc.simplesyllabus.com/en-US/doc/1thnk55qi/2026-Fall-ACCT-2101-Section-01-%2881797%29?mode=view"
    
    print(f"Testing syllabus content scraper with: {test_url}\n")
    sections = fetch_and_parse_syllabus(test_url)
    
    print(f"Extracted {len(sections)} sections:\n")
    for section_type, content in sections.items():
        print(f"[{section_type.upper()}]")
        print(f"{content[:200]}...\n")
