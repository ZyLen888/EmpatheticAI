#!/usr/bin/env python3
"""
Startup script for the Empathetic AI Web Application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import ollama
        from utils.cbt_database import init_cbt_db
        print("✅ All dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install the required packages:")
        print("pip install -r requirements_web.txt")
        return False

def check_ollama():
    """Check if Ollama is running and has the required model"""
    try:
        import ollama
        # Try to list models to see if Ollama is running
        models = ollama.list()
        
        # Check if llama3.2 model is available
        model_names = [model['name'] for model in models.get('models', [])]
        if not any('llama3.2' in name for name in model_names):
            print("⚠️  WARNING: llama3.2 model not found")
            print("Please install it with: ollama pull llama3.2")
            return False
        
        print("✅ Ollama is running with llama3.2 model")
        return True
        
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        print("Please make sure Ollama is installed and running:")
        print("1. Install Ollama from https://ollama.ai")
        print("2. Start Ollama service")
        print("3. Pull the model: ollama pull llama3.2")
        return False

def create_directories():
    """Create necessary directories"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    print("✅ Templates directory ready")

def main():
    print("🧠 Empathetic AI - Web Application Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check Ollama
    if not check_ollama():
        print("\n⚠️  Continuing anyway, but the app may not work properly without Ollama")
    
    # Create directories
    create_directories()
    
    # Initialize database
    try:
        from utils.cbt_database import init_cbt_db
        init_cbt_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1
    
    print("\n🚀 Starting web application...")
    print("📱 The app will be available at: http://localhost:5001")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start the Flask app
    try:
        from web_app import app
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        return 0
    except Exception as e:
        print(f"❌ Failed to start web application: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 