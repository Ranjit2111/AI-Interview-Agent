import logging
import io
from typing import Dict

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from backend.config import get_logger
from backend.utils.file_utils import extract_text_from_pdf, extract_text_from_docx

logger = get_logger(__name__)

class ResumeUploadResponse(BaseModel):
    filename: str
    resume_text: str
    message: str

def create_file_processing_api(app):
    router = APIRouter(prefix="/files", tags=["File Processing"])

    @router.post("/upload-resume", response_model=ResumeUploadResponse)
    async def upload_resume(file: UploadFile = File(...)):
        """
        Uploads a resume file (PDF or DOCX) and extracts text content.
        """
        logger.info(f"Received resume upload request for file: {file.filename}, type: {file.content_type}")    
        
        extracted_text = ""
        file_content_bytes = await file.read() # Read file content as bytes
        file_stream = io.BytesIO(file_content_bytes)

        try:
            if file.content_type == "application/pdf":
                extracted_text = extract_text_from_pdf(file_stream)
                logger.info(f"Successfully extracted text from PDF: {file.filename}")
            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                extracted_text = extract_text_from_docx(file_stream)
                logger.info(f"Successfully extracted text from DOCX: {file.filename}")
            elif file.content_type == "text/plain":
                extracted_text = file_content_bytes.decode('utf-8') # For .txt files
                logger.info(f"Successfully read text from TXT: {file.filename}")
            else:
                logger.warning(f"Unsupported file type: {file.content_type} for file {file.filename}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file.content_type}. Please upload a PDF, DOCX, or TXT file."
                )
            
            if not extracted_text.strip():
                logger.warning(f"Extracted text is empty for file: {file.filename}")
                return ResumeUploadResponse(
                    filename=file.filename or "unknown_file",
                    resume_text="",
                    message="Extracted text is empty or file could not be read properly."
                )

            return ResumeUploadResponse(
                filename=file.filename or "unknown_file",
                resume_text=extracted_text,
                message="File processed successfully."
            )
        except ValueError as ve:
            logger.error(f"ValueError during text extraction for {file.filename}: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.exception(f"Unexpected error processing file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing the file: {e}")
        finally:
            file_stream.close()

    app.include_router(router)
    logger.info("File Processing API router registered with prefix /files") 