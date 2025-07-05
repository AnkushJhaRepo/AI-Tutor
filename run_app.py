import subprocess
import webbrowser
import time
import sys
import os
import requests
from urllib.parse import urljoin
import locale

def get_system_encoding():
    """Get the system's default encoding."""
    try:
        return locale.getpreferredencoding()
    except:
        return 'utf-8'

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ['GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("\nError: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease create a .env file in the project root with these variables.")
        print("Example .env file:")
        print("GEMINI_API_KEY=your_api_key_here")
        print("DEBUG=True")  # Changed to True for local development
        return False
    return True

def check_dependencies():
    """Check if all required Python packages are installed."""
    try:
        import fastapi
        import uvicorn
        import google.generativeai
        return True
    except ImportError as e:
        print(f"\nError: Missing required package: {str(e)}")
        print("Please run: pip install -r requirements.txt")
        return False

def wait_for_server(url: str, max_retries: int = 5, delay: int = 2) -> bool:
    """Wait for the server to be ready by checking the health endpoint."""
    for i in range(max_retries):
        try:
            response = requests.get(urljoin(url, "/api/health"))
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(delay)
    return False

def run_app():
    """Run the application in development mode."""
    print("Checking environment and dependencies...")
    
    # Check environment variables
    if not check_environment():
        return
    
    # Check Python packages
    if not check_dependencies():
        return
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Set environment variables for local development
    os.environ["DEBUG"] = "True"
    os.environ["ENVIRONMENT"] = "development"
    
    # Activate virtual environment if it exists
    venv_path = os.path.join(script_dir, "venv")
    if os.path.exists(venv_path):
        if sys.platform == "win32":
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")
    else:
        python_path = sys.executable

    server_url = "http://localhost:8000"
    print("\nStarting the application in development mode...")

    # Start the FastAPI app in a subprocess with development settings
    try:
        # Use system encoding for subprocess
        encoding = get_system_encoding()
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Development server settings
        app_process = subprocess.Popen(
            [
                python_path, "-m", "uvicorn", "app.main:app",
                "--reload",  # Enable auto-reload
                "--reload-dir", "app",  # Watch app directory for changes
                "--host", "0.0.0.0",
                "--port", "8000",
                "--log-level", "debug"  # More detailed logs for development
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding=encoding,
            errors='replace',
            startupinfo=startupinfo,
            bufsize=1,
            env=dict(os.environ, PYTHONPATH=script_dir)  # Ensure proper Python path
        )

        # Wait for server to be ready
        if wait_for_server(server_url):
            print("Server is ready! Opening browser...")
            webbrowser.open(server_url)
        else:
            print("\nError: Server failed to start. Checking logs...")
            try:
                # Read stderr with timeout
                import threading
                error_output = []
                def read_stderr():
                    while True:
                        line = app_process.stderr.readline()
                        if not line:
                            break
                        error_output.append(line.strip())
                
                stderr_thread = threading.Thread(target=read_stderr)
                stderr_thread.daemon = True
                stderr_thread.start()
                stderr_thread.join(timeout=2)
                
                if error_output:
                    print("\nServer Error Log:")
                    print("\n".join(error_output))
                else:
                    print("No error output found. Checking if port 8000 is in use...")
                    try:
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        result = sock.connect_ex(('127.0.0.1', 8000))
                        if result == 0:
                            print("Port 8000 is already in use. Please close any other applications using this port.")
                        sock.close()
                    except:
                        pass
            except Exception as e:
                print(f"Error reading server output: {str(e)}")
            finally:
                app_process.terminate()
                return

        print("\nDevelopment server is running. Press Ctrl+C to stop.")
        print("Logs will appear below:")
        print("Note: Auto-reload is enabled. The server will restart when you make changes to the code.")

        # Print both stdout and stderr from the server
        while True:
            try:
                output = app_process.stdout.readline()
                error = app_process.stderr.readline()
                
                if output:
                    print(output.strip())
                if error:
                    print("Error:", error.strip(), file=sys.stderr)
                    
                if app_process.poll() is not None:
                    print("\nServer process ended unexpectedly.")
                    break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error reading server output: {str(e)}")
                break
                
    except KeyboardInterrupt:
        print("\nShutting down the development server...")
        app_process.terminate()
        app_process.wait()
    except Exception as e:
        print(f"\nError starting server: {str(e)}")
        return

if __name__ == "__main__":
    run_app() 