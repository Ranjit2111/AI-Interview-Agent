"""
AI Interviewer Agent - Local Backend
This application provides interview preparation services that run locally.
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


# API key handling
load_dotenv()
api_key = os.environ.get('API_KEY')
if not api_key:
    print("WARNING: No API key found. Please set the API_KEY environment variable.")
    api_key = "MISSING_API_KEY"

# Create temp directory if it doesn't exist
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize services
service_provider = initialize_services({
    "log_level": logging.INFO,
    "api_key": api_key
})

# Initialize database
init_db()

# Create API app
app = create_app()

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Interviewer Agent API (Local Version)"}

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
async def generate_api_docs():
    """Generate API documentation when the application starts."""
    docs_dir = os.path.join(os.getcwd(), "..", "docs", "api")
    try:
        generate_static_docs(app, docs_dir)
        print(f"API documentation generated in {os.path.join(docs_dir, 'api_docs')}")
    except Exception as e:
        print(f"Error generating API documentation: {str(e)}")

# Run the application with uvicorn when the script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 