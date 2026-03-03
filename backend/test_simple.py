"""
Simple Test Script for Students
Tests Agentic OER Finder with a basic course search
"""
import sys
import os

# Add parent directory to path to allow imports from backend package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header():
    """Print test header"""
    print("=" * 60)
    print("Agentic OER Finder - Simple Test")
    print("=" * 60)
    print()

def check_setup():
    """Check if everything is set up correctly"""
    print("Step 1: Checking setup...")
    issues = []
    
    # Check Python version
    try:
        version = sys.version_info
        print(f"  [OK] Python {version.major}.{version.minor}.{version.micro}")
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            issues.append("Python 3.8+ required")
    except:
        issues.append("Could not check Python version")
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("  [OK] .env file found")
    else:
        issues.append(".env file not found - create it (optional for this demo)")
        print("  [--] .env file not found")
    
    # Check if required modules can be imported
    try:
        from config import Config
        print("  [OK] Configuration module loaded")
    except ImportError as e:
        issues.append(f"Config import failed: {e}")
        print(f"  [FAIL] Config import failed: {e}")
    
    try:
        import flask
        print("  [OK] Flask installed")
    except ImportError:
        issues.append("Flask not installed - run: pip install -r requirements.txt")
        print("  [FAIL] Flask not installed")
    
    try:
        import requests
        print("  [OK] Requests installed")
    except ImportError:
        issues.append("Requests not installed - run: pip install -r requirements.txt")
        print("  [FAIL] Requests not installed")
    
    try:
        import openai
        print("  [OK] OpenAI library installed")
    except ImportError:
        issues.append("OpenAI not installed - run: pip install -r requirements.txt")
        print("  [FAIL] OpenAI not installed")
    
    print()
    
    if issues:
        print("Setup issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("Please fix these issues before continuing.")
        return False
    
    print("[OK] All setup checks passed.")
    print()
    return True

def test_agent():
    """Test the OER agent"""
    print("Step 2: Testing OER Agent...")
    print()
    
    try:
        from backend.oer_agent import OERAgent
        from backend.config import Config
        
        print("  [OK] Importing OER Agent...")
        
        config = Config()
        if not config.OPENAI_API_KEY:
            print("  [OK] No API key - using built-in suggestions (no API needed)")
        else:
            print("  [OK] API key found")
        
        print("  [OK] Initializing agent...")
        agent = OERAgent()
        print("  [OK] Agent initialized.")
        print()
        
        # Test with a simple course
        test_course = "ITEC 1001"
        print(f"Step 3: Testing search for '{test_course}'...")
        print("  (This may take 10-30 seconds...)")
        print()
        
        results = agent.find_oer_for_course(test_course)
        
        # Display results
        print("=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print()
        print(f"Course: {results.get('course_code', 'N/A')}")
        print(f"Resources Found: {results.get('resources_found', 0)}")
        print(f"Resources Evaluated: {results.get('resources_evaluated', 0)}")
        print(f"Processing Time: {results.get('processing_time_seconds', 0):.2f} seconds")
        print()
        
        evaluated = results.get('evaluated_resources', [])
        if evaluated:
            print(f"Found {len(evaluated)} OER resources:")
            print()
            for i, resource in enumerate(evaluated[:3], 1):  # Show first 3
                res = resource.get('resource', {})
                title = res.get('title', 'Unknown')
                score = resource.get('rubric_evaluation', {}).get('overall_score', 0)
                source = res.get('source', 'Unknown')
                print(f"  {i}. {title}")
                print(f"     Source: {source}")
                print(f"     Quality Score: {score:.1f}/5.0")
                print()
            
            if len(evaluated) > 3:
                print(f"  ... and {len(evaluated) - 3} more resources")
                print()
        else:
            print("  No resources found. Default suggestions may still appear.")
            print()
        
        print("=" * 60)
        print("TEST COMPLETED.")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Try running: python app.py (to start web interface)")
        print("  2. Try different courses: python test_courses.py")
        print("  3. Explore the code in oer_agent.py")
        print()
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Install packages: pip install -r requirements.txt")
        print("  2. Ensure .env exists (optional for this demo)")
        print("  3. Check the error message above")
        print()
        import traceback
        print("Detailed error:")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print_header()
    
    if not check_setup():
        print()
        print("Please fix the setup issues above and try again.")
        sys.exit(1)
    
    success = test_agent()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
