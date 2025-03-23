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
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np
import scipy.io.wavfile as wav
import fitz  # PyMuPDF
import docx
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from backend.api import create_app
from backend.database.connection import init_db
from backend.services import initialize_services
from backend.utils.docs_generator import generate_static_docs
from backend.api.agent_api import create_agent_api
from backend.api.resource_api import create_resource_api
from backend.api.transcript_api import router as transcript_router


# Load environment variables
load_dotenv()

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AI Interviewer Agent",
    description="AI-powered interview practice and coaching system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import API routes
from backend.api.agent_api import create_agent_api
from backend.api.resource_api import create_resource_api
from backend.services import initialize_services

# Initialize services
service_provider = initialize_services()
logger.info("Services initialized")

# Create API routes
create_agent_api(app)
create_resource_api(app)
# Register transcript API routes
app.include_router(transcript_router, prefix="/api/transcripts", tags=["transcripts"])
logger.info("API routes registered")

# Mount static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.post("/submit-context", response_model=ContextResponse)
async def submit_context(
    job_role: str = Form(...),
    job_description: str = Form(...),
    resume_file: UploadFile = File(None)
):
    try:
        resume_text = ""
        
        if resume_file:
            file_path = os.path.join(TEMP_DIR, resume_file.filename)
            
            # Save the uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(resume_file.file, buffer)
            
            if file_path.endswith('.pdf'):
                # Use PyMuPDF for PDF processing
                pdf_document = fitz.open(file_path)
                resume_text = " ".join([page.get_text() for page in pdf_document])
            elif file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                resume_text = " ".join([para.text for para in doc.paragraphs])
            else:
                raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are allowed.")
            
            # Clean up the temporary file
            os.unlink(file_path)
        
        return ContextResponse(
            message=f"Successfully processed context. Job Role: {job_role}, Resume length: {len(resume_text)} characters"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/generate-interview", response_model=InterviewResponse)
async def generate_interview(request: InterviewRequest):
    if api_key == "MISSING_API_KEY":
        raise HTTPException(status_code=500, detail="No valid API key found. Please set the API_KEY environment variable.")
        
    try:
        # Generate the adaptive prompt using the chain
        adaptive_prompt = chain.invoke({
            "user_input": request.user_input, 
            "job_role": request.job_role, 
            "job_description": request.job_description
        })
        return InterviewResponse(generated_text=adaptive_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating interview question: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize services when the application starts."""
    # Initialize database
    init_db()
    
    # Initialize services
    global service_provider
    service_provider = initialize_services()
    
    # Generate API documentation
    docs_dir = os.path.join(os.getcwd(), "..", "docs", "api")
    try:
        generate_static_docs(app, docs_dir)
        logger.info(f"API documentation generated in {docs_dir}")
    except Exception as e:
        logger.error(f"Error generating API documentation: {str(e)}")
    
    logger.info("Application startup complete")

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True) 