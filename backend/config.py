"""
Configuration management for Agentic OER Finder
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _parse_csv_env(name: str, default: str) -> list[str]:
    """Parse comma-separated env values into a clean list."""
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]

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
    SYLLABUS_BASE_URL = os.getenv('SYLLABUS_BASE_URL', 'https://ggc.simplesyllabus.com').rstrip('/')
    ALG_BASE_URL = os.getenv('ALG_BASE_URL', 'https://alg.manifoldapp.org').rstrip('/')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # Application
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 8000))
    CORS_ALLOWED_ORIGINS = _parse_csv_env(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000'
    )
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')
    SUPABASE_JWT_KID = os.getenv('SUPABASE_JWT_KID', '')
    SUPABASE_JWKS_URL = os.getenv('SUPABASE_JWKS_URL', '').strip() or (
        f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else ''
    )
    USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
    REQUIRE_AUTH_FOR_SAVES = os.getenv('REQUIRE_AUTH_FOR_SAVES', 'true').lower() == 'true'
    # Anonymous/demo bookmarks before auth (must match schema.sql legacy default)
    LEGACY_SAVED_USER_ID = os.getenv('LEGACY_SAVED_USER_ID', '00000000-0000-4000-8000-000000000001')

    # Term policy (mined from global feedback)
    ENABLE_TERM_POLICY = os.getenv('ENABLE_TERM_POLICY', 'true').lower() == 'true'
    TERM_POLICY_BLEND_WEIGHT = float(os.getenv('TERM_POLICY_BLEND_WEIGHT', '0.5'))
    TERM_POLICY_TOP_K = int(os.getenv('TERM_POLICY_TOP_K', '8'))
    TERM_POLICY_SUPPRESS_THRESHOLD = float(os.getenv('TERM_POLICY_SUPPRESS_THRESHOLD', '-2.0'))
    
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
    RERANKER_WEIGHT = float(os.getenv('RERANKER_WEIGHT', '0.35'))
    ENABLE_RERANKER = os.getenv('ENABLE_RERANKER', 'true').lower() == 'true'
    ENABLE_ADAPTIVE_QUERY_POLICY = os.getenv('ENABLE_ADAPTIVE_QUERY_POLICY', 'true').lower() == 'true'
    ENABLE_RATING_DISPUTES = os.getenv('ENABLE_RATING_DISPUTES', 'true').lower() == 'true'
    RERANKER_MIN_TRAINING_SAMPLES = int(os.getenv('RERANKER_MIN_TRAINING_SAMPLES', '30'))
    ADAPTIVE_QUERY_EPSILON = float(os.getenv('ADAPTIVE_QUERY_EPSILON', '0.15'))
    ADAPTIVE_QUERY_HISTORY_LIMIT = int(os.getenv('ADAPTIVE_QUERY_HISTORY_LIMIT', '200'))

    # Candidate and evaluation budgets
    MAX_PRIMARY_CANDIDATES = int(os.getenv('MAX_PRIMARY_CANDIDATES', '24'))
    MAX_TOTAL_CANDIDATES = int(os.getenv('MAX_TOTAL_CANDIDATES', '30'))
    MAX_RELEVANCE_EVALUATIONS = int(os.getenv('MAX_RELEVANCE_EVALUATIONS', '12'))
    MAX_EVALUATED_RESOURCES = int(os.getenv('MAX_EVALUATED_RESOURCES', '15'))
    MAX_LLM_EVALUATIONS = int(os.getenv('MAX_LLM_EVALUATIONS', '3'))

    # Syllabus-derived query generation
    MAX_SYLLABUS_QUERY_VARIANTS = int(os.getenv('MAX_SYLLABUS_QUERY_VARIANTS', '5'))
    MAX_QUERY_TERMS_PER_VARIANT = int(os.getenv('MAX_QUERY_TERMS_PER_VARIANT', '10'))
