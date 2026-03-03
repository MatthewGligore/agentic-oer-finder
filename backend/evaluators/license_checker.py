"""
Open License Checker
Verifies whether resources have open educational licenses
"""
import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class LicenseChecker:
    """Checks for open educational licenses"""
    
    # Common open licenses
    OPEN_LICENSES = [
        r'cc\s*by[-\s]?(\d+\.?\d*)?',  # Creative Commons Attribution
        r'cc\s*by[-\s]?sa',  # CC BY-SA
        r'cc\s*by[-\s]?nc',  # CC BY-NC
        r'cc\s*by[-\s]?nd',  # CC BY-ND
        r'cc\s*by[-\s]?nc[-\s]?sa',  # CC BY-NC-SA
        r'cc\s*by[-\s]?nc[-\s]?nd',  # CC BY-NC-ND
        r'creative\s+commons',
        r'public\s+domain',
        r'open\s+access',
        r'mit\s+license',
        r'apache\s+license',
        r'gpl',
        r'bsd\s+license',
        r'cc0',  # CC0 Public Domain Dedication
    ]
    
    # Restrictive licenses
    RESTRICTIVE_LICENSES = [
        r'copyright',
        r'all\s+rights\s+reserved',
        r'proprietary',
    ]
    
    def check_license(self, resource: Dict) -> Dict:
        """
        Check if resource has an open educational license
        
        Args:
            resource: Resource information
        
        Returns:
            Dictionary with license status and details
        """
        license_text = resource.get('license', '')
        description = resource.get('description', '')
        url = resource.get('url', '')
        
        # Combine all text to search
        search_text = f"{license_text} {description}".lower()
        
        result = {
            'has_open_license': False,
            'license_type': 'Unknown',
            'confidence': 'low',
            'evidence': '',
            'details': ''
        }
        
        # Check for open licenses
        for license_pattern in self.OPEN_LICENSES:
            match = re.search(license_pattern, search_text, re.IGNORECASE)
            if match:
                result['has_open_license'] = True
                result['license_type'] = match.group(0)
                result['confidence'] = 'high' if license_text else 'medium'
                result['evidence'] = f"Found open license indicator: {match.group(0)}"
                result['details'] = license_text or description[:200]
                return result
        
        # Check for restrictive licenses
        for restrictive_pattern in self.RESTRICTIVE_LICENSES:
            match = re.search(restrictive_pattern, search_text, re.IGNORECASE)
            if match:
                result['has_open_license'] = False
                result['license_type'] = 'Restrictive'
                result['confidence'] = 'medium'
                result['evidence'] = f"Found restrictive license indicator: {match.group(0)}"
                result['details'] = license_text or description[:200]
                return result
        
        # If no clear license found
        if license_text:
            result['license_type'] = license_text
            result['confidence'] = 'medium'
            result['evidence'] = "License information present but not clearly identifiable as open"
        else:
            result['confidence'] = 'low'
            result['evidence'] = "No license information found. Manual verification required."
        
        return result
    
    def check_multiple(self, resources: List[Dict]) -> List[Dict]:
        """
        Check licenses for multiple resources
        
        Args:
            resources: List of resource dictionaries
        
        Returns:
            List of license check results
        """
        return [self.check_license(resource) for resource in resources]
