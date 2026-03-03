#!/bin/bash
# Quick setup script for Agentic OER Finder
# This script sets up both backend and frontend for development

set -e

echo "🚀 Agentic OER Finder - Quick Setup"
echo "================================"
echo ""

# Backend Setup
echo "📦 Setting up Python backend..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "✅ Backend setup complete!"
echo ""

# Frontend Setup
echo "📦 Setting up React frontend..."
cd frontend

echo "Installing Node dependencies..."
npm install

echo "✅ Frontend setup complete!"
echo ""

# Summary
echo "================================"
echo "✨ Setup Complete!"
echo "================================"
echo ""
echo "To run the application:"
echo ""
echo "Terminal 1 - Backend:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:3000"
echo ""
echo "For more information, see README.md"
