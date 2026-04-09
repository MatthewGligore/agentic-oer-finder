"""
Supabase client for syllabus database operations
"""
import logging
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from backend.config import Config

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper around Supabase client for syllabus operations"""
    
    def __init__(self):
        """Initialize Supabase client with credentials from config"""
        if not Config.USE_SUPABASE:
            logger.warning("Supabase credentials not configured. Database operations will be unavailable.")
            self.client: Optional[Client] = None
            return
        
        try:
            self.client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None
    
    # ===== SYLLABUSES TABLE OPERATIONS =====
    
    def fetch_syllabuses_by_course_code(
        self,
        course_code: str,
        term: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch syllabuses by course code (and optionally by term)
        
        Args:
            course_code: Course code (e.g., "ACCT 2101")
            term: Optional term filter (e.g., "2026-Fall")
        
        Returns:
            List of syllabus records
        """
        if not self.is_available():
            logger.debug("Supabase not available, returning empty list")
            return []
        
        try:
            query = self.client.table('syllabuses').select('*').eq('course_code', course_code)
            
            if term:
                query = query.eq('term', term)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching syllabuses for {course_code}: {e}")
            return []
    
    def fetch_syllabuses_by_term(self, term: str) -> List[Dict[str, Any]]:
        """
        Fetch all syllabuses for a given term
        
        Args:
            term: Term (e.g., "2026-Fall")
        
        Returns:
            List of syllabus records
        """
        if not self.is_available():
            return []
        
        try:
            response = self.client.table('syllabuses').select('*').eq('term', term).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching syllabuses for term {term}: {e}")
            return []
    
    def fetch_syllabus_by_id(self, syllabus_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single syllabus by ID
        
        Args:
            syllabus_id: UUID of syllabus
        
        Returns:
            Syllabus record or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('syllabuses').select('*').eq('id', syllabus_id).single().execute()
            return response.data
        except Exception as e:
            logger.debug(f"Syllabus {syllabus_id} not found: {e}")
            return None
    
    def fetch_syllabus_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single syllabus by URL
        
        Args:
            url: Syllabus URL
        
        Returns:
            Syllabus record or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('syllabuses').select('*').eq('syllabus_url', url).single().execute()
            return response.data
        except Exception as e:
            logger.debug(f"Syllabus with URL {url} not found: {e}")
            return None
    
    def insert_syllabus(self, syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert a single syllabus record
        
        Args:
            syllabus_data: Dictionary with syllabus fields
        
        Returns:
            Inserted record or None on failure
        """
        if not self.is_available():
            logger.error("Supabase not available for insert")
            return None
        
        try:
            response = self.client.table('syllabuses').insert(syllabus_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error inserting syllabus: {e}")
            return None
    
    def insert_syllabuses_batch(self, syllabuses_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple syllabus records in batch
        
        Args:
            syllabuses_data: List of syllabus dictionaries
        
        Returns:
            Number of successfully inserted records
        """
        if not self.is_available():
            logger.error("Supabase not available for batch insert")
            return 0
        
        try:
            response = self.client.table('syllabuses').insert(syllabuses_data).execute()
            count = len(response.data) if response.data else 0
            logger.info(f"Inserted {count} syllabuses")
            return count
        except Exception as e:
            logger.error(f"Error batch inserting syllabuses: {e}")
            return 0
    
    def update_syllabus(self, syllabus_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a syllabus record
        
        Args:
            syllabus_id: UUID of syllabus to update
            update_data: Dictionary with fields to update
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            response = self.client.table('syllabuses').update(update_data).eq('id', syllabus_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating syllabus {syllabus_id}: {e}")
            return False
    
    # ===== SYLLABUS SECTIONS TABLE OPERATIONS =====
    
    def fetch_sections_by_syllabus_id(
        self,
        syllabus_id: str,
        section_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch sections for a given syllabus
        
        Args:
            syllabus_id: UUID of syllabus
            section_type: Optional filter by section type (e.g., 'objectives', 'grading')
        
        Returns:
            List of section records ordered by position
        """
        if not self.is_available():
            return []
        
        try:
            query = self.client.table('syllabus_sections').select('*').eq('syllabus_id', syllabus_id)
            
            if section_type:
                query = query.eq('section_type', section_type)
            
            response = query.order('order', desc=False).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching sections for syllabus {syllabus_id}: {e}")
            return []
    
    def fetch_section_content(self, syllabus_id: str, section_type: str) -> Optional[str]:
        """
        Get the content of a specific section
        
        Args:
            syllabus_id: UUID of syllabus
            section_type: Section type (e.g., 'objectives')
        
        Returns:
            Section content string or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('syllabus_sections').select('section_content').eq('syllabus_id', syllabus_id).eq('section_type', section_type).single().execute()
            return response.data.get('section_content') if response.data else None
        except Exception as e:
            logger.debug(f"Section {section_type} not found for syllabus {syllabus_id}: {e}")
            return None
    
    def insert_section(self, section_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert a single section record
        
        Args:
            section_data: Dictionary with section fields
        
        Returns:
            Inserted record or None on failure
        """
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('syllabus_sections').insert(section_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error inserting section: {e}")
            return None
    
    def insert_sections_batch(self, sections_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple section records in batch
        
        Args:
            sections_data: List of section dictionaries
        
        Returns:
            Number of successfully inserted records
        """
        if not self.is_available():
            return 0
        
        try:
            response = self.client.table('syllabus_sections').insert(sections_data).execute()
            count = len(response.data) if response.data else 0
            logger.info(f"Inserted {count} syllabus sections")
            return count
        except Exception as e:
            logger.error(f"Error batch inserting sections: {e}")
            return 0
    
    # ===== UTILITY METHODS =====
    
    def syllabus_exists(self, url: str) -> bool:
        """Check if a syllabus with the given URL already exists"""
        return self.fetch_syllabus_by_url(url) is not None
    
    def get_course_count(self) -> int:
        """Get total count of unique courses in database"""
        if not self.is_available():
            return 0
        
        try:
            response = self.client.rpc('count_unique_courses').execute() if hasattr(self.client, 'rpc') else None
            return response.data if response else 0
        except Exception as e:
            logger.debug(f"Error getting course count: {e}")
            return 0
    
    def search_syllabuses_by_text(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Full-text search across syllabus sections
        
        Args:
            search_query: Text to search for
        
        Returns:
            List of matching sylabus records with relevant sections
        """
        if not self.is_available():
            return []
        
        try:
            # Use Postgres full-text search if available
            response = self.client.from_('syllabuses_with_sections').select('*').ilike('section_content', f'%{search_query}%').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error searching syllabuses: {e}")
            return []


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create singleton Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
