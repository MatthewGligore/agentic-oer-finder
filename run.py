#!/usr/bin/env python
"""
Entrypoint script for running the Agentic OER Finder Flask API server
Run from project root: python run.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app


def _warn_on_python_version() -> None:
    """Print a compatibility warning for Python runtimes newer than tested range."""
    if sys.version_info >= (3, 14):
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print("⚠️  Compatibility warning:")
        print(f"   Detected Python {version}")
        print("   Recommended version for this project: Python 3.10–3.13")
        print("   Some native dependencies may fail or behave unexpectedly on 3.14+\n")

if __name__ == '__main__':
    from backend.config import Config
    _warn_on_python_version()
    port = int(os.environ.get('PORT', getattr(Config, 'PORT', 8000)))
    debug = getattr(Config, 'DEBUG', True)
    
    print("\n" + "="*60)
    print("🚀 Agentic OER Finder API Server")
    print("="*60)
    print(f"Starting on: http://0.0.0.0:{port}")
    print(f"API Endpoint: http://localhost:{port}/api/search")
    print(f"Health Check: http://localhost:{port}/api/health")
    print(f"Debug Mode: {debug}")
    print("="*60 + "\n")
    
    app.run(debug=debug, port=port, host='0.0.0.0')
