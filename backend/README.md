# Backend - Python + Flask

REST API server for the Agentic OER Finder, built with Flask.

Recommended Python version: 3.10–3.13.

## Quick Start

```bash
# From project root
source venv/bin/activate  # Activate virtual environment
pip install -r backend/requirements.txt
python run.py
```

The API will start on `http://localhost:8000`

### Alternative Ways to Run

```bash
# Option 1: Using module syntax
python -m backend.app

# Option 2: Using custom port
PORT=9000 python run.py

# Option 3: Change to backend directory
cd backend
python app.py
```

## Project Structure

```
backend/
├── app.py                  # Flask application (entry point)
├── oer_agent.py           # Main OER search and evaluation logic
├── config.py              # Configuration management
├── cli.py                 # Command-line interface
├── requirements.txt       # Python dependencies
├── evaluators/            # Resource evaluation modules
│   ├── rubric_evaluator.py
│   └── license_checker.py
├── scrapers/              # Web scraping modules
│   ├── syllabus_scraper.py
│   ├── syllabus_scraper_selenium.py
│   └── alg_scraper.py
├── llm/                   # Language model integration
│   └── llm_client.py
├── utils/                 # Utility modules
│   ├── logger.py
│   └── __init__.py
├── logs/                  # Application logs
├── static/                # Legacy static files
├── test_simple.py         # Simple tests
└── test_courses.py        # Course-based tests
```

## API Endpoints

### Health Check
```
GET /api/health
```

Returns: `{ "status": "ok", "message": "Agentic OER Finder API is running" }`

### Search OER Resources
```
POST /api/search
Content-Type: application/json
```

**Request:**
```json
{
  "course_code": "ENGL 1101",
  "term": "Fall 2025"
}
```

**Response:**
```json
{
  "course_code": "ENGL 1101",
  "term": "Fall 2025",
  "resources_found": 5,
  "evaluated_resources": [
    {
      "resource": {
        "title": "...",
        "url": "...",
        "description": "..."
      },
      "rubric_evaluation": { "score": 85 },
      "license_check": { "license": "CC-BY-4.0" },
      "integration_guidance": "..."
    }
  ]
}
```

## Dependencies

### Required
- `flask>=3.0.0` - Web framework
- `flask-cors>=4.0.0` - CORS support
- `requests>=2.31.0` - HTTP client
- `beautifulsoup4>=4.12.2` - HTML parsing
- `python-dotenv>=1.0.0` - Environment variables

### Optional (for enhanced scraping)
- `selenium>=4.0.0` - JavaScript-rendering scraper
- `openai>=1.3.0` - OpenAI API integration
- `anthropic>=0.7.0` - Anthropic API integration

## Configuration

Configuration is managed through `config.py` and environment variables.

### Environment Variables (.env)

```
# LLM Configuration
DEFAULT_LLM_PROVIDER=openai  # or 'anthropic' or 'no_api'
DEFAULT_MODEL=gpt-4o
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Scraper Configuration
SYLLABUS_BASE_URL=https://ggc.simplesyllabus.com
ALG_BASE_URL=https://alg.manifoldapp.org

# Logging
LOG_DIR=backend/logs
LOG_LEVEL=INFO

# Flask Configuration
FLASK_ENV=development
DEBUG=True
PORT=5000
```

See `.env.example` for template.

## Running Tests

### Simple Test
```bash
python backend/test_simple.py
```

Tests basic OER search functionality without external APIs.

### Course-based Tests
```bash
python backend/test_courses.py
```

Tests OER search for multiple course codes.

## Development

### File Organization

- **app.py**: Flask routes and request handling
- **oer_agent.py**: Core business logic (search, evaluation)
- **config.py**: Configuration management
- **evaluators/**: Modules that score/evaluate resources
- **scrapers/**: Modules that fetch data from web sources
- **llm/**: Language model integration for analysis
- **utils/**: Helper functions and logging

### Adding a New API Endpoint

1. Create a route in `app.py`:
```python
@app.route('/api/your-endpoint', methods=['POST'])
def your_endpoint():
    """Endpoint description"""
    try:
        data = request.get_json()
        # Your logic here
        return jsonify({'result': data})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
```

2. Make sure CORS is configured if needed

3. Log important operations with `logger.info()`

### Code Style

Follow PEP 8:
```bash
# Check with pylint (optional)
pip install pylint
pylint backend/*.py
```

## Logging

Application logs are written to `backend/logs/`:

- `usage_log.json` - Structured usage data
- `usage_log.csv` - CSV formatted usage data

Access logs via the Flask app run output.

## Performance

The OER Agent search can take 30-60 seconds due to:
- Web scraping for syllabi
- Database searches
- LLM analysis (if enabled)
- Resource evaluation

Typical response time: **45-90 seconds**

## Deployment

### Local Development
```bash
python backend/app.py
```

### Production with Gunicorn
```bash
pip install gunicorn
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Environment Variables for Production

Set these via platform environment:
```
FLASK_ENV=production
DEFAULT_LLM_PROVIDER=no_api  # or configure OpenAI/Anthropic
PORT=5000
```

### Deploying to Cloud Platforms

#### Heroku
```bash
heroku create your-app-name
git push heroku main
```

#### Railway
```bash
railway init
railway up
```

#### AWS/DigitalOcean
See platform-specific documentation for Flask deployment.

## Troubleshooting

### Import Errors
Ensure you're using the correct Python path:
```bash
source venv/bin/activate
python backend/app.py  # from project root
```

### Module Not Found
```bash
pip install -r backend/requirements.txt
```

### CORS Errors
Check that CORS is properly configured in `app.py`:
```python
CORS(app, resources={r"/api/*": {"origins": [...]}})
```

### Slow Searches
- Reduce timeout in config
- Use `no_api` mode for faster responses
- Check network connectivity for web scraping

## API Response Examples

### Successful Search
```json
{
  "course_code": "ENGL 1101",
  "resources_found": 3,
  "evaluated_resources": [
    {
      "resource": {
        "title": "OpenStax English Literature",
        "url": "https://openstax.org/...",
        "type": "textbook"
      },
      "rubric_evaluation": {
        "score": 92,
        "criteria": {...}
      },
      "license_check": {
        "license": "CC-BY-4.0",
        "verified": true
      },
      "integration_guidance": "Can be used as primary textbook..."
    }
  ]
}
```

### Error Response
```json
{
  "error": "Course code is required",
  "debug": false
}
```

## Support

For issues with the backend:
1. Check logs in `backend/logs/`
2. Enable debug mode in `.env`
3. See main README.md for general troubleshooting
