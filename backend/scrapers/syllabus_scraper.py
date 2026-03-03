"""
Web scraper for GGC Simple Syllabus
Scrapes syllabi information from ggc.simplesyllabus.com

Note: Simple Syllabus is an Angular SPA (Single Page Application), so it requires
JavaScript rendering. This scraper attempts multiple methods.
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import logging
import json
import time

logger = logging.getLogger(__name__)

class SyllabusScraper:
    """Scraper for GGC Simple Syllabus"""
    
    def __init__(self, base_url='https://ggc.simplesyllabus.com'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def search_course(self, course_code: str, term: str = None) -> List[Dict]:
        """
        Search for syllabi by course code
        
        Args:
            course_code: Course code (e.g., 'ENGL 1101')
            term: Term to search (e.g., 'Fall 2025', 'Spring 2026')
        
        Returns:
            List of syllabus information dictionaries
        """
        try:
            # Parse course code
            course_parts = course_code.split()
            if len(course_parts) < 2:
                logger.error(f"Invalid course code format: {course_code}")
                return []
            
            subject = course_parts[0]
            number = course_parts[1]
            
            # Method 1: Try direct search URL (if it exists)
            syllabi = self._try_direct_search(subject, number, term)
            if syllabi:
                return syllabi
            
            # Method 2: Try API endpoint (many Angular apps have APIs)
            syllabi = self._try_api_search(subject, number, term)
            if syllabi:
                return syllabi
            
            # Method 3: Try browsing to main page and extracting course info
            syllabi = self._try_browse_search(course_code, term)
            if syllabi:
                return syllabi
            
            # If all methods fail, return basic info
            logger.warning(f"Could not scrape syllabus for {course_code}. Site may require JavaScript rendering.")
            return [{
                'course_code': course_code,
                'title': f'{course_code} - Course Syllabus',
                'description': f'Syllabus information for {course_code}. Note: Website requires JavaScript rendering.',
                'url': self.base_url,
                'instructor': '',
                'source': 'GGC Simple Syllabus (requires manual access)',
                'note': 'This site uses Angular/JavaScript. Consider using Selenium for full scraping.'
            }]
            
        except Exception as e:
            logger.error(f"Unexpected error in syllabus scraper: {e}")
            return []
    
    def _try_direct_search(self, subject: str, number: str, term: str = None) -> List[Dict]:
        """Try direct URL search"""
        try:
            # Try actual Simple Syllabus URL structure
            # Based on: https://ggc.simplesyllabus.com/en-US/syllabus-library?organization_id=...
            search_patterns = [
                f"{self.base_url}/en-US/syllabus-library?q={subject}+{number}",
                f"{self.base_url}/en-US/syllabus-library?subject={subject}&number={number}",
                f"{self.base_url}/en-US/syllabus-library?search={subject}+{number}",
                f"{self.base_url}/en-US/syllabus-library?course={subject}+{number}",
                f"{self.base_url}/search?q={subject}+{number}",
                f"{self.base_url}/search?subject={subject}&number={number}",
                f"{self.base_url}/courses/{subject}/{number}",
                f"{self.base_url}/syllabus/{subject}/{number}",
            ]
            
            for url in search_patterns:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Look for Angular-rendered content or JSON data
                        syllabi = self._extract_from_angular_page(soup, f"{subject} {number}")
                        if syllabi:
                            return syllabi
                except:
                    continue
        except Exception as e:
            logger.debug(f"Direct search failed: {e}")
        return []
    
    def _try_api_search(self, subject: str, number: str, term: str = None) -> List[Dict]:
        """Try API endpoints (common in Angular apps)"""
        try:
            # Try API endpoints that Angular apps often use
            api_patterns = [
                f"{self.base_url}/api/v1/syllabi?subject={subject}&number={number}",
                f"{self.base_url}/api/v1/search?q={subject}+{number}",
                f"{self.base_url}/api/syllabi?subject={subject}&number={number}",
                f"{self.base_url}/api/search?q={subject}+{number}",
                f"{self.base_url}/api/courses/{subject}/{number}",
                f"{self.base_url}/en-US/api/syllabi?subject={subject}&number={number}",
            ]
            
            for url in api_patterns:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            return self._parse_api_response(data, f"{subject} {number}")
                        except:
                            pass
                except:
                    continue
        except Exception as e:
            logger.debug(f"API search failed: {e}")
        return []
    
    def _try_browse_search(self, course_code: str, term: str = None) -> List[Dict]:
        """Try browsing main page and syllabus library"""
        try:
            # Try the actual syllabus library page
            library_url = f"{self.base_url}/en-US/syllabus-library"
            response = self.session.get(library_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for embedded JSON data (common in Angular apps)
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        syllabi = self._extract_from_json_data(data, course_code)
                        if syllabi:
                            return syllabi
                    except:
                        continue
                
                # Also try to find course links in the page
                course_links = soup.find_all('a', href=re.compile(rf'{course_code.replace(" ", "")}', re.I))
                if course_links:
                    syllabi = []
                    for link in course_links[:5]:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        if course_code.upper() in title.upper():
                            syllabi.append({
                                'course_code': course_code,
                                'title': title,
                                'url': href if href.startswith('http') else f"{self.base_url}{href}",
                                'description': '',
                                'instructor': '',
                                'source': 'GGC Simple Syllabus'
                            })
                    if syllabi:
                        return syllabi
        except Exception as e:
            logger.debug(f"Browse search failed: {e}")
        return []
    
    def _extract_from_angular_page(self, soup: BeautifulSoup, course_code: str) -> List[Dict]:
        """Extract syllabus info from Angular-rendered page"""
        syllabi = []
        
        # Look for common Angular Material patterns
        # Based on the HTML you provided, look for mat-* elements
        course_cards = soup.find_all(['div', 'mat-card'], class_=re.compile(r'course|syllabus|card', re.I))
        
        for card in course_cards:
            # Try to extract course information
            title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'span'], class_=re.compile(r'title|name', re.I))
            if not title_elem:
                title_elem = card.find('mat-card-title') or card.find('h3')
            
            title = title_elem.get_text(strip=True) if title_elem else course_code
            
            # Look for links
            link_elem = card.find('a', href=True)
            link = ''
            if link_elem:
                href = link_elem.get('href', '')
                link = href if href.startswith('http') else f"{self.base_url}{href}"
            
            if title and course_code.upper() in title.upper():
                syllabi.append({
                    'course_code': course_code,
                    'title': title,
                    'url': link or self.base_url,
                    'description': card.get_text(strip=True)[:300],
                    'instructor': '',
                    'source': 'GGC Simple Syllabus'
                })
        
        return syllabi
    
    def _parse_api_response(self, data: dict, course_code: str) -> List[Dict]:
        """Parse API JSON response"""
        syllabi = []
        
        # Handle different API response structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('results', data.get('data', data.get('syllabi', [])))
        
        for item in items:
            if isinstance(item, dict):
                title = item.get('title', item.get('name', course_code))
                if course_code.upper() in title.upper() or course_code.upper() in str(item).upper():
                    syllabi.append({
                        'course_code': course_code,
                        'title': title,
                        'url': item.get('url', self.base_url),
                        'description': item.get('description', ''),
                        'instructor': item.get('instructor', item.get('professor', '')),
                        'source': 'GGC Simple Syllabus'
                    })
        
        return syllabi
    
    def _extract_from_json_data(self, data: dict, course_code: str) -> List[Dict]:
        """Extract from embedded JSON data"""
        return self._parse_api_response(data, course_code)
    
    def _extract_syllabus_info(self, element, course_code: str) -> Optional[Dict]:
        """Extract syllabus information from HTML element"""
        try:
            # Extract title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name', re.I))
            title = title_elem.get_text(strip=True) if title_elem else course_code
            
            # Extract link
            link_elem = element.find('a', href=True) if element.name != 'a' else element
            link = link_elem.get('href', '') if link_elem else ''
            if link and not link.startswith('http'):
                link = f"{self.base_url}{link}"
            
            # Extract description/text
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary', re.I))
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract instructor
            instructor_elem = element.find(['span', 'div'], class_=re.compile(r'instructor|professor', re.I))
            instructor = instructor_elem.get_text(strip=True) if instructor_elem else ''
            
            return {
                'course_code': course_code,
                'title': title,
                'url': link,
                'description': description,
                'instructor': instructor,
                'source': 'GGC Simple Syllabus'
            }
        except Exception as e:
            logger.debug(f"Error extracting syllabus info: {e}")
            return None
    
    def _extract_from_page_content(self, soup: BeautifulSoup, course_code: str) -> Optional[Dict]:
        """Fallback: extract information from page content"""
        try:
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else course_code
            
            # Extract main content
            main_content = soup.find('main') or soup.find('body')
            description = ''
            if main_content:
                paragraphs = main_content.find_all('p', limit=3)
                description = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return {
                'course_code': course_code,
                'title': title_text,
                'url': self.base_url,
                'description': description[:500],  # Limit description length
                'instructor': '',
                'source': 'GGC Simple Syllabus'
            }
        except Exception as e:
            logger.debug(f"Error extracting from page content: {e}")
            return None
    
    def get_syllabus_content(self, syllabus_url: str) -> Optional[str]:
        """Get full content of a specific syllabus"""
        try:
            response = self.session.get(syllabus_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error getting syllabus content from {syllabus_url}: {e}")
            return None
