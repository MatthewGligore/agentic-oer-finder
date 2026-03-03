"""
Usage logging system for Agentic OER Finder
Tracks queries, timestamps, and results for review by teams, instructors, and Working Group
"""
import os
import json
import csv
from datetime import datetime
from pathlib import Path
import logging

class UsageLogger:
    """Logs all tool usage: queries, timestamps, and results"""
    
    def __init__(self, log_dir='logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # CSV log file for structured data
        self.csv_log_path = self.log_dir / 'usage_log.csv'
        self._init_csv_log()
        
        # JSON log file for detailed results
        self.json_log_path = self.log_dir / 'usage_log.json'
        
        # Setup Python logger
        self.logger = logging.getLogger('oer_agent')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_dir / 'agent.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _init_csv_log(self):
        """Initialize CSV log file with headers if it doesn't exist"""
        if not self.csv_log_path.exists():
            with open(self.csv_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'course_code',
                    'query_type',
                    'num_results',
                    'processing_time_seconds',
                    'status'
                ])
    
    def log_query(self, course_code, query_type, results, processing_time=None, status='success'):
        """
        Log a query and its results
        
        Args:
            course_code: Course code (e.g., 'ENGL 1101')
            query_type: Type of query ('syllabus_search', 'oer_search', 'evaluation')
            results: List of results returned
            processing_time: Time taken in seconds
            status: 'success' or 'error'
        """
        timestamp = datetime.now().isoformat()
        
        # Log to CSV
        with open(self.csv_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                course_code,
                query_type,
                len(results) if isinstance(results, list) else 0,
                processing_time or 0,
                status
            ])
        
        # Log to JSON for detailed results
        log_entry = {
            'timestamp': timestamp,
            'course_code': course_code,
            'query_type': query_type,
            'results': results,
            'processing_time_seconds': processing_time,
            'status': status
        }
        
        # Append to JSON log file
        log_entries = []
        if self.json_log_path.exists():
            with open(self.json_log_path, 'r', encoding='utf-8') as f:
                try:
                    log_entries = json.load(f)
                except json.JSONDecodeError:
                    log_entries = []
        
        log_entries.append(log_entry)
        
        with open(self.json_log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, indent=2, ensure_ascii=False)
        
        # Log to Python logger
        self.logger.info(f"Query logged: {course_code} - {query_type} - {len(results) if isinstance(results, list) else 0} results")
    
    def get_usage_stats(self):
        """Get usage statistics from logs"""
        if not self.csv_log_path.exists():
            return {}
        
        stats = {
            'total_queries': 0,
            'by_course': {},
            'by_query_type': {},
            'average_processing_time': 0
        }
        
        total_time = 0
        with open(self.csv_log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats['total_queries'] += 1
                
                course = row['course_code']
                stats['by_course'][course] = stats['by_course'].get(course, 0) + 1
                
                qtype = row['query_type']
                stats['by_query_type'][qtype] = stats['by_query_type'].get(qtype, 0) + 1
                
                try:
                    total_time += float(row['processing_time_seconds'])
                except (ValueError, KeyError):
                    pass
        
        if stats['total_queries'] > 0:
            stats['average_processing_time'] = total_time / stats['total_queries']
        
        return stats
