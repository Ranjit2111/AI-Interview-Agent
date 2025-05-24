"""
File validation utilities for secure file processing.
"""

import os
import logging
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

from backend.config.file_processing_config import (
    MAX_FILE_SIZE, MAX_TEXT_CONTENT_LENGTH, MIN_TEXT_LENGTH, MAX_FILENAME_LENGTH,
    ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS, ERROR_MESSAGES
)


class FileValidator:
    """Handles file validation for security and compliance."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def validate_upload(self, file: UploadFile) -> None:
        """
        Comprehensive validation of uploaded file.
        
        Args:
            file: The uploaded file to validate
            
        Raises:
            HTTPException: If validation fails
        """
        self._validate_filename(file.filename)
        self._validate_content_type(file.content_type)
        self._validate_file_extension(file.filename)
    
    async def validate_file_size(self, file: UploadFile) -> bytes:
        """
        Validate file size and return content bytes.
        
        Args:
            file: The uploaded file
            
        Returns:
            File content as bytes
            
        Raises:
            HTTPException: If file is too large
        """
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            self.logger.warning(f"File {file.filename} exceeds size limit: {len(content)} bytes")
            raise HTTPException(
                status_code=413,
                detail=ERROR_MESSAGES["file_too_large"]
            )
        
        self.logger.debug(f"File {file.filename} size validated: {len(content)} bytes")
        return content
    
    def validate_extracted_text(self, text: str, filename: str) -> str:
        """
        Validate extracted text content.
        
        Args:
            text: Extracted text content
            filename: Original filename for logging
            
        Returns:
            Validated text content
            
        Raises:
            HTTPException: If text content is invalid
        """
        # Check if text is too large
        text_size = len(text.encode('utf-8'))
        if text_size > MAX_TEXT_CONTENT_LENGTH:
            self.logger.warning(f"Extracted text from {filename} exceeds size limit: {text_size} bytes")
            raise HTTPException(
                status_code=413,
                detail=ERROR_MESSAGES["text_too_large"]
            )
        
        # Check if text is too short or empty
        clean_text = text.strip()
        if len(clean_text) < MIN_TEXT_LENGTH:
            self.logger.warning(f"Extracted text from {filename} is too short: {len(clean_text)} characters")
            raise HTTPException(
                status_code=400,
                detail=ERROR_MESSAGES["empty_content"]
            )
        
        self.logger.debug(f"Text content from {filename} validated: {len(clean_text)} characters")
        return clean_text
    
    def _validate_filename(self, filename: Optional[str]) -> None:
        """Validate filename security and length."""
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        if len(filename) > MAX_FILENAME_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=ERROR_MESSAGES["invalid_filename"]
            )
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            self.logger.warning(f"Suspicious filename detected: {filename}")
            raise HTTPException(
                status_code=400,
                detail="Invalid filename. Please use a simple filename without paths."
            )
    
    def _validate_content_type(self, content_type: Optional[str]) -> None:
        """Validate file content type."""
        if not content_type or content_type not in ALLOWED_CONTENT_TYPES:
            self.logger.warning(f"Unsupported content type: {content_type}")
            raise HTTPException(
                status_code=400,
                detail=ERROR_MESSAGES["unsupported_type"]
            )
    
    def _validate_file_extension(self, filename: Optional[str]) -> None:
        """Validate file extension."""
        if not filename:
            return
        
        _, extension = os.path.splitext(filename.lower())
        if extension not in ALLOWED_EXTENSIONS:
            self.logger.warning(f"Unsupported file extension: {extension} for file {filename}")
            raise HTTPException(
                status_code=400,
                detail=ERROR_MESSAGES["unsupported_type"]
            )
    
    def get_safe_filename(self, filename: str) -> str:
        """
        Generate a safe filename for storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components and dangerous characters
        safe_name = os.path.basename(filename)
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '.-_')
        
        # Ensure it's not too long
        if len(safe_name) > MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:MAX_FILENAME_LENGTH - len(ext)] + ext
        
        return safe_name


def create_file_validator(logger: Optional[logging.Logger] = None) -> FileValidator:
    """Create a FileValidator instance."""
    return FileValidator(logger) 