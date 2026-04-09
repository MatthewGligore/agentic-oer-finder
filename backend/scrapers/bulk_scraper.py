"""
Orchestrator for bulk scraping of SimpleSyllabus library
Discovers all syllabuses, scrapes individual content, and stores in Supabase
"""
import logging
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm

from backend.scrapers.library_index_scraper import fetch_library_index
from backend.scrapers.syllabus_content_scraper import (
    fetch_and_parse_syllabus,
    prepare_section_records
)
from backend.llm.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bulk_scraper.log')
    ]
)


class BulkScraper:
    """Orchestrate bulk scraping and storage of syllabuses"""
    
    def __init__(self):
        self.supabase_client = get_supabase_client()
        self.stats = {
            'total_discovered': 0,
            'successfully_scraped': 0,
            'failed_scrapes': 0,
            'already_exists': 0,
            'total_sections_stored': 0
        }
    
    def run(
        self,
        limit: Optional[int] = None,
        skip_existing: bool = True,
        batch_size: int = 100
    ):
        """
        Run the bulk scraping pipeline
        
        Args:
            limit: Maximum number of syllabuses to scrape (None for all)
            skip_existing: Skip syllabuses already in database
            batch_size: Number of records to batch insert at once
        """
        logger.info("Starting bulk syllabus scraper")
        
        try:
            # Step 1: Fetch library index
            logger.info("Step 1: Discovering syllabuses from library index...")
            syllabuses_to_scrape = self._fetch_library_index(limit)
            
            if not syllabuses_to_scrape:
                logger.error("No syllabuses found in library index")
                return
            
            logger.info(f"Found {len(syllabuses_to_scrape)} syllabuses to process")
            self.stats['total_discovered'] = len(syllabuses_to_scrape)
            
            # Step 2: Filter existing (if enabled)
            if skip_existing:
                logger.info("Step 2: Filtering out existing syllabuses...")
                syllabuses_to_scrape = self._filter_existing(syllabuses_to_scrape)
                logger.info(f"After filtering: {len(syllabuses_to_scrape)} new syllabuses to scrape")
            
            if not syllabuses_to_scrape:
                logger.info("No new syllabuses to scrape")
                self._print_stats()
                return
            
            # Step 3: Scrape content and prepare database records
            logger.info("Step 3: Scraping syllabus content...")
            syllabuses_records, sections_records = self._scrape_and_prepare(syllabuses_to_scrape)
            
            # Step 4: Batch insert into Supabase
            logger.info("Step 4: Inserting records into Supabase...")
            self._batch_insert(syllabuses_records, sections_records, batch_size)
            
            logger.info("✅ Bulk scraping completed successfully")
            self._print_stats()
        
        except Exception as e:
            logger.error(f"Bulk scraper failed: {e}", exc_info=True)
            self._print_stats()
            raise
    
    def _fetch_library_index(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Fetch library index"""
        try:
            syllabuses = fetch_library_index()
            
            if limit:
                syllabuses = syllabuses[:limit]
            
            return syllabuses
        except Exception as e:
            logger.error(f"Error fetching library index: {e}")
            return []
    
    def _filter_existing(self, syllabuses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out syllabuses that already exist in database"""
        if not self.supabase_client.is_available():
            logger.warning("Supabase not available; cannot filter existing syllabuses")
            return syllabuses
        
        filtered = []
        for s in syllabuses:
            if not self.supabase_client.syllabus_exists(s['syllabus_url']):
                filtered.append(s)
            else:
                self.stats['already_exists'] += 1
        
        return filtered
    
    def _scrape_and_prepare(
        self,
        syllabuses: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrape content for each syllabus and prepare database records
        
        Returns:
            (syllabuses_records, sections_records)
        """
        syllabuses_records = []
        sections_records = []
        
        with tqdm(total=len(syllabuses), desc="Scraping syllabuses") as pbar:
            for syllabus_meta in syllabuses:
                try:
                    url = syllabus_meta.get('syllabus_url')
                    
                    # Fetch and parse syllabus content
                    sections = fetch_and_parse_syllabus(url)
                    
                    if not sections:
                        logger.warning(f"No content extracted from {url}")
                        self.stats['failed_scrapes'] += 1
                        pbar.update(1)
                        continue
                    
                    # Prepare syllabus record
                    syllabus_record = {
                        'course_code': syllabus_meta.get('course_code', 'UNKNOWN'),
                        'course_title': syllabus_meta.get('course_title'),
                        'term': syllabus_meta.get('term'),
                        'section_number': syllabus_meta.get('section_number'),
                        'course_id': syllabus_meta.get('course_id'),
                        'instructor_name': syllabus_meta.get('instructor_name'),
                        'syllabus_url': url,
                        'scraped_at': datetime.utcnow().isoformat()
                    }
                    
                    syllabuses_records.append(syllabus_record)
                    
                    # Note: We'll save the ID after insert and use it for sections
                    # For now, we'll insert syllabuses first, then fetch IDs for sections
                    
                    self.stats['successfully_scraped'] += 1
                    pbar.update(1)
                
                except Exception as e:
                    logger.error(f"Error scraping {syllabus_meta.get('syllabus_url')}: {e}")
                    self.stats['failed_scrapes'] += 1
                    pbar.update(1)
                    continue
        
        # Insert syllabuses and get IDs
        logger.info("Inserting syllabuses and retrieving IDs for sections...")
        syllabus_id_map = {}  # Map URL -> ID
        
        if self.supabase_client.is_available():
            for i, syllabus in enumerate(syllabuses_records):
                try:
                    inserted = self.supabase_client.insert_syllabus(syllabus)
                    if inserted:
                        syllabus_id_map[syllabus['syllabus_url']] = inserted['id']
                except Exception as e:
                    logger.error(f"Error inserting syllabus: {e}")
        
        # Prepare sections records with correct syllabus IDs
        with tqdm(total=len(syllabuses), desc="Preparing sections") as pbar:
            for syllabus_meta in syllabuses:
                try:
                    url = syllabus_meta.get('syllabus_url')
                    
                    # Skip if syllabus wasn't inserted
                    if url not in syllabus_id_map:
                        pbar.update(1)
                        continue
                    
                    syllabus_id = syllabus_id_map[url]
                    
                    # Fetch sections again (or cache them)
                    sections = fetch_and_parse_syllabus(url)
                    
                    if sections:
                        section_records = prepare_section_records(syllabus_id, sections)
                        sections_records.extend(section_records)
                        self.stats['total_sections_stored'] += len(section_records)
                    
                    pbar.update(1)
                
                except Exception as e:
                    logger.error(f"Error preparing sections for {url}: {e}")
                    pbar.update(1)
        
        return syllabuses_records, sections_records
    
    def _batch_insert(
        self,
        syllabuses_records: List[Dict[str, Any]],
        sections_records: List[Dict[str, Any]],
        batch_size: int
    ):
        """Insert records into Supabase in batches"""
        if not self.supabase_client.is_available():
            logger.error("Supabase client not available; cannot insert records")
            return
        
        # Insert sections in batches
        logger.info(f"Inserting {len(sections_records)} section records in batches of {batch_size}...")
        
        for i in range(0, len(sections_records), batch_size):
            batch = sections_records[i:i + batch_size]
            try:
                count = self.supabase_client.insert_sections_batch(batch)
                logger.info(f"Inserted batch {i // batch_size + 1}: {count} section records")
            except Exception as e:
                logger.error(f"Error inserting batch: {e}")
    
    def _print_stats(self):
        """Print final statistics"""
        print("\n" + "=" * 60)
        print("BULK SCRAPER STATISTICS")
        print("=" * 60)
        print(f"Total syllabuses discovered: {self.stats['total_discovered']}")
        print(f"Successfully scraped:        {self.stats['successfully_scraped']}")
        print(f"Failed scrapes:              {self.stats['failed_scrapes']}")
        print(f"Already in database:         {self.stats['already_exists']}")
        print(f"Total sections stored:       {self.stats['total_sections_stored']}")
        print("=" * 60 + "\n")


def main():
    """Entry point for bulk scraper CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk scrape SimpleSyllabus library")
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of syllabuses to scrape (default: all)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        default=True,
        help='Skip syllabuses already in database (default: True)'
    )
    parser.add_argument(
        '--no-skip',
        dest='skip_existing',
        action='store_false',
        help='Do NOT skip existing syllabuses (re-scrape all)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for database inserts (default: 100)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting bulk scraper with args: {args}")
    
    scraper = BulkScraper()
    scraper.run(
        limit=args.limit,
        skip_existing=args.skip_existing,
        batch_size=args.batch_size
    )


if __name__ == '__main__':
    main()
