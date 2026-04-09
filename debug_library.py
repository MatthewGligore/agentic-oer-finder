#!/usr/bin/env python
"""Debug script to inspect SimpleSyllabus library page structure"""
import requests
from bs4 import BeautifulSoup

url = "https://ggc.simplesyllabus.com/en-US/syllabus-library"
print(f"Fetching: {url}\n")

response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

# Show page title
print(f"Page title: {soup.title.string if soup.title else 'N/A'}\n")

# Count all links
all_links = soup.find_all('a')
print(f"Total links on page: {len(all_links)}")

# Show first 15 links
print(f"\nFirst 15 links:")
for i, link in enumerate(all_links[:15], 1):
    href = link.get('href', 'N/A')
    text = link.get_text(strip=True)[:50]
    print(f"  {i}. href={href}")
    if text:
        print(f"     text={text}")

# Check for /en-US/doc/ pattern
doc_links = [a for a in all_links if a.get('href', '').startswith('/en-US/doc')]
print(f"\n/en-US/doc/ links found: {len(doc_links)}")

# Look for data attributes
print(f"\nScript tags: {len(soup.find_all('script'))}")

# Check page HTML size
print(f"Page size: {len(response.content)} bytes")

# Look for any element with 'syllabus' in it
syllabus_elements = soup.find_all(string=lambda x: x and 'syllabus' in x.lower())
print(f"\nElements containing 'syllabus': {len(syllabus_elements)}")
if syllabus_elements:
    for elem in syllabus_elements[:5]:
        print(f"  - {elem[:80]}")
