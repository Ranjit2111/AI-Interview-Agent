#!/usr/bin/env python
"""
Script to ensure all dependencies for the AI Interviewer Agent are properly installed
with the correct versions. This includes checking for the correct version of pydantic
and installing the Kokoro TTS dependencies if needed.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Add TTS dependencies
TTS_DEPENDENCIES = [
    "torch==2.0.1",
    "torchaudio==2.0.2",
    "numpy>=1.24.3",
    "soundfile>=0.12.1",
    "omegaconf>=2.3.0"
]

# Additional required packages
ADDITIONAL_PACKAGES = [
    "backoff>=2.0.0",
]

def check_installed_packages():
    """Return a dictionary of installed packages and their versions."""
    result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"], 
                            capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error checking installed packages: {result.stderr}")
        return {}
    
    import json
    packages = json.loads(result.stdout)
    return {pkg["name"].lower(): pkg["version"] for pkg in packages}


def install_package(package):
    """Install a specified package."""
    print(f"Installing {package}...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                            capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error installing {package}: {result.stderr}")
        return False
    else:
        print(f"Successfully installed {package}")
        return True


def check_kokoro_tts():
    """Check if Kokoro TTS is installed and install it if needed."""
    kokoro_path = Path(__file__).parent / "backend" / "kokoro-tts"
    
    if not kokoro_path.exists():
        print("Kokoro TTS not found. Would you like to install it? (y/n)")
        choice = input().lower()
        if choice == 'y':
            try:
                # Run the setup script
                setup_script = Path(__file__).parent / "backend" / "setup_kokoro_tts.py"
                if setup_script.exists():
                    print("Running Kokoro TTS setup script...")
                    subprocess.run([sys.executable, str(setup_script)], check=True)
                else:
                    print(f"Setup script not found at {setup_script}")
                    print("Installing TTS dependencies...")
                    for package in TTS_DEPENDENCIES:
                        install_package(package)
            except Exception as e:
                print(f"Error setting up Kokoro TTS: {e}")
        else:
            print("Skipping Kokoro TTS installation.")
    else:
        print("Kokoro TTS is already installed.")


def fix_windows_paths():
    """Fix any Windows path issues in configuration files."""
    if platform.system() != "Windows":
        return  # Only apply fixes on Windows
    
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()
        
        # Fix any paths with wrong slashes
        updated_content = env_content.replace("/", "\\")
        
        # Write back if changes were made
        if updated_content != env_content:
            with open(env_path, "w") as f:
                f.write(updated_content)
            print("Fixed Windows paths in .env file")


def main():
    """Main function to check and fix dependencies."""
    # Check if running in a virtual environment
    if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        print("WARNING: You are not running in a virtual environment.")
        print("It is recommended to create and activate a virtual environment before proceeding.")
        print("Continue anyway? (y/n)")
        choice = input().lower()
        if choice != 'y':
            print("Exiting...")
            return
    
    # Get installed packages
    installed_packages = check_installed_packages()
    
    # Check pydantic
    pydantic_version = installed_packages.get('pydantic')
    if pydantic_version and not pydantic_version.startswith('1.'):
        print(f"Incorrect pydantic version installed: {pydantic_version}")
        print("Uninstalling pydantic and pydantic-core...")
        # Uninstall pydantic
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pydantic"], 
                       capture_output=True)
        # Also uninstall pydantic-core which is used by pydantic v2
        if 'pydantic-core' in installed_packages:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pydantic-core"],
                          capture_output=True)
        pydantic_version = None
    
    if not pydantic_version:
        install_package("pydantic==1.10.8")
    else:
        print(f"Correct pydantic version already installed: {pydantic_version}")
    
    # Check langchain-google-genai
    if 'langchain-google-genai' not in installed_packages:
        install_package("langchain-google-genai")
    else:
        print(f"langchain-google-genai already installed: {installed_packages.get('langchain-google-genai')}")
    
    # Install additional required packages
    for package in ADDITIONAL_PACKAGES:
        package_name = package.split('>=')[0].split('==')[0]
        if package_name.lower() not in installed_packages:
            install_package(package)
        else:
            print(f"{package_name} already installed: {installed_packages.get(package_name.lower())}")
    
    # Check requirements.txt
    requirements_path = Path(__file__).parent / "backend" / "requirements.txt"
    if requirements_path.exists():
        print(f"Installing requirements from {requirements_path}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)], 
                       capture_output=True)
    
    # Check for Kokoro TTS
    check_kokoro_tts()
    
    # Fix Windows path issues
    fix_windows_paths()
    
    print("Dependency check and fix completed!")
    print("Please restart your application if it was running.")


if __name__ == "__main__":
    main() 