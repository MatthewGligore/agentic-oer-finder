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
    DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
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
    
    # Required Courses for Testing
    REQUIRED_COURSES = [
        'ARTS 1100',
        'ENGL 1101',
        'ENGL 1102',
        'HIST 2111',
        'HIST 2112',
        'ITEC 1001',
        'BIOL 1101K',
        'BIOL 1102'
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
