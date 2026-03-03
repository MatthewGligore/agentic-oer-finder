"""
Command Line Interface for Agentic OER Finder
"""
import argparse
import json
import sys
from oer_agent import OERAgent
from config import Config

def main():
    parser = argparse.ArgumentParser(description='Agentic OER Finder - Find Open Educational Resources')
    parser.add_argument('--course', '-c', type=str, required=True,
                       help='Course code (e.g., ENGL 1101)')
    parser.add_argument('--term', '-t', type=str, default=None,
                       help='Term (e.g., Fall 2025)')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Output file path (JSON format)')
    parser.add_argument('--llm-provider', type=str, default=None,
                       help='LLM provider (openai, anthropic)')
    parser.add_argument('--llm-model', type=str, default=None,
                       help='LLM model name')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
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

if __name__ == '__main__':
    main()
