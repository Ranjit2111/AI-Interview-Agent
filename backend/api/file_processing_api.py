import logging
import io
from typing import Dict

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from backend.config import get_logger
from backend.utils.file_utils import extract_text_from_pdf, extract_text_from_docx
from backend.utils.file_validator import create_file_validator
from backend.config.file_processing_config import ERROR_MESSAGES

logger = get_logger(__name__)

class ResumeUploadResponse(BaseModel):
    filename: str
    resume_text: str
    message: str

def create_file_processing_api(app):
    router = APIRouter(prefix="/files", tags=["File Processing"])
    file_validator = create_file_validator(logger)

    @router.post("/upload-resume", response_model=ResumeUploadResponse)
    async def upload_resume(file: UploadFile = File(...)):
        """
        Uploads a resume file (PDF or DOCX) and extracts text content.
        Includes security validations for file size, type, and content.
        """
        logger.info(f"Received resume upload request for file: {file.filename}, type: {file.content_type}")    
        
        try:
            # Security validations
            file_validator.validate_upload(file)
            file_content_bytes = await file_validator.validate_file_size(file)
            
            # Extract text based on file type
            extracted_text = await _extract_text_by_type(file, file_content_bytes)
            
            # Validate extracted text
            validated_text = file_validator.validate_extracted_text(extracted_text, file.filename)
            
            logger.info(f"Successfully processed file: {file.filename}")
            return ResumeUploadResponse(
                filename=file.filename or "unknown_file",
                resume_text=validated_text,
                message="File processed successfully."
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions (from validators)
            raise
        except ValueError as ve:
            logger.error(f"ValueError during text extraction for {file.filename}: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.exception(f"Unexpected error processing file {file.filename}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=ERROR_MESSAGES["processing_failed"]
            )

    async def _extract_text_by_type(file: UploadFile, file_content_bytes: bytes) -> str:
        """Extract text based on file content type."""
        file_stream = io.BytesIO(file_content_bytes)
        
        try:
            if file.content_type == "application/pdf":
                extracted_text = extract_text_from_pdf(file_stream)
                logger.debug(f"Successfully extracted text from PDF: {file.filename}")
            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                extracted_text = extract_text_from_docx(file_stream)
                logger.debug(f"Successfully extracted text from DOCX: {file.filename}")
            elif file.content_type == "text/plain":
                extracted_text = file_content_bytes.decode('utf-8')
                logger.debug(f"Successfully read text from TXT: {file.filename}")
            else:
                # This should not happen due to validation, but added for safety
                logger.error(f"Unsupported file type reached processing: {file.content_type}")
                raise HTTPException(
                    status_code=400,
                    detail=ERROR_MESSAGES["unsupported_type"]
                )
            
            return extracted_text
            
        finally:
            file_stream.close()

    app.include_router(router)
    logger.info("File Processing API router registered with prefix /files") 