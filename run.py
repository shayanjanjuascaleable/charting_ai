"""
Main entry point for running the Flask application.
This script allows running the app from the project root.
"""
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir.parent))

# Import and run the Flask app
from backend.app import app

if __name__ == '__main__':
    app.run(debug=True)

