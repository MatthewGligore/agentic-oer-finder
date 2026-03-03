# Agentic OER Finder

A modern, AI-powered Open Educational Resources (OER) finder that helps educators discover and evaluate high-quality educational materials for their courses.

## Project Structure

```
agentic-oer-finder/
├── backend/                       # Python Flask backend
│   ├── app.py                    # Flask application (API server)
│   ├── oer_agent.py              # Main OER search logic
│   ├── config.py                 # Configuration
│   ├── requirements.txt          # Python dependencies
│   ├── evaluators/               # Resource evaluators
│   ├── scrapers/                 # Web scrapers
│   ├── llm/                      # LLM integration
│   ├── utils/                    # Utilities
│   ├── logs/                     # Application logs
│   ├── static/                   # Legacy static assets
│   ├── test_simple.py            # Simple tests
│   └── test_courses.py           # Course-based tests
├── frontend/                      # React + Vite frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── services/             # API service layer
│   │   ├── App.jsx               # Main App component
│   │   └── main.jsx              # Entry point
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── README.md
├── .env                          # Environment variables (copy from .env.example)
├── .env.example                  # Environment template
├── .gitignore
├── setup.sh                      # Setup script (Mac/Linux)
├── setup.bat                     # Setup script (Windows)
└── README.md
```

## Features

- **No API Key Required**: Uses built-in suggestions and web scraping instead of external APIs
- **Course-based Search**: Find OER resources by course code
- **Quality Evaluation**: Automatic scoring of resources using rubric-based evaluation
- **License Checking**: Identifies open licenses and permissions
- **Modern React UI**: Built with React and Vite for fast, responsive experience
- **REST API Backend**: Flask API server for backend operations
- **Integration Guidance**: Provides tips for integrating resources into courses

## Quick Start

### Prerequisites

- Node.js 16+ (for frontend)
- Python 3.10–3.13 recommended (for backend)

Python 3.14 may have compatibility issues with native dependencies in some environments.

### Automated Setup (Recommended)

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### Manual Setup

**Backend:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

## Running the Application

### Development Mode

**Terminal 1 - Start Backend (API server on port 8000):**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
```

**Terminal 2 - Start Frontend (dev server on port 3000):**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:3000** in your browser.

### Alternative Backend Commands

If you prefer to run the backend directly:
```bash
# Option 1: Using the provided run.py script (recommended)
python run.py

# Option 2: Using Python module syntax
python -m backend.app

# Option 3: Using custom port
PORT=9000 python run.py

# Option 4: Direct (if using setup from project root)
cd backend
python app.py
```

## Usage

1. Enter a course code (e.g., ENGL 1101, HIST 2111, ITEC 1001)
2. Optionally specify the term
3. Click "Search OER Resources"
4. Browse the results with quality scores and integration tips
5. Click on resources to visit them directly

## Running Tests

Test the backend locally:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python backend/test_simple.py
```

Test with specific courses:
```bash
python backend/test_courses.py
```

## Building for Production

### Backend
The Flask app runs as-is. For production:
```bash
# Set environment variables
export FLASK_ENV=production

# Run with production server (requires gunicorn)
pip install gunicorn
gunicorn backend.app:app
```

### Frontend
Build optimized static files:
```bash
cd frontend
npm run build
```

Output: `frontend/dist/` - Deploy these files to any static hosting (GitHub Pages, Vercel, Netlify, etc.)

## No API Key Needed

The `.env` file is pre-configured for no-API mode. You don't need to sign up for OpenAI or any other service.

### What Works Without External APIs

- Finding course-related OER from built-in suggestions
- Quality scores for each resource
- The complete web interface
- All main features

## API Endpoints

**Health Check:**
```
GET /api/health
```

**Search for OER Resources:**
```
POST /api/search
Content-Type: application/json

{
  "course_code": "ENGL 1101",
  "term": "Fall 2025"
}
```

**Response:**
```json
{
  "evaluated_resources": [...],
  "resources_found": 5
}
```

## Documentation

- [Backend README](./backend/README.md) - Backend API documentation
- [Frontend README](./frontend/README.md) - React app documentation
- [GITHUB_SETUP.md](./GITHUB_SETUP.md) - Guide for pushing to GitHub
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - Refactoring details

## Architecture

### Frontend (React + Vite)
- React 18 with functional components and hooks
- Vite for fast development and optimized production builds
- Modular CSS with component-scoped styling
- Axios for API communication
- Responsive design for all devices

### Backend (Python + Flask)
- Flask REST API server
- OER Agent for discovery and evaluation
- Web scrapers (BeautifulSoup, Selenium)
- LLM integration (OpenAI, Anthropic) - optional
- Rubric and license evaluation
- Comprehensive logging

## Troubleshooting

### Frontend won't connect to backend
- Ensure Flask is running on `http://localhost:5000`
- Check `frontend/vite.config.js` proxy configuration
- Check browser console (DevTools) for API errors
- Verify CORS headers in Flask response

### Python modules not found
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Port already in use
```bash
# Flask (change from default 5000)
export PORT=5001 && python backend/app.py

# Vite (change from default 3000)
cd frontend && npm run dev -- --port 3001
```

### Module import errors
If you get import errors, make sure you're running from the correct directory:
```bash
# For Flask
cd /path/to/agentic-oer-finder
python backend/app.py

# For tests
python backend/test_simple.py
```

## Development Workflow

### Adding a New Feature

1. **Backend API**: Add endpoint to `backend/app.py`
2. **Frontend Component**: Create component in `frontend/src/components/`
3. **API Service**: Update `frontend/src/services/oerAPI.js`
4. **Styling**: Add CSS in component folder

### Code Style
- Python: Follow PEP 8
- JavaScript/React: ESLint compatible formatting

## Deployment

### Deploy Frontend
```bash
cd frontend
npm run build
# Deploy frontend/dist/ folder to GitHub Pages, Vercel, Netlify, etc.
```

### Deploy Backend
Push to any Python-capable platform (Heroku, Railway, AWS, DigitalOcean, etc.)

Update `.env` variables for production environment.

## GitHub Repository

To push to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: Agentic OER Finder"
git remote add origin https://github.com/USERNAME/agentic-oer-finder.git
git branch -M main
git push -u origin main
```

See [GITHUB_SETUP.md](./GITHUB_SETUP.md) for detailed GitHub setup instructions.

## License

[Add your license information here]

## Support

For issues, questions, or contributions, please open an issue on GitHub.
