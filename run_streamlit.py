#!/usr/bin/env python3
"""
Simple script to run Streamlit app
"""
import subprocess
import sys
import os

def main():
    # Change to the project directory
    os.chdir('/Users/timon/UMS_code/ums__chunking')
    
    # Set up the environment
    env = os.environ.copy()
    env['PYTHONPATH'] = '/Users/timon/UMS_code/ums__chunking'
    
    # Run streamlit
    cmd = [
        '/Users/timon/UMS_code/ums__chunking/venv/bin/python',
        '-m', 'streamlit', 'run', 'streamlit_app.py',
        '--server.port', '8501',
        '--server.headless', 'true'
    ]
    
    print("Starting Streamlit application...")
    print("Command:", ' '.join(cmd))
    print("URL: http://localhost:8501")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\nStopping Streamlit...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
