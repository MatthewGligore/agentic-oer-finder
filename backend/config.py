"""
Configuration management for Agentic OER Finder
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # LLM Configuration
    # Note: System works without API keys (uses fallback mode)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    # If no API keys provided, system uses no-API mode automatically
    DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'no_api').strip().lower()
    env_model = os.getenv('DEFAULT_MODEL', 'gpt-4o')
    if env_model in ['gpt-4-turbo-preview', 'gpt-4-turbo']:
        DEFAULT_MODEL = 'gpt-4o'
    else:
        DEFAULT_MODEL = env_model
    
    # Data Sources
    SYLLABUS_BASE_URL = 'https://ggc.simplesyllabus.com'
    ALG_BASE_URL = 'https://alg.manifoldapp.org'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # Application
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 8000))
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
    
    # Required Courses for Testing
    REQUIRED_COURSES = [
        'ENGL 1101',
        'ITEC 1001',
        'ITEC 2150',
        'ENGL 1102',
        'ITEC 3150'
    ]
    
    # OER Quality Rubric Criteria
    RUBRIC_CRITERIA = [
        'Open License',
        'Content Quality',
        'Accessibility',
        'Relevance to Course',
        'Currency/Up-to-date',
        'Pedagogical Value',
        'Technical Quality'
    ]
