"""
Selenium-based scraper for GGC Simple Syllabus
Use this if the basic scraper doesn't work - requires Selenium and ChromeDriver
"""
from typing import Dict, List, Optional
import logging
import time

logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available. Install with: pip install selenium webdriver-manager")

class SyllabusScraperSelenium:
    """Selenium-based scraper for JavaScript-rendered Simple Syllabus"""
    
    def __init__(self, base_url='https://ggc.simplesyllabus.com', headless=True):
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required. Install with: pip install selenium webdriver-manager")
        
        self.base_url = base_url
        self.headless = headless
        self.driver = None
    
    def _get_driver(self):
        """Get or create Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def search_course(self, course_code: str, term: str = None) -> List[Dict]:
        """
        Search for syllabi using Selenium (handles JavaScript)
        
        Args:
            course_code: Course code (e.g., 'ENGL 1101')
            term: Term to search (e.g., 'Fall 2025')
        
        Returns:
            List of syllabus information dictionaries
        """
        try:
            driver = self._get_driver()
            driver.get(self.base_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Find search input (based on the HTML you provided)
            try:
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[matinput][type='text'][placeholder*='Looking']"))
                )
                
                # Enter course code
                search_input.clear()
                search_input.send_keys(course_code)
                time.sleep(2)  # Wait for search results
                
                # Extract results
                syllabi = self._extract_results(driver, course_code)
                return syllabi
                
            except Exception as e:
                logger.error(f"Error interacting with search: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error in Selenium scraper: {e}")
            return []
    
    def _extract_results(self, driver, course_code: str) -> List[Dict]:
        """Extract syllabus results from the page"""
        syllabi = []
        
        try:
            # Look for result cards/items
            # Adjust selectors based on actual page structure
            result_elements = driver.find_elements(By.CSS_SELECTOR, "mat-card, .course-card, .syllabus-item, [class*='course']")
            
            for element in result_elements:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, "h1, h2, h3, h4, .title, mat-card-title")
                    title = title_elem.text.strip()
                    
                    if course_code.upper() in title.upper():
                        link_elem = element.find_element(By.CSS_SELECTOR, "a")
                        url = link_elem.get_attribute('href') if link_elem else self.base_url
                        
                        desc_elem = element.find_element(By.CSS_SELECTOR, "p, .description, mat-card-content")
                        description = desc_elem.text.strip()[:300] if desc_elem else ''
                        
                        syllabi.append({
                            'course_code': course_code,
                            'title': title,
                            'url': url,
                            'description': description,
                            'instructor': '',
                            'source': 'GGC Simple Syllabus (Selenium)'
                        })
                except:
                    continue
        except Exception as e:
            logger.debug(f"Error extracting results: {e}")
        
        return syllabi
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup"""
        self.close()
