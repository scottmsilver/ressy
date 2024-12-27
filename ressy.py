import multiprocessing
import time
import sys
import uvicorn
import requests
from contextlib import contextmanager
import signal
import os

from api import app
from main import main as cli_main
from models import Base
from database import engine

def run_api_server():
    """Run the FastAPI server using uvicorn"""
    # Initialize the database
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

@contextmanager
def start_api_server():
    """Start the API server in a separate process and wait for it to be ready"""
    # Start the API server process
    server_process = multiprocessing.Process(target=run_api_server)
    server_process.start()

    # Wait for the server to be ready
    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        try:
            response = requests.get("http://localhost:8000/docs")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            attempt += 1
            time.sleep(1)
    
    if attempt == max_attempts:
        print("Error: Could not start API server")
        server_process.terminate()
        sys.exit(1)

    try:
        yield
    finally:
        # Cleanup: terminate the server process
        server_process.terminate()
        server_process.join()

def main():
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\nShutting down Ressy...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

    print("Starting Ressy Property Management System...")
    print("Initializing database and API server...")

    with start_api_server():
        try:
            cli_main()
        except KeyboardInterrupt:
            print("\nShutting down Ressy...")
            sys.exit(0)

if __name__ == "__main__":
    # Ensure clean process termination on Windows
    if sys.platform == 'win32':
        multiprocessing.freeze_support()
    main()
