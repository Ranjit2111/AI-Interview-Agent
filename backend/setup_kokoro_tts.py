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
import platform  # Added for OS check
import venv # Added for venv creation clarity
import shutil # Added for checking espeak command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kokoro-setup")

# Use the official Kokoro repository
KOKORO_REPO_URL = "https://github.com/hexgrad/kokoro.git" # Changed from nazdridoy fork
KOKORO_INTERNAL_DIR_NAME = "kokoro_official" # Use a distinct name to avoid conflicts with old clone
DEFAULT_INSTALL_DIR = Path.home() / KOKORO_INTERNAL_DIR_NAME # Changed directory name
DEFAULT_PORT = 8008
CUSTOM_SERVER_SCRIPT_NAME = "kokoro_tts_server.py" # Name for our custom FastAPI server script

def check_prerequisites():
    """Check if the prerequisites are installed."""
    logger.info("Checking prerequisites...")
    success = True
    
    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True, text=True) # Use text=True
        logger.info("Git is installed.")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("Git is not installed. Please install Git and try again.")
        success = False

    # Check if Python 3.9+ is recommended (Kokoro's env.yml uses 3.9)
    if sys.version_info < (3, 9):
        logger.warning(f"Python 3.9 or higher is recommended for Kokoro. You are using {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        # Allow continuation, but warn
    else:
        logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} is installed.")
    
    # Check if pip is installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True, text=True) # Use text=True
        logger.info("Pip is installed.")
    except (subprocess.SubprocessError, FileNotFoundError): # Check FileNotFoundError too
        logger.error("Pip is not installed. Please install pip and try again.")
        success = False

    # Check for espeak-ng (essential dependency)
    espeak_cmd = "espeak-ng"
    if shutil.which(espeak_cmd) is None: # Use shutil.which for cross-platform PATH check
        logger.warning("="*80)
        logger.warning("! espeak-ng NOT FOUND IN PATH !")
        logger.warning("Kokoro TTS requires 'espeak-ng' to be installed and accessible in the system's PATH.")
        logger.warning("Please install it using your system's package manager:")
        logger.warning("  - Ubuntu/Debian: sudo apt-get update && sudo apt-get install espeak-ng")
        logger.warning("  - macOS: brew install espeak-ng")
        logger.warning("  - Windows: Download from https://github.com/espeak-ng/espeak-ng/releases")
        logger.warning("After installation, ensure it's added to your system's PATH.")
        logger.warning("Continuing setup, but the TTS server WILL LIKELY FAIL to start without espeak-ng.")
        logger.warning("="*80)
        # Allow continuation, but warn strongly
    else:
        logger.info(f"'{espeak_cmd}' found in PATH.")
        # Optional: Run version check if needed
        # try:
        #     result = subprocess.run([espeak_cmd, "--version"], check=True, capture_output=True, text=True)
        #     logger.info(f"espeak-ng version check successful: {result.stdout.strip()}")
        # except (subprocess.SubprocessError, FileNotFoundError):
        #      logger.warning(f"Found '{espeak_cmd}' in PATH, but failed to execute '--version'. Check installation.")

    return success

def clone_repository(install_dir):
    """Clone the Kokoro TTS repository."""
    repo_subdir = install_dir / "repo" # Clone into a subdirectory
    logger.info(f"Attempting to clone/update official Kokoro repository in {repo_subdir}...")

    try:
        if repo_subdir.exists() and (repo_subdir / ".git").exists():
             logger.info(f"Directory {repo_subdir} exists and is a git repo. Attempting to pull latest changes...")
             # Change to the repo directory to run git pull
             original_cwd = Path.cwd()
             os.chdir(repo_subdir)
             subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)
             logger.info("Pulled latest changes from official Kokoro repository.")
             os.chdir(original_cwd) # Change back
        else:
             logger.info(f"Directory {repo_subdir} does not exist or is not a git repo. Cloning...")
             repo_subdir.mkdir(parents=True, exist_ok=True)
             subprocess.run(["git", "clone", KOKORO_REPO_URL, str(repo_subdir)], check=True, capture_output=True, text=True)
             logger.info("Official Kokoro repository cloned successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed git operation in {repo_subdir}: {e}")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during git operation: {e}")
        return False


def install_dependencies(install_dir, cpu_only=True):
    """Install the dependencies in a virtual environment."""
    venv_dir = install_dir / "venv"
    logger.info(f"Setting up virtual environment in {venv_dir} and installing dependencies...")

    try:
        # Create a virtual environment if it doesn't exist
        if not venv_dir.exists():
            # Use the venv module directly
            venv.create(venv_dir, with_pip=True)
            logger.info("Created virtual environment.")
        else:
            logger.info("Virtual environment already exists.")
        
        # Determine the pip executable path based on the OS
        pip_cmd = str(venv_dir / ("Scripts" if platform.system() == "Windows" else "bin") / "pip").replace("\\", "/") # Ensure forward slashes
        python_cmd = str(venv_dir / ("Scripts" if platform.system() == "Windows" else "bin") / "python").replace("\\", "/") # Ensure forward slashes

        # Upgrade pip first
        logger.info("Upgrading pip in venv...")
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True, capture_output=True, text=True)

        # Install necessary packages: kokoro, soundfile, fastapi, uvicorn
        # Also install misaki[en] as per kokoro docs (optional but good practice)
        # Use --no-cache-dir to avoid potential issues with cached packages
        # Pin kokoro version for stability, >=0.9.4 has breaking changes potentially
        base_packages = ["kokoro==0.9.3", "soundfile", "fastapi", "uvicorn[standard]", "python-dotenv", "misaki[en]"]
        logger.info(f"Installing base packages: {', '.join(base_packages)}...")
        subprocess.run([pip_cmd, "install", "--upgrade", "--no-cache-dir"] + base_packages, check=True, capture_output=True, text=True)
        logger.info("Installed base server and Kokoro dependencies.")

        # Install torch with appropriate support
        if cpu_only:
            logger.info("Installing PyTorch with CPU-only support...")
            # Use --index-url for CPU version explicitly
            torch_packages = ["torch", "torchaudio"]
            subprocess.run([pip_cmd, "install", "--upgrade", "--no-cache-dir"] + torch_packages + ["--index-url", "https://download.pytorch.org/whl/cpu"], check=True, capture_output=True, text=True)
            logger.info("Installed PyTorch with CPU-only support.")
        else:
            # Instruct user to install GPU version manually for simplicity
            # Handling CUDA versions automatically is complex
            logger.warning("GPU support requested. Please install the appropriate PyTorch version for your CUDA setup manually within the venv.")
            logger.warning(f"Example: Activate the venv ({venv_dir}/bin/activate or {venv_dir}\\Scripts\\activate) and find your command at https://pytorch.org/")
            # Install basic torch/torchaudio as a fallback, user can upgrade
            logger.info("Installing basic PyTorch (CPU version) as fallback. Upgrade manually for GPU.")
            torch_packages = ["torch", "torchaudio"]
            subprocess.run([pip_cmd, "install", "--upgrade", "--no-cache-dir"] + torch_packages, check=True, capture_output=True, text=True)


        # We don't need to install the cloned repo itself (`-e .`) anymore
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed dependency installation step: {e}")
        logger.error(f"Command: '{e.cmd}'")
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Stderr: {e.stderr}")
        logger.error(f"Stdout: {e.stdout}") # Include stdout for more context
        return False
    except Exception as e:
         logger.error(f"An unexpected error occurred during dependency installation: {e}")
         return False

# Create the custom FastAPI server script (if it doesn't exist)
def ensure_custom_server_script(install_dir):
    server_script_path = install_dir / CUSTOM_SERVER_SCRIPT_NAME
    if server_script_path.exists():
        logger.info(f"Custom server script {CUSTOM_SERVER_SCRIPT_NAME} already exists.")
        return True

    logger.info(f"Creating custom FastAPI server script at {server_script_path}...")
    # Basic server structure (can be enhanced later)
    # IMPORTANT: Ensure correct imports within the script content
    server_script_content = f"""
import logging
import os
import platform # Added for MPS check
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import soundfile as sf
import io
import numpy as np
from contextlib import asynccontextmanager
from kokoro import KPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kokoro-tts-server")

# --- Configuration ---
# Use environment variables or defaults
DEFAULT_LANG_CODE = os.environ.get("KOKORO_LANG_CODE", "a") # 'a' for American English
DEFAULT_VOICE = os.environ.get("KOKORO_DEFAULT_VOICE", "af_heart")
MODEL_DEVICE = os.environ.get("KOKORO_DEVICE", "cpu") # "cuda" or "mps" if available and configured
SERVER_PORT = int(os.environ.get("PORT", {DEFAULT_PORT})) # Get port from env
SERVER_HOST = os.environ.get("HOST", "127.0.0.1") # Default to localhost

kokoro_pipeline = None

# --- Lifespan Management (Load Model on Startup) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global kokoro_pipeline
    logger.info("Initializing Kokoro TTS pipeline...")
    logger.info(f"Language Code: {{DEFAULT_LANG_CODE}}")
    logger.info(f"Device: {{MODEL_DEVICE}}")
    try:
        # Check for MPS fallback environment variable needed for Apple Silicon
        if MODEL_DEVICE == "mps" and platform.system() == "Darwin":
             os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
             logger.info("Enabled PYTORCH_ENABLE_MPS_FALLBACK for MPS device on Darwin.")

        kokoro_pipeline = KPipeline(lang_code=DEFAULT_LANG_CODE, device=MODEL_DEVICE)
        logger.info("Kokoro TTS pipeline initialized successfully.")
        # Optional: Pre-load a voice or warm up the model
        logger.info(f"Warming up with default voice: {{DEFAULT_VOICE}}...")
        try:
             # Simple warm-up call
             _ = list(kokoro_pipeline("Hello", voice=DEFAULT_VOICE, speed=1.0))
             logger.info("Warm-up complete.")
        except Exception as warmup_err:
             logger.warning(f"Warm-up failed (this might be okay): {{warmup_err}}")

    except Exception as e:
        logger.error(f"FATAL: Failed to initialize Kokoro pipeline: {{e}}", exc_info=True)
        # Optionally raise the error to prevent server start if model load fails
        # raise RuntimeError(f"Failed to initialize Kokoro pipeline: {e}") from e
        kokoro_pipeline = None # Ensure it's None if failed

    yield
    # Clean up resources if needed (though typically not necessary for pipelines)
    logger.info("Kokoro TTS server shutting down.")
    kokoro_pipeline = None
    if MODEL_DEVICE == "cuda":
        torch.cuda.empty_cache() # If using CUDA


app = FastAPI(lifespan=lifespan)

# --- Request Model ---
class TTSRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE
    speed: float = Query(1.0, ge=0.5, le=2.0) # Speed control with validation

# --- API Endpoints ---
@app.get("/health")
async def health_check():
    if kokoro_pipeline is None:
         raise HTTPException(status_code=503, detail="TTS Service Unavailable: Model not loaded.")
    return {{"status": "ok", "message": "Kokoro TTS Server is running."}}

@app.get("/voices")
async def get_voices():
    # Kokoro doesn't have a built-in way to list all voices easily.
    # We'll return a predefined list based on common examples or allow user config.
    # This list might need manual updating based on Kokoro releases.
    # For now, return the default as the only known one.
    # TODO: Explore if kokoro or misaki offers voice listing capabilities.
    return [{{"name": DEFAULT_VOICE, "language": DEFAULT_LANG_CODE, "description": "Default Kokoro Voice (af_heart)"}}]

@app.post("/synthesize", response_class=StreamingResponse)
async def synthesize_speech(request: TTSRequest):
    if kokoro_pipeline is None:
        logger.error("Synthesize request failed: Pipeline not initialized.")
        raise HTTPException(status_code=503, detail="TTS Service Unavailable: Model not loaded.")

    logger.info(f"Received synthesis request for voice '{{request.voice}}' with speed {{request.speed}}")
    logger.debug(f"Text: {{request.text[:100]}}...")

    try:
        # Generate audio chunks using the pipeline
        # Kokoro pipeline yields (graphemes, phonemes, audio_chunk)
        # We only need the audio_chunk
        generator = kokoro_pipeline(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            # split_pattern=r'\n+' # Optional: control sentence splitting
        )

        # Stream the audio data back
        async def audio_streamer():
            buffer = io.BytesIO()
            all_audio_list = [] # Accumulate numpy arrays
            first_chunk = True

            async for i, (gs, ps, audio_chunk) in enumerate(generator):
                # logger.debug(f"Generated chunk {{i}} (length: {{len(audio_chunk)}})")
                if not isinstance(audio_chunk, torch.Tensor) or audio_chunk.numel() == 0:
                    logger.warning(f"Audio chunk {{i}} is not a valid tensor or is empty: {{type(audio_chunk)}}. Skipping.")
                    continue

                # Convert tensor to numpy array (move to CPU if needed)
                if audio_chunk.device != torch.device('cpu'):
                    audio_chunk = audio_chunk.cpu()

                # Ensure float32 for processing, convert to int16 for WAV later
                if audio_chunk.dtype != torch.float32:
                    audio_numpy = audio_chunk.float().numpy()
                else:
                    audio_numpy = audio_chunk.numpy()

                all_audio_list.append(audio_numpy)
                first_chunk = False

            if first_chunk: # Handle case where no audio was generated
                 logger.warning("No audio chunks were generated for the request.")
                 # Return empty WAV or raise error? Let's return empty for now.
                 # Create a minimal valid WAV header for silence
                 samplerate = 24000
                 channels = 1
                 subtype = 'PCM_16'
                 # Write minimal WAV header
                 buffer.write(b'RIFF')
                 buffer.write(b'\x00\x00\x00\x00') # Placeholder for file size
                 buffer.write(b'WAVE')
                 buffer.write(b'fmt ')
                 buffer.write((16).to_bytes(4, 'little')) # Subchunk1Size (16 for PCM)
                 buffer.write((1).to_bytes(2, 'little')) # AudioFormat (1 for PCM)
                 buffer.write(channels.to_bytes(2, 'little')) # NumChannels
                 buffer.write(samplerate.to_bytes(4, 'little')) # SampleRate
                 buffer.write((samplerate * channels * 2).to_bytes(4, 'little')) # ByteRate (SampleRate * NumChannels * BitsPerSample/8)
                 buffer.write((channels * 2).to_bytes(2, 'little')) # BlockAlign (NumChannels * BitsPerSample/8)
                 buffer.write((16).to_bytes(2, 'little')) # BitsPerSample
                 buffer.write(b'data')
                 buffer.write((0).to_bytes(4, 'little')) # Subchunk2Size (data size)
                 # Update file size
                 file_size = buffer.tell() - 8
                 buffer.seek(4)
                 buffer.write(file_size.to_bytes(4, 'little'))
                 buffer.seek(0)
                 yield buffer.read()
                 return

            # Concatenate all numpy arrays
            all_audio = np.concatenate(all_audio_list)
            logger.info(f"Concatenated audio shape: {{all_audio.shape}}, dtype: {{all_audio.dtype}}")

            # Convert to int16 for WAV file
            # Scale float32 audio from [-1.0, 1.0] to int16 [-32768, 32767]
            if all_audio.dtype == np.float32:
                 all_audio = (all_audio * 32767).astype(np.int16)
            elif all_audio.dtype != np.int16:
                 logger.warning(f"Unexpected audio dtype after concat: {{all_audio.dtype}}. Attempting conversion to int16.")
                 all_audio = all_audio.astype(np.int16) # Attempt direct conversion if not float32

            # Now write the accumulated audio to a WAV in memory
            logger.info(f"Writing accumulated audio (shape: {{all_audio.shape}}, dtype: {{all_audio.dtype}}) to WAV buffer.")
            samplerate = 24000 # Kokoro uses 24kHz
            try:
                sf.write(buffer, all_audio, samplerate=samplerate, format='WAV', subtype='PCM_16')
                buffer.seek(0)
                # Yield the entire buffer content
                yield buffer.read()
            except Exception as write_err:
                logger.error(f"Error writing WAV buffer: {{write_err}}", exc_info=True)
                # If writing fails, we can't return audio. Yield empty bytes?
                yield b""


        # Return a streaming response
        # Note: This currently sends the whole file at once after generation.
        # True streaming would involve yielding smaller byte chunks from the buffer
        # or directly yielding raw PCM data with appropriate content-type.
        return StreamingResponse(audio_streamer(), media_type="audio/wav")

    except FileNotFoundError as e:
         # Specific handling for missing voice files
         logger.error(f"Voice file likely not found for '{{request.voice}}': {{e}}", exc_info=True)
         raise HTTPException(status_code=404, detail=f"Voice '{{request.voice}}' not found or invalid.")
    except ValueError as e:
         # Handle potential value errors from kokoro/torch
         logger.error(f"Value error during synthesis: {{e}}", exc_info=True)
         raise HTTPException(status_code=400, detail=f"Invalid input or configuration: {{e}}")
    except Exception as e:
        logger.error(f"Error during speech synthesis: {{e}}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during synthesis: {{str(e)}}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Kokoro TTS server on {{SERVER_HOST}}:{{SERVER_PORT}}...")
    # Use reload=True for development convenience, disable in production
    uvicorn.run("__main__:app", host=SERVER_HOST, port=SERVER_PORT, reload=False) # Use reload=False for setup script

"""
    try:
        with open(server_script_path, "w", encoding="utf-8") as f:
            f.write(server_script_content)
        logger.info(f"Successfully created {CUSTOM_SERVER_SCRIPT_NAME}.")
        return True
    except IOError as e:
        logger.error(f"Failed to write server script {server_script_path}: {e}")
        return False


def create_startup_script(install_dir, port):
    """Create a startup script for the custom Kokoro TTS server."""
    venv_dir = install_dir / "venv"
    server_script_path = install_dir / CUSTOM_SERVER_SCRIPT_NAME
    logger.info("Creating startup script for custom Kokoro server...")
    
    # Determine the script extension based on the OS
    script_ext = ".bat" if platform.system() == "Windows" else ".sh"
    startup_script_path = install_dir / f"start_kokoro_server{script_ext}"

    # Get absolute paths, ensuring correct separators for the target OS in the script
    activate_path = (venv_dir / ("Scripts" if platform.system() == "Windows" else "bin") / "activate").resolve()
    python_exec = (venv_dir / ("Scripts" if platform.system() == "Windows" else "bin") / "python").resolve()
    server_script_abs_path = server_script_path.resolve()
    
    # Create the appropriate script content based on the OS
    if platform.system() == "Windows":
        # Use CALL for activate script, handle paths carefully, use double quotes
        # Set environment variables using SET
        script_content = f"""@echo off
echo Activating virtual environment...
CALL "{activate_path}"
echo Setting environment variables...
SET PORT={port}
SET HOST=127.0.0.1
SET KOKORO_DEVICE={"cuda" if not cpu_only else "cpu"}
echo Starting custom Kokoro TTS server on port %PORT%...
echo Running: "{python_exec}" "{server_script_abs_path}"
"{python_exec}" "{server_script_abs_path}"
echo Server stopped. Press any key to exit.
pause > nul
"""
    else:
        # Use source for activate script, use double quotes
        # Export environment variables
        script_content = f"""#!/bin/bash
echo "Activating virtual environment..."
source "{activate_path}"
echo "Setting environment variables..."
export PORT={port}
export HOST="127.0.0.1"
export KOKORO_DEVICE={"cuda" if not cpu_only else "cpu"}
echo "Starting custom Kokoro TTS server on port $PORT..."
echo "Running: {python_exec} {server_script_abs_path}"
"{python_exec}" "{server_script_abs_path}"
echo "Server stopped."
"""
    
    # Write the script to file
    try:
        with open(startup_script_path, "w", encoding="utf-8", newline='') as f: # Use newline='' for scripts
            f.write(script_content)
    
    # Make the script executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(startup_script_path, 0o755)

        logger.info(f"Created startup script at {startup_script_path}")
        return startup_script_path
    except IOError as e:
        logger.error(f"Failed to write startup script {startup_script_path}: {e}")
        return None


def update_env_file(port):
    """Update the .env file for the main backend application."""
    # Find .env in backend or project root
    backend_dir = Path(__file__).parent.resolve() # Assumes setup script is in backend/
    project_root = backend_dir.parent.resolve()

    env_paths = [
        backend_dir / ".env",  # Backend directory first
        project_root / ".env"  # Project root as fallback
    ]

    env_file_to_update = None
    for path in env_paths:
        if path.is_file(): # Check if it's a file
            env_file_to_update = path
            logger.info(f"Found existing .env file at: {env_file_to_update}")
            break

    if not env_file_to_update:
        # Default to creating in backend/ if none found
        env_file_to_update = backend_dir / ".env"
        logger.info(f"No existing .env file found in search paths. Will create/update {env_file_to_update}")

    # Read existing content or initialize if creating new
    env_lines = []
    if env_file_to_update.exists():
        try:
            with open(env_file_to_update, "r", encoding="utf-8") as f:
                env_lines = f.read().splitlines()
        except IOError as e:
            logger.error(f"Could not read existing .env file at {env_file_to_update}: {e}")
            # Proceed to create/overwrite

    key_to_set = "KOKORO_API_URL"
    value_to_set = f"http://127.0.0.1:{port}" # Use 127.0.0.1 explicitly
    key_line = f"{key_to_set}={value_to_set}"

    updated_lines = []
    key_found = False
    for line in env_lines:
        stripped_line = line.strip()
        if stripped_line.startswith("#"): # Keep comments
            updated_lines.append(line)
        elif "=" in stripped_line:
            parts = stripped_line.split("=", 1)
            current_key = parts[0].strip()
            if current_key == key_to_set:
                updated_lines.append(key_line) # Replace with new value
                key_found = True
                logger.info(f"Updating existing {key_to_set} in {env_file_to_update}")
            else:
                updated_lines.append(line) # Keep other keys
        else:
             updated_lines.append(line) # Keep lines without '=' (e.g., blank lines)


    if not key_found:
        # Add header if it's a new file or the key wasn't found
        if not updated_lines or key_found==False: # Add header if file was empty or key not found
            updated_lines.append("# TTS Configuration")
        updated_lines.append(key_line)
        logger.info(f"Adding {key_to_set} to {env_file_to_update}")

    # Write the updated content back
    try:
        with open(env_file_to_update, "w", encoding="utf-8") as f:
            f.write("".join(updated_lines) + "") # Ensure final newline
        logger.info(f"Successfully wrote/updated {env_file_to_update}")
    except IOError as e:
        logger.error(f"Failed to write to {env_file_to_update}: {e}")


def main():
    """Main function."""
    global cpu_only # Make cpu_only accessible in create_startup_script implicitly
    parser = argparse.ArgumentParser(description="Setup script for Kokoro TTS Server.")
    parser.add_argument("--install-dir", type=Path, default=DEFAULT_INSTALL_DIR,
                      help=f"Base directory for installation (venv, server script will be here) (default: {DEFAULT_INSTALL_DIR})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                      help=f"Port for the Kokoro TTS server (default: {DEFAULT_PORT})")
    parser.add_argument("--gpu", action="store_true",
                      help="Attempt GPU setup (requires manual PyTorch install with CUDA/MPS and sets KOKORO_DEVICE=cuda)")
    args = parser.parse_args()
    
    logger.info("Starting Kokoro TTS Server setup...")
    install_dir = args.install_dir.resolve() # Use absolute path
    install_dir.mkdir(parents=True, exist_ok=True) # Ensure base install dir exists
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisite check failed. Please address the issues above.")
        # sys.exit(1) # Allow continuing but warn

    # Clone/Update the official Kokoro repository (optional but good for reference/future)
    # Note: We are not installing FROM the repo directly anymore
    # if not clone_repository(install_dir):
    #     logger.warning("Failed to clone/update official Kokoro repository. Continuing setup...")
        # sys.exit(1) # Decide if cloning is critical

    # Install dependencies in venv
    cpu_only = not args.gpu
    if not install_dependencies(install_dir, cpu_only):
        logger.error("Dependency installation failed.")
        sys.exit(1)
    
    # Ensure the custom FastAPI server script exists
    if not ensure_custom_server_script(install_dir):
        logger.error("Failed to create custom server script.")
        sys.exit(1)
    
    # Create startup script for the custom server
    script_path = create_startup_script(install_dir, args.port) # Pass cpu_only implicitly via global
    if not script_path:
        logger.error("Failed to create startup script.")
        sys.exit(1)
    
    logger.info("Kokoro TTS Server setup partially completed!")
    logger.warning("Please ensure 'espeak-ng' is correctly installed and in your PATH if you haven't already.")
    logger.info(f"To start the server, navigate to '{install_dir}' and run: {script_path.name}")
    logger.info(f"The server should be available at: http://127.0.0.1:{args.port}") # Use 127.0.0.1

    # Update the .env file for the main backend application
    update_env_file(args.port)

    logger.info("Setup finished.")


if __name__ == "__main__":
    # Define cpu_only globally based on args BEFORE calling functions that might use it
    # This is a bit hacky, passing explicitly would be better, but simplifies setup flow for now
    parser = argparse.ArgumentParser(add_help=False) # Temporary parser to get args
    parser.add_argument("--gpu", action="store_true")
    known_args, _ = parser.parse_known_args()
    cpu_only = not known_args.gpu

    main() 