"""
Desktop UI Launcher for API Chart Generator
Launches the Streamlit-based chat interface.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import streamlit
    except ImportError:
        missing_deps.append("streamlit")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import plotly
    except ImportError:
        missing_deps.append("plotly")
    
    return missing_deps

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("📦 Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def launch_ui():
    """Launch the Streamlit UI"""
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    if not app_path.exists():
        print("❌ Streamlit app file not found!")
        return False
    
    print("🚀 Launching API Chart Generator UI...")
    print("🌐 The app will open in your default web browser")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        # Set environment variable to skip email prompt
        env = os.environ.copy()
        env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.headless", "false",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false",
            "--global.showWarningOnDirectExecution", "false"
        ], env=env)
        return True
    except KeyboardInterrupt:
        print("\n👋 UI stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to launch UI: {str(e)}")
        return False

def main():
    """Main launcher function"""
    print("🤖 API Chart Generator - Desktop UI Launcher")
    print("=" * 50)
    
    # Check if dependencies are installed
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("📦 Installing dependencies...")
        if not install_dependencies():
            print("❌ Please install dependencies manually: pip install -r requirements.txt")
            sys.exit(1)
    
    # Check .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  .env file not found!")
        print("📝 Please create a .env file with your API_URL")
        print("💡 Example:")
        print("   API_URL=https://your-api-endpoint.com")
        print("   TEMPERATURE=0.1")
        print("   TOP_K=0.1")
        print("   MAX_TOKENS=2048")
        sys.exit(1)
    
    print("✅ Setup complete! Launching application...")
    print()
    
    # Launch the UI
    if not launch_ui():
        sys.exit(1)

if __name__ == "__main__":
    main()
