"""
Setup script for Kokoro TTS.
This script helps install and configure the Kokoro TTS service.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kokoro-setup")

KOKORO_REPO_URL = "https://github.com/nazdridoy/kokoro-tts.git"
DEFAULT_INSTALL_DIR = Path.home() / "kokoro-tts"
DEFAULT_PORT = 8008

def check_prerequisites():
    """Check if the prerequisites are installed."""
    logger.info("Checking prerequisites...")
    
    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Git is installed.")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("Git is not installed. Please install Git and try again.")
        return False
    
    # Check if Python 3.8+ is installed
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required. You are using %s.%s.%s", 
                    sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
        return False
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} is installed.")
    
    # Check if pip is installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Pip is installed.")
    except subprocess.SubprocessError:
        logger.error("Pip is not installed. Please install pip and try again.")
        return False
    
    return True

def clone_repository(install_dir):
    """Clone the Kokoro TTS repository."""
    logger.info(f"Cloning Kokoro TTS repository to {install_dir}...")
    
    if install_dir.exists():
        logger.warning(f"Directory {install_dir} already exists.")
        while True:
            choice = input(f"The directory {install_dir} already exists. Do you want to use it anyway? [y/N]: ").lower()
            if choice in ("", "n"):
                logger.error("Aborting installation.")
                return False
            elif choice == "y":
                logger.info("Using existing directory.")
                break
            else:
                print("Please enter 'y' or 'n'.")
    else:
        # Create the directory
        install_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Change to the install directory
        os.chdir(install_dir)
        
        # Check if this is already a git repository
        if (install_dir / ".git").exists():
            logger.info("Directory is already a git repository.")
            
            # Pull the latest changes
            subprocess.run(["git", "pull"], check=True)
            logger.info("Pulled latest changes.")
        else:
            # Clone the repository
            subprocess.run(["git", "clone", KOKORO_REPO_URL, "."], check=True)
            logger.info("Repository cloned successfully.")
        
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to clone repository: {e}")
        return False

def install_dependencies(install_dir, cpu_only=True):
    """Install the dependencies."""
    logger.info("Installing dependencies...")
    
    try:
        # Change to the install directory
        os.chdir(install_dir)
        
        # Create a virtual environment
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        logger.info("Created virtual environment.")
        
        # Determine the pip executable path based on the OS
        pip_cmd = str(install_dir / "venv" / ("Scripts" if os.name == "nt" else "bin") / "pip")
        
        # Install the dependencies
        subprocess.run([pip_cmd, "install", "-e", "."], check=True)
        logger.info("Installed dependencies.")
        
        # Install torch with CPU-only support if requested
        if cpu_only:
            logger.info("Installing PyTorch with CPU-only support...")
            subprocess.run([pip_cmd, "install", "torch", "torchaudio", "--index-url", 
                          "https://download.pytorch.org/whl/cpu"], check=True)
            logger.info("Installed PyTorch with CPU-only support.")
        
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def create_startup_script(install_dir, port):
    """Create a startup script for the Kokoro TTS server."""
    logger.info("Creating startup script...")
    
    # Determine the script extension based on the OS
    script_ext = ".bat" if os.name == "nt" else ".sh"
    script_path = install_dir / f"start_kokoro{script_ext}"
    
    # Create the appropriate script content based on the OS
    if os.name == "nt":
        script_content = f"""@echo off
call {install_dir}\\venv\\Scripts\\activate
echo Starting Kokoro TTS server on port {port}...
python -m kokoro.api.server --port {port}
"""
    else:
        script_content = f"""#!/bin/bash
source {install_dir}/venv/bin/activate
echo "Starting Kokoro TTS server on port {port}..."
python -m kokoro.api.server --port {port}
"""
    
    # Write the script to file
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make the script executable on Unix-like systems
    if os.name != "nt":
        os.chmod(script_path, 0o755)
    
    logger.info(f"Created startup script at {script_path}")
    return script_path

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Setup script for Kokoro TTS.")
    parser.add_argument("--install-dir", type=Path, default=DEFAULT_INSTALL_DIR,
                      help=f"Installation directory (default: {DEFAULT_INSTALL_DIR})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                      help=f"Port for the Kokoro TTS server (default: {DEFAULT_PORT})")
    parser.add_argument("--gpu", action="store_true",
                      help="Install with GPU support (default: CPU only)")
    args = parser.parse_args()
    
    logger.info("Starting Kokoro TTS setup...")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Clone the repository
    if not clone_repository(args.install_dir):
        sys.exit(1)
    
    # Install dependencies
    cpu_only = not args.gpu
    if not install_dependencies(args.install_dir, cpu_only):
        sys.exit(1)
    
    # Create startup script
    script_path = create_startup_script(args.install_dir, args.port)
    
    logger.info("Kokoro TTS setup completed successfully!")
    logger.info(f"To start the Kokoro TTS server, run: {script_path}")
    logger.info(f"The server will be available at: http://localhost:{args.port}")
    
    # Update the .env file
    # Ensure we use absolute paths for consistency and avoid Windows path issues
    current_dir = Path(__file__).parent.resolve()
    project_root = current_dir.parent.resolve()
    
    # Define possible .env locations
    env_paths = [
        current_dir / ".env",  # Backend directory
        project_root / ".env"  # Project root
    ]
    
    # Use the first existing .env file, or create one in backend
    env_file = next((path for path in env_paths if path.exists()), current_dir / ".env")
    
    # Update or create the .env file
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            env_content = f.read()
        
        # Check if KOKORO_API_URL is already set
        if "KOKORO_API_URL" not in env_content:
            with open(env_file, "a", encoding="utf-8") as f:
                f.write(f"\n# TTS Configuration\nKOKORO_API_URL=http://localhost:{args.port}\n")
            logger.info(f"Updated .env file at {env_file} with KOKORO_API_URL")
    else:
        # Create a new .env file
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"# TTS Configuration\nKOKORO_API_URL=http://localhost:{args.port}\n")
        logger.info(f"Created new .env file at {env_file} with KOKORO_API_URL")
    
    logger.info("Don't forget to obtain an AssemblyAI API key for the Speech-to-Text functionality.")
    logger.info("You can sign up at: https://www.assemblyai.com/")

if __name__ == "__main__":
    main() 