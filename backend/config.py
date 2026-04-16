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

    # Search Source Policy
    PRIMARY_OER_SOURCES = [
        'Open ALG Library',
        'MERLOT',
        'OER Commons Hub',
    ]
    FALLBACK_MIN_PRIMARY_RESULTS = int(os.getenv('FALLBACK_MIN_PRIMARY_RESULTS', '10'))

    # Ranking Weights (final_rank_score = relevance * W1 + rubric * W2)
    # relevance score is normalized to 1-5 before weighting.
    RELEVANCE_WEIGHT = float(os.getenv('RELEVANCE_WEIGHT', '0.6'))
    RUBRIC_WEIGHT = float(os.getenv('RUBRIC_WEIGHT', '0.4'))

    # Candidate and evaluation budgets
    MAX_PRIMARY_CANDIDATES = int(os.getenv('MAX_PRIMARY_CANDIDATES', '24'))
    MAX_TOTAL_CANDIDATES = int(os.getenv('MAX_TOTAL_CANDIDATES', '30'))
    MAX_RELEVANCE_EVALUATIONS = int(os.getenv('MAX_RELEVANCE_EVALUATIONS', '12'))
    MAX_EVALUATED_RESOURCES = int(os.getenv('MAX_EVALUATED_RESOURCES', '15'))

    # Syllabus-derived query generation
    MAX_SYLLABUS_QUERY_VARIANTS = int(os.getenv('MAX_SYLLABUS_QUERY_VARIANTS', '5'))
    MAX_QUERY_TERMS_PER_VARIANT = int(os.getenv('MAX_QUERY_TERMS_PER_VARIANT', '10'))
