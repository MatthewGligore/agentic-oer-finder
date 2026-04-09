"""
Command Line Interface for Agentic OER Finder
"""
import argparse
import json
import sys
from .oer_agent import OERAgent
from .config import Config

def search_command(args):
    """Handle search command"""
    # Initialize agent
    agent = OERAgent(llm_provider=args.llm_provider, llm_model=args.llm_model)
    
    print(f"Searching for OER resources for {args.course}...")
    if args.term:
        print(f"Term: {args.term}")
    print()
    
    # Search for OER
    results = agent.find_oer_for_course(args.course, args.term)
    
    # Check for errors
    if 'error' in results:
        print(f"Error: {results['error']}", file=sys.stderr)
        sys.exit(1)
    
    # Display results
    print("=" * 80)
    print(f"OER Search Results for {results['course_code']}")
    print("=" * 80)
    print()
    
    print(f"Resources Found: {results.get('resources_found', 0)}")
    print(f"Resources Evaluated: {results.get('resources_evaluated', 0)}")
    print(f"Processing Time: {results.get('processing_time_seconds', 0):.2f} seconds")
    print()
    
    if results.get('summary'):
        print("Summary:")
        print(results['summary'])
        print()
    
    # Display evaluated resources
    evaluated_resources = results.get('evaluated_resources', [])
    if evaluated_resources:
        print(f"\nTop {len(evaluated_resources)} OER Resources:")
        print("-" * 80)
        
        for i, item in enumerate(evaluated_resources, 1):
            resource = item.get('resource', {})
            rubric_eval = item.get('rubric_evaluation', {})
            license_check = item.get('license_check', {})
            overall_score = rubric_eval.get('overall_score', 0)
            
            print(f"\n{i}. {resource.get('title', 'Untitled')}")
            print(f"   URL: {resource.get('url', 'N/A')}")
            print(f"   Quality Score: {overall_score:.1f}/5.0")
            
            if license_check.get('has_open_license'):
                print(f"   License: ✓ Open ({license_check.get('license_type', 'Unknown')})")
            else:
                print(f"   License: ⚠ {license_check.get('license_type', 'Unknown')}")
            
            if resource.get('description'):
                desc = resource.get('description', '')[:200]
                print(f"   Description: {desc}...")
            
            if item.get('integration_guidance'):
                print(f"   Integration: {item.get('integration_guidance', '').split(chr(10))[0]}")
    else:
        print("No OER resources found for this course.")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")
    
    print("\n" + "=" * 80)


def scrape_syllabuses_command(args):
    """Handle scrape-syllabuses command"""
    from .scrapers.bulk_scraper import BulkScraper
    
    print("Starting bulk syllabus scraper...")
    print(f"Limit: {args.limit if args.limit else 'All syllabuses'}")
    print(f"Skip existing: {args.skip_existing}")
    print()
    
    try:
        scraper = BulkScraper()
        scraper.run(
            limit=args.limit,
            skip_existing=args.skip_existing,
            batch_size=args.batch_size
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Agentic OER Finder - Find Open Educational Resources'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for OER resources')
    search_parser.add_argument('--course', '-c', type=str, required=True,
                              help='Course code (e.g., ENGL 1101)')
    search_parser.add_argument('--term', '-t', type=str, default=None,
                              help='Term (e.g., Fall 2025)')
    search_parser.add_argument('--output', '-o', type=str, default=None,
                              help='Output file path (JSON format)')
    search_parser.add_argument('--llm-provider', type=str, default=None,
                              help='LLM provider (openai, anthropic)')
    search_parser.add_argument('--llm-model', type=str, default=None,
                              help='LLM model name')
    search_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Verbose output')
    search_parser.set_defaults(func=search_command)
    
    # Scrape syllabuses command
    scrape_parser = subparsers.add_parser('scrape-syllabuses', help='Bulk scrape SimpleSyllabus library')
    scrape_parser.add_argument('--limit', type=int, default=None,
                              help='Maximum number of syllabuses to scrape (default: all)')
    scrape_parser.add_argument('--skip-existing', dest='skip_existing', action='store_true',
                              default=True, help='Skip syllabuses already in database (default: True)')
    scrape_parser.add_argument('--no-skip', dest='skip_existing', action='store_false',
                              help='Do NOT skip existing syllabuses (re-scrape all)')
    scrape_parser.add_argument('--batch-size', type=int, default=100,
                              help='Batch size for database inserts (default: 100)')
    scrape_parser.set_defaults(func=scrape_syllabuses_command)
    
    args = parser.parse_args()
    
    # If no command specified, show help
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Execute the appropriate command function
    args.func(args)

if __name__ == '__main__':
    main()
