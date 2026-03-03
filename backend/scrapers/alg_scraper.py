"""
Web scraper for Open ALG Library
Scrapes open educational resources from alg.manifoldapp.org
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ALGScraper:
    """Scraper for Open ALG Library"""
    
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
            # Construct search URL
            search_url = f"{self.base_url}/search"
            
            params = {
                'q': query
            }
            
            if course_code:
                params['course'] = course_code
            
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract resource information
            resources = []
            
            # Look for resource items (structure may vary)
            resource_items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'resource|project|book|item', re.I))
            
            for item in resource_items:
                resource_info = self._extract_resource_info(item, query)
                if resource_info:
                    resources.append(resource_info)
            
            # If no structured results, try alternative selectors
            if not resources:
                # Try finding links that might be resources
                links = soup.find_all('a', href=re.compile(r'/projects/|/resources/|/books/', re.I))
                for link in links[:20]:  # Limit to first 20
                    # Skip generic listing pages
                    href = link.get('href', '')
                    if href and ('/projects/all' in href.lower() or '/all' in href.lower()):
                        continue
                    resource_info = self._extract_from_link(link, query)
                    if resource_info and resource_info.get('title') and resource_info.get('title').lower() != 'projects':
                        resources.append(resource_info)
            
            logger.info(f"Found {len(resources)} resources for query: {query}")
            return resources
            
        except requests.RequestException as e:
            logger.error(f"Error scraping ALG Library for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in ALG scraper: {e}")
            return []
    
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
            response = self.session.get(resource_url, timeout=10)
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
