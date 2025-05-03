"""
Main application entry point for the AI Interviewer Agent.
Initializes the FastAPI application and routes.
"""

import os
import logging
import shutil
import tempfile
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Pydantic imports
from pydantic import BaseModel, Field

# Third-party imports
import numpy as np
import scipy.io.wavfile as wav
import fitz  # PyMuPDF
import docx
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Local imports
from backend.services import initialize_services, get_agent_session_manager
from backend.utils.docs_generator import generate_static_docs
from backend.api.agent_api import create_agent_api


# Define Pydantic models for API responses
class AudioResponse(BaseModel):
    """Response model for audio processing."""
    audio_url: str = Field(..., description="URL to the processed audio file")
    transcription: str = Field(..., description="Transcription of the audio")
    
    class Config:
        try:
            # Pydantic v1 compatibility
            orm_mode = True
        except:
            # Pydantic v2 compatibility
            from_attributes = True

class ContextResponse(BaseModel):
    """Response model for context submission."""
    message: str = Field(..., description="Status message")
    
    class Config:
        try:
            # Pydantic v1 compatibility
            orm_mode = True
        except:
            # Pydantic v2 compatibility
            from_attributes = True

class InterviewRequest(BaseModel):
    """Request model for generating interview questions."""
    user_input: str = Field(..., description="User's input or context")
    job_role: str = Field(..., description="Target job role")
    job_description: Optional[str] = Field("", description="Job description")
    
    class Config:
        try:
            # Pydantic v1 compatibility
            orm_mode = True
        except:
            # Pydantic v2 compatibility
            from_attributes = True

class InterviewResponse(BaseModel):
    """Response model for generated interview content."""
    generated_text: str = Field(..., description="Generated interview content")
    
    class Config:
        try:
            # Pydantic v1 compatibility
            orm_mode = True
        except:
            # Pydantic v2 compatibility
            from_attributes = True

# Load environment variables
load_dotenv()

# --- Logging Configuration ---
# Configure logging ONCE here for the entire application
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Define log format
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Get root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Remove existing handlers (if any) to avoid duplicates if app reloads
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# Create formatter
formatter = logging.Formatter(log_format)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Optionally add a file handler (example)
# log_dir = Path("logs")
# log_dir.mkdir(exist_ok=True)
# file_handler = logging.FileHandler(log_dir / f"app-{datetime.now().strftime('%Y%m%d')}.log")
# file_handler.setFormatter(formatter)
# root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__) # Get logger for this module
logger.info(f"Logging configured with level: {log_level_str}")
# --- End Logging Configuration ---

# Create FastAPI application
app = FastAPI(
    title="AI Interviewer Agent",
    description="AI-powered interview practice and coaching system",
    version="0.1.0",
)

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exception with traceback
    logger.exception(f"Unhandled exception during request processing for {request.url.path}: {exc}")
    # Return a generic 500 response
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {exc}"}, # Include exc details for debugging
    )
# --- End Global Exception Handler ---

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
service_provider = initialize_services()
logger.info("Services initialized")

# Create API routes
create_agent_api(app)
logger.info("API routes registered")

# Mount static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Define temporary directory for file uploads
TEMP_DIR = tempfile.gettempdir()

# Initialize API key for Gemini
api_key = os.environ.get("GOOGLE_API_KEY", "MISSING_API_KEY")

# Create LLM chain for interview question generation
def setup_llm_chain():
    """Set up the LLM chain for interview question generation."""
    if api_key != "MISSING_API_KEY":
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key, temperature=0.7)
        prompt = PromptTemplate.from_template(
            """You are an AI interview coach helping prepare for job interviews.
            Generate a relevant interview question for a {job_role} position.
            
            Additional context from the job description: {job_description}
            
            User input: {user_input}
            
            Give me a challenging but realistic interview question based on this information.
            """
        )
        chain = (
            {"user_input": RunnablePassthrough(), 
             "job_role": RunnablePassthrough(), 
             "job_description": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return chain
    return None

# Setup the chain
chain = setup_llm_chain()

# Define helper functions
def transcribe_audio(audio_path):
    """Transcribe audio file using local processing."""
    # This is a stub implementation - in production, use a proper STT service
    return "This is a placeholder transcription. In production, use a proper speech-to-text service."

def synthesize_speech(text, output_path):
    """Synthesize speech from text."""
    # This is a stub implementation - in production, use a proper TTS service
    sample_rate = 22050
    silence = np.zeros(int(sample_rate * 3))  # 3 seconds of silence
    wav.write(output_path, sample_rate, silence.astype(np.int16))

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "ok",
        "message": "AI Interviewer Agent is running"
    }

@app.post("/process-audio", response_model=AudioResponse)
async def process_audio(audio_file: UploadFile = File(...)):
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    audio_path = None
    try:
        # Create temporary files
        audio_path = os.path.join(TEMP_DIR, f"input_{uuid.uuid4()}.wav")
        output_path = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.wav")
        
        # Save the input audio
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Transcribe the audio
        transcription = transcribe_audio(audio_path)
        
        # Generate a response
        response_text = f"I heard: {transcription}. How can I help you with your interview preparation?"
        
        # Synthesize speech for the response
        synthesize_speech(response_text, output_path)
        
        # Return the audio file path
        return {"audio_url": f"/audio/{os.path.basename(output_path)}", "transcription": transcription}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    
    finally:
        # Clean up input temporary file
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except:
                pass

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files from the temporary directory."""
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path)

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Application startup...")
    # Remove database initialization
    # try:
    #     init_db()
    # except Exception as e:
    #     logger.error(f"Database initialization failed: {e}")

    # Initialize services using the refactored function
    try:
        initialize_services() # This should now create the singletons
        # Store the single AgentSessionManager on app state
        app.state.agent_manager = get_agent_session_manager()
        logger.info("AgentSessionManager attached to app state.")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        # Decide how to handle critical service failure (e.g., exit?)

    # Optional: Generate static docs on startup
    # try:
    #     docs_dir = Path("docs/api")
    #     docs_dir.mkdir(parents=True, exist_ok=True)
    #     generate_static_docs(app, "docs/api")
    # except Exception as e:
    #     logger.error(f"Static documentation generation failed: {e}")

    logger.info("Application startup completed.")

logger.info("Application setup complete. Waiting for Uvicorn server start...")

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True) 