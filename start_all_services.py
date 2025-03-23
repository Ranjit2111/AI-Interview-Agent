#!/usr/bin/env python
"""
Start all services required for the AI Interviewer Agent.
This includes:
1. Kokoro TTS server (optional)
2. Backend FastAPI server
3. Frontend Next.js development server

This script provides a Python alternative to start.ps1, adding support for Kokoro TTS.
"""

import os
import sys
import subprocess
import time
import threading
import signal
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("services")

# Get the directory of this script
SCRIPT_DIR = Path(__file__).parent.absolute()

# Default ports
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 3000
DEFAULT_KOKORO_PORT = 8008

# Process tracking
processes = []

def run_command(cmd, cwd=None, name=None, shell=False):
    """Run a command in a separate process."""
    try:
        logger.info(f"Running command: {cmd if shell else ' '.join(map(str, cmd))}")
        
        if os.name == "nt":  # Windows
            # On Windows, we need to create a new process group
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=shell,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if not shell else 0,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        else:  # Unix/Linux
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=shell,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        
        # Create threads to read output and error streams
        def read_output(stream, log_func):
            for line in stream:
                if line.strip():
                    log_func(f"[{name}] {line.strip()}")
                    
        threading.Thread(target=read_output, args=(process.stdout, logger.info)).start()
        threading.Thread(target=read_output, args=(process.stderr, logger.error)).start()
        
        processes.append((process, name))
        return process
    except Exception as e:
        logger.error(f"Failed to run command: {e}")
        return None

def setup_environment():
    """Set up the environment (checking for necessary files)."""
    logger.info("Checking environment setup...")
    
    backend_dir = SCRIPT_DIR / "backend"
    frontend_dir = SCRIPT_DIR / "frontend"
    
    # Check if backend directory exists
    if not backend_dir.exists():
        logger.error(f"Backend directory not found at {backend_dir}")
        return False
        
    # Check if frontend directory exists
    if not frontend_dir.exists():
        logger.error(f"Frontend directory not found at {frontend_dir}")
        return False
    
    # Check if .env file exists in backend
    env_example = backend_dir / ".env.example"
    env_file = backend_dir / ".env"
    
    if not env_file.exists() and env_example.exists():
        logger.info("Creating .env file from example...")
        with open(env_example, "r") as src, open(env_file, "w") as dst:
            dst.write(src.read())
        logger.info("✓ Created backend .env file. Please edit it to add your API keys.")
    elif not env_file.exists():
        logger.error("Backend .env file not found and no example file available.")
        return False
    
    # Check if .env.local file exists in frontend
    frontend_env_file = frontend_dir / ".env.local"
    
    if not frontend_env_file.exists():
        logger.info("Creating frontend .env.local file...")
        with open(frontend_env_file, "w") as f:
            f.write(f"NEXT_PUBLIC_BACKEND_URL=http://localhost:{DEFAULT_BACKEND_PORT}")
        logger.info("✓ Created frontend .env.local file.")
    
    # Check if .venv exists in backend
    venv_dir = backend_dir / ".venv"
    if not venv_dir.exists():
        logger.error(f"Backend virtual environment not found at {venv_dir}")
        logger.error("Please run the original start.ps1 script once to set up the environment.")
        return False
    
    # Verify Python interpreter in virtual environment
    if os.name == "nt":  # Windows
        python_path = venv_dir / "Scripts" / "python.exe"
    else:  # Unix
        python_path = venv_dir / "bin" / "python"
        
    if not python_path.exists():
        logger.error(f"Python not found in virtual environment at {python_path}")
        return False
    
    # Create temp directory if it doesn't exist
    temp_dir = backend_dir / "temp"
    if not temp_dir.exists():
        logger.info("Creating temp directory...")
        temp_dir.mkdir(exist_ok=True)
        logger.info("✓ Created temp directory.")
    
    return True

def verify_backend_imports():
    """Verify that the backend can import its own modules correctly."""
    logger.info("Verifying backend imports...")
    
    backend_dir = SCRIPT_DIR / "backend"
    
    # Determine Python path
    if os.name == "nt":  # Windows
        python_path = backend_dir / ".venv" / "Scripts" / "python.exe"
    else:  # Unix
        python_path = backend_dir / ".venv" / "bin" / "python"
    
    # Simple script to try importing modules the way main.py does
    test_script = (
        "try:\n"
        "    # Import in the same way main.py does\n"
        "    from utils.docs_generator import generate_static_docs\n"
        "    print('Backend imports verified successfully')\n"
        "    exit(0)\n"
        "except ImportError as e:\n"
        "    print(f'Import error: {e}')\n"
        "    exit(1)\n"
    )
    
    # Create a temporary file
    test_file = backend_dir / "temp_import_test.py"
    try:
        with open(test_file, "w") as f:
            f.write(test_script)
            
        # Run the test script from the backend directory
        result = subprocess.run(
            [str(python_path), str(test_file.name)],  # Use just the filename since we're running in backend_dir
            cwd=backend_dir,  # Run from backend directory
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Backend imports verified successfully.")
            return True
        else:
            logger.error(f"Backend import verification failed: {result.stdout.strip()} {result.stderr.strip()}")
            logger.error("Import error in the backend code. The application might not start correctly.")
            return False
    except Exception as e:
        logger.error(f"Failed to verify backend imports: {e}")
        return False
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

def start_kokoro_tts(port):
    """Start the Kokoro TTS server."""
    logger.info("Starting Kokoro TTS server...")
    
    # Determine the script name based on the OS
    script_name = "start_kokoro.bat" if os.name == "nt" else "start_kokoro.sh"
    
    # Default location for Kokoro TTS
    kokoro_dir = Path.home() / "kokoro-tts"
    script_path = kokoro_dir / script_name
    
    if not script_path.exists():
        logger.warning(f"Kokoro TTS startup script not found at {script_path}")
        logger.warning("You might need to install Kokoro TTS first.")
        logger.warning("Run: python backend/setup_kokoro_tts.py")
        
        # Ask user if they want to install Kokoro TTS now
        install_now = input("Would you like to install Kokoro TTS now? (y/n): ").lower().strip() == 'y'
        if install_now:
            logger.info("Installing Kokoro TTS...")
            setup_script = SCRIPT_DIR / "backend" / "setup_kokoro_tts.py"
            if setup_script.exists():
                try:
                    subprocess.run([sys.executable, str(setup_script)], check=True)
                    logger.info("Kokoro TTS installed successfully.")
                    # Try to find the script again
                    if script_path.exists():
                        logger.info("Kokoro TTS startup script found.")
                    else:
                        logger.error("Kokoro TTS startup script still not found after installation.")
                        return None
                except subprocess.SubprocessError as e:
                    logger.error(f"Failed to install Kokoro TTS: {e}")
                    return None
            else:
                logger.error(f"Kokoro TTS setup script not found at {setup_script}")
                return None
        else:
            logger.info("Proceeding without Kokoro TTS. Speech output functionality will be limited.")
            return None
    
    # On Windows, we need to call the batch file
    if os.name == "nt":
        cmd = [str(script_path)]
    else:
        cmd = ["bash", str(script_path)]
    
    return run_command(cmd, name="Kokoro TTS")

def start_backend(port):
    """Start the backend FastAPI server."""
    logger.info(f"Starting backend server on port {port}...")
    
    backend_dir = SCRIPT_DIR / "backend"
    
    # Check if main.py exists
    main_file = backend_dir / "main.py"
    if not main_file.exists():
        logger.error(f"Backend main.py not found at {main_file}")
        return None
    
    # Match exactly what the original start.ps1 did:
    # Run the command inside the backend directory directly
    if os.name == "nt":  # Windows
        # Use correct path formatting
        venv_path = Path(".venv") / "Scripts" / "activate.bat"
        # Note: we run uvicorn with main:app NOT backend.main:app
        activate_cmd = f"\"{venv_path}\" && python -m uvicorn main:app --host 0.0.0.0 --port {port} --reload"
        return run_command(f"cmd /c {activate_cmd}", cwd=backend_dir, name="Backend", shell=True)
    else:  # Unix/Linux
        venv_path = Path(".venv") / "bin" / "activate"
        activate_cmd = f"source {venv_path} && python -m uvicorn main:app --host 0.0.0.0 --port {port} --reload"
        return run_command(["bash", "-c", activate_cmd], cwd=backend_dir, name="Backend")

def start_frontend(port):
    """Start the frontend Next.js development server."""
    logger.info(f"Starting frontend server on port {port}...")
    
    # Change to the frontend directory
    frontend_dir = SCRIPT_DIR / "frontend"
    
    # Check if package.json exists
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        logger.error(f"Frontend package.json not found at {package_json}")
        return None
    
    # Use npm to start the frontend
    if os.name == "nt":  # Windows
        # Following start.ps1's approach: use npm install first
        npm_install_cmd = "npm.cmd install"
        logger.info("Installing frontend dependencies...")
        run_command(npm_install_cmd, cwd=frontend_dir, name="Frontend-Install", shell=True)
        
        # Then start the dev server
        return run_command("npm.cmd run dev", cwd=frontend_dir, name="Frontend", shell=True)
    else:  # Unix/Linux
        # Install dependencies
        logger.info("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Then start the dev server
        return run_command(["npm", "run", "dev"], cwd=frontend_dir, name="Frontend")

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Shutting down services...")
    
    for process, name in processes:
        if process.poll() is None:  # If process is still running
            logger.info(f"Stopping {name}...")
            
            try:
                if os.name == "nt":  # Windows
                    # On Windows, send Ctrl+C to the process group
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                    
                    # Wait for a bit, then forcibly terminate if still running
                    time.sleep(2)
                    if process.poll() is None:
                        process.terminate()
                else:  # Unix/Linux
                    # On Unix, send SIGTERM, wait, then SIGKILL if necessary
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                
                # Wait for the process to exit
                process.wait(timeout=5)
                logger.info(f"{name} stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
                # Force kill if all else fails
                try:
                    process.kill()
                except:
                    pass
    
    logger.info("All services stopped")
    sys.exit(0)

def monitor_processes():
    """Monitor running processes and exit if any of them exit."""
    while True:
        for i, (process, name) in enumerate(processes):
            if process.poll() is not None:  # If process has exited
                exit_code = process.returncode
                logger.error(f"{name} exited with code {exit_code}")
                
                # Stop other processes
                signal_handler(None, None)
        
        time.sleep(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Start all services for the AI Interviewer Agent.")
    parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT,
                      help=f"Port for the backend server (default: {DEFAULT_BACKEND_PORT})")
    parser.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT,
                      help=f"Port for the frontend server (default: {DEFAULT_FRONTEND_PORT})")
    parser.add_argument("--kokoro-port", type=int, default=DEFAULT_KOKORO_PORT,
                      help=f"Port for the Kokoro TTS server (default: {DEFAULT_KOKORO_PORT})")
    parser.add_argument("--no-kokoro", action="store_true",
                      help="Don't start the Kokoro TTS server")
    parser.add_argument("--skip-backend", action="store_true",
                      help="Skip starting the backend server")
    parser.add_argument("--skip-frontend", action="store_true",
                      help="Skip starting the frontend server")
    parser.add_argument("--verify-only", action="store_true",
                      help="Only verify the environment setup without starting services")
    parser.add_argument("--skip-verification", action="store_true",
                      help="Skip import verification (use if you're having issues with verification)")
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Display welcome message
    print("===================================")
    print("   AI INTERVIEWER AGENT STARTUP    ")
    print("===================================")
    print()
    
    # Check environment
    if not setup_environment():
        logger.error("Environment setup failed. Please resolve the issues and try again.")
        return
    
    # Verify backend imports if we're going to start the backend
    if not args.skip_backend and not args.verify_only and not args.skip_verification:
        verification_result = verify_backend_imports()
        if not verification_result:
            logger.error("Backend import verification failed.")
            logger.error("This may cause issues when starting the backend server.")
            logger.error("Options:")
            logger.error("1. Fix the import issues in the backend code")
            logger.error("2. Run with --skip-verification to bypass this check")
            logger.error("3. Run only the frontend with --skip-backend")
            
            # Ask if user wants to continue
            if input("Do you want to continue anyway? (y/n): ").lower().strip() != 'y':
                logger.info("Startup aborted. Resolve the issues and try again.")
                return
            logger.warning("Continuing despite verification failure. The backend may not start correctly.")
    
    # If only verifying, exit now
    if args.verify_only:
        logger.info("Environment verification completed. Use --help to see available options.")
        return
    
    # Start Kokoro TTS server
    kokoro_process = None
    if not args.no_kokoro:
        kokoro_process = start_kokoro_tts(args.kokoro_port)
        if kokoro_process:
            # Give Kokoro TTS some time to start
            logger.info("Waiting for Kokoro TTS to initialize...")
            time.sleep(5)
        else:
            logger.warning("Proceeding without Kokoro TTS. Text-to-speech functionality will be unavailable.")
    
    # Start backend server
    backend_process = None
    if not args.skip_backend:
        backend_process = start_backend(args.backend_port)
        if not backend_process:
            logger.error("Failed to start backend server")
            # Stop Kokoro if it was started
            if kokoro_process:
                logger.info("Stopping Kokoro TTS since backend failed to start...")
                signal_handler(None, None)
            return
    
    # Start frontend server
    frontend_process = None
    if not args.skip_frontend:
        frontend_process = start_frontend(args.frontend_port)
        if not frontend_process:
            logger.error("Failed to start frontend server")
            # Stop other services
            logger.info("Stopping other services since frontend failed to start...")
            signal_handler(None, None)
            return
    
    # Check if any services were started
    if len(processes) == 0:
        logger.error("No services were started. Please check your arguments.")
        return
    
    # Monitor processes
    monitor_thread = threading.Thread(target=monitor_processes)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    logger.info("Services started successfully")
    if not args.skip_backend:
        logger.info(f"Backend server: http://localhost:{args.backend_port}")
    if not args.skip_frontend:
        logger.info(f"Frontend server: http://localhost:{args.frontend_port}")
    if not args.no_kokoro and kokoro_process:
        logger.info(f"Kokoro TTS server: http://localhost:{args.kokoro_port}")
    
    logger.info("Press Ctrl+C to stop all services")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main() 