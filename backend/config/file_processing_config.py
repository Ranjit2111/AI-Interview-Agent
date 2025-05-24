"""
File processing configuration.
Contains file size limits, allowed types, and security settings.
"""

from typing import Set

# File size limits (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TEXT_CONTENT_LENGTH = 1000 * 1024  # 1 MB for extracted text

# Allowed file types and extensions
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx", 
    ".txt"
}

# Content validation rules
MIN_TEXT_LENGTH = 10  # Minimum characters for meaningful content
MAX_FILENAME_LENGTH = 255  # Maximum filename length

# Security settings
ENABLE_VIRUS_SCAN = False  # Set to True if virus scanning is available
QUARANTINE_SUSPICIOUS_FILES = True

# Error messages
ERROR_MESSAGES = {
    "file_too_large": f"File size exceeds the maximum limit of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
    "unsupported_type": "Unsupported file type. Please upload a PDF, DOCX, or TXT file.",
    "empty_content": "The uploaded file appears to be empty or contains no readable text.",
    "invalid_filename": f"Filename is too long. Maximum length is {MAX_FILENAME_LENGTH} characters.",
    "text_too_large": f"Extracted text exceeds the maximum limit of {MAX_TEXT_CONTENT_LENGTH // 1024} KB.",
    "processing_failed": "Failed to process the uploaded file. Please try again with a different file."
}

# Rate limiting settings (requests per minute per IP)
UPLOAD_RATE_LIMIT = 10  # Maximum uploads per minute per IP address 