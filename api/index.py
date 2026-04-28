# api/index.py
# Vercel serverless entry point - imports the Flask app from the root app.py

import sys
import os

# Add the project root to the Python path so all imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel calls the handler named 'app'
# No changes to app.py needed - this file just exposes it
