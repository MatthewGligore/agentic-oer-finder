"""
Test script for required courses
Tests Agentic OER Finder with all minimum required courses
"""
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow imports from backend package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.oer_agent import OERAgent
from backend.config import Config

def test_required_courses():
    """Test OER agent with all required courses"""
    config = Config()
    agent = OERAgent()
    
    results_dir = Path('test_results')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = results_dir / f'test_summary_{timestamp}.json'
    
    print("=" * 80)
    print("Agentic OER Finder - Required Courses Test")
    print("=" * 80)
    print()
    print(f"Testing {len(config.REQUIRED_COURSES)} required courses...")
    print()
    
    all_results = {
        'timestamp': timestamp,
        'courses_tested': [],
        'summary': {
            'total_courses': len(config.REQUIRED_COURSES),
            'successful': 0,
            'failed': 0,
            'total_resources_found': 0,
            'total_resources_evaluated': 0
        }
    }
    
    for i, course_code in enumerate(config.REQUIRED_COURSES, 1):
        print(f"[{i}/{len(config.REQUIRED_COURSES)}] Testing {course_code}...")
        
        start_time = time.time()
        try:
            results = agent.find_oer_for_course(course_code)
            elapsed = time.time() - start_time
            
            if 'error' in results:
                print(f"  ❌ Error: {results['error']}")
                all_results['summary']['failed'] += 1
                all_results['courses_tested'].append({
                    'course_code': course_code,
                    'status': 'error',
                    'error': results['error'],
                    'elapsed_time': elapsed
                })
            else:
                resources_found = results.get('resources_found', 0)
                resources_evaluated = results.get('resources_evaluated', 0)
                
                print(f"  ✓ Found {resources_found} resources, evaluated {resources_evaluated}")
                print(f"  Time: {elapsed:.2f}s")
                
                all_results['summary']['successful'] += 1
                all_results['summary']['total_resources_found'] += resources_found
                all_results['summary']['total_resources_evaluated'] += resources_evaluated
                
                # Save individual course results
                course_file = results_dir / f'{course_code.replace(" ", "_")}_{timestamp}.json'
                with open(course_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                all_results['courses_tested'].append({
                    'course_code': course_code,
                    'status': 'success',
                    'resources_found': resources_found,
                    'resources_evaluated': resources_evaluated,
                    'elapsed_time': elapsed,
                    'results_file': str(course_file)
                })
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Exception: {str(e)}")
            all_results['summary']['failed'] += 1
            all_results['courses_tested'].append({
                'course_code': course_code,
                'status': 'exception',
                'error': str(e),
                'elapsed_time': elapsed
            })
        
        print()
    
    # Save summary
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total Courses: {all_results['summary']['total_courses']}")
    print(f"Successful: {all_results['summary']['successful']}")
    print(f"Failed: {all_results['summary']['failed']}")
    print(f"Total Resources Found: {all_results['summary']['total_resources_found']}")
    print(f"Total Resources Evaluated: {all_results['summary']['total_resources_evaluated']}")
    print()
    print(f"Summary saved to: {summary_file}")
    print("=" * 80)
    
    return all_results

if __name__ == '__main__':
    test_required_courses()
