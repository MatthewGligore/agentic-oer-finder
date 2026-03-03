# GitHub Repository Setup

This document explains how to set up this repository on GitHub and configure it for collaborative development.

## Preparing for GitHub

This project is ready to be pushed to a private GitHub repository. Follow these steps:

### 1. Create a New Repository on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Enter repository name: `agentic-oer-finder`
3. Select **Private** (for a private repository)
4. Do NOT initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

### 2. Initialize Git and Push

```bash
# Navigate to the project root
cd /Users/mgligore/Downloads/agentic-oer-finder

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Agentic OER Finder with React + Vite frontend"

# Add remote repository (replace USERNAME/REPO with your details)
git remote add origin https://github.com/USERNAME/agentic-oer-finder.git

# Push to GitHub (use main or master depending on your preference)
git branch -M main
git push -u origin main
```

### 3. Set Up Basic Configuration

After pushing, configure these GitHub settings:

#### Branch Protection (Optional but Recommended)
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Require pull request reviews before merging
4. Require status checks to pass

#### Secrets and Variables (for CI/CD)
1. Go to Settings → Secrets and variables → Actions
2. No secrets needed for development, but useful for deployment

## Project Structure for GitHub

The repository is organized as follows:

```
agentic-oer-finder/
├── frontend/              # React + Vite SPA
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── evaluators/            # Python evaluation modules
├── scrapers/              # Web scraping modules
├── llm/                   # LLM integration
├── utils/                 # Utilities
├── app.py                 # Flask backend
├── oer_agent.py           # Main agent logic
├── requirements.txt       # Python dependencies
├── .gitignore
├── .env.example
└── README.md
```

## Development Workflow

### For Contributors

1. Clone the repository:
   ```bash
   git clone https://github.com/USERNAME/agentic-oer-finder.git
   cd agentic-oer-finder
   ```

2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

4. Push and create a Pull Request:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation update
- `refactor:` - Code refactoring without behavior change
- `test:` - Test additions or updates
- `ci:` - CI/CD configuration changes

## Environment Setup for Contributors

### Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy example env file
cp .env.example .env
# Edit .env as needed

# Run backend
python app.py
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## CI/CD Ready

The project structure supports GitHub Actions for:
- Running Python tests when code is pushed
- Building the React app for production
- Deploying to hosting services

(GitHub Actions workflows can be added in `.github/workflows/` directory)

## Security Considerations

- ✅ `.gitignore` configured to exclude sensitive files
- ✅ `.env.example` shows structure without secrets
- ✅ CORS enabled only for local development
- ✅ No API keys committed to repository

## Deployment

### Frontend Deployment
- Build: `cd frontend && npm run build`
- Output: `frontend/dist/` directory
- Deploy to: GitHub Pages, Vercel, Netlify, or any static host

### Backend Deployment
- Requires Python 3.8+
- Can be deployed to: Heroku, AWS, DigitalOcean, or other platform
- Set `FLASK_ENV=production` in production

## Issues and Pull Requests

- Use clear titles and descriptions
- Link related issues
- Include screenshots for UI changes
- Run tests before submitting PR

## Questions?

For setup issues or questions, please open an issue on GitHub.
