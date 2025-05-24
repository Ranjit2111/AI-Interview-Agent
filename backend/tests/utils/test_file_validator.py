"""
Tests for file_validator module.
Tests the FileValidator class that provides security validation for file uploads.
"""

import pytest
import logging
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, UploadFile
from backend.utils.file_validator import FileValidator
from backend.config.file_processing_config import (
    MAX_FILE_SIZE, MAX_TEXT_CONTENT_LENGTH, MIN_TEXT_LENGTH, MAX_FILENAME_LENGTH,
    ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS
)


class TestFileValidator:
    """Test the FileValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = Mock(spec=logging.Logger)
        self.validator = FileValidator(self.logger)
    
    def test_validator_initialization(self):
        """Test FileValidator initialization."""
        # Test with provided logger
        validator = FileValidator(self.logger)
        assert validator.logger == self.logger
        
        # Test with default logger
        validator_default = FileValidator()
        assert validator_default.logger is not None
    
    def test_validate_upload_success(self):
        """Test successful file upload validation."""
        # Mock valid upload file
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        
        # Should not raise exception
        self.validator.validate_upload(mock_file)
    
    def test_validate_upload_no_filename(self):
        """Test validation failure with no filename."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        mock_file.content_type = "application/pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_upload(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Filename is required" in str(exc_info.value.detail)
    
    def test_validate_upload_filename_too_long(self):
        """Test validation failure with filename too long."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "a" * (MAX_FILENAME_LENGTH + 1) + ".pdf"
        mock_file.content_type = "application/pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_upload(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "too long" in str(exc_info.value.detail)
    
    def test_validate_upload_path_traversal(self):
        """Test validation failure with path traversal attempt."""
        test_cases = ["../test.pdf", "dir/test.pdf", "dir\\test.pdf", "..\\test.pdf"]
        
        for dangerous_filename in test_cases:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = dangerous_filename
            mock_file.content_type = "application/pdf"
            
            with pytest.raises(HTTPException) as exc_info:
                self.validator.validate_upload(mock_file)
            
            assert exc_info.value.status_code == 400
            assert "Invalid filename" in str(exc_info.value.detail)
    
    def test_validate_upload_unsupported_content_type(self):
        """Test validation failure with unsupported content type."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_upload(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)
    
    def test_validate_upload_unsupported_extension(self):
        """Test validation failure with unsupported file extension."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "application/pdf"  # Valid content type but wrong extension
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_upload(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_file_size_success(self):
        """Test successful file size validation."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        test_content = b"valid file content"
        mock_file.read = AsyncMock(return_value=test_content)
        
        result = await self.validator.validate_file_size(mock_file)
        assert result == test_content
        mock_file.read.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_file_size_too_large(self):
        """Test file size validation failure."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "large.pdf"
        # Create content larger than MAX_FILE_SIZE
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        mock_file.read = AsyncMock(return_value=large_content)
        
        with pytest.raises(HTTPException) as exc_info:
            await self.validator.validate_file_size(mock_file)
        
        assert exc_info.value.status_code == 413
        assert "exceeds the maximum limit" in str(exc_info.value.detail)
    
    def test_validate_extracted_text_success(self):
        """Test successful text content validation."""
        valid_text = "This is a valid text content that meets minimum length requirements."
        filename = "test.pdf"
        
        result = self.validator.validate_extracted_text(valid_text, filename)
        assert result == valid_text.strip()
    
    def test_validate_extracted_text_too_short(self):
        """Test text validation failure with too short content."""
        short_text = "short"  # Less than MIN_TEXT_LENGTH
        filename = "test.pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_extracted_text(short_text, filename)
        
        assert exc_info.value.status_code == 400
        assert "too short" in str(exc_info.value.detail)
    
    def test_validate_extracted_text_too_large(self):
        """Test text validation failure with content too large."""
        # Create text larger than MAX_TEXT_CONTENT_LENGTH
        large_text = "x" * (MAX_TEXT_CONTENT_LENGTH + 1)
        filename = "test.pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_extracted_text(large_text, filename)
        
        assert exc_info.value.status_code == 413
        assert "exceeds the maximum limit" in str(exc_info.value.detail)
    
    def test_validate_extracted_text_empty_after_strip(self):
        """Test text validation failure with empty content after stripping."""
        empty_text = "   \n\t   "  # Only whitespace
        filename = "test.pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            self.validator.validate_extracted_text(empty_text, filename)
        
        assert exc_info.value.status_code == 400
        assert "too short" in str(exc_info.value.detail)
    
    def test_get_safe_filename_basic(self):
        """Test basic safe filename generation."""
        original = "test document.pdf"
        safe = self.validator.get_safe_filename(original)
        assert safe == "test document.pdf"
    
    def test_get_safe_filename_remove_dangerous_chars(self):
        """Test safe filename generation removes dangerous characters."""
        original = "test<>:|?*file.pdf"
        safe = self.validator.get_safe_filename(original)
        # Should only contain alphanumeric and allowed characters
        assert all(c.isalnum() or c in '.-_' for c in safe)
        assert safe.endswith(".pdf")
    
    def test_get_safe_filename_path_removal(self):
        """Test safe filename generation removes path components."""
        original = "/path/to/file.pdf"
        safe = self.validator.get_safe_filename(original)
        assert safe == "file.pdf"
        
        original_windows = "C:\\path\\to\\file.pdf"
        safe_windows = self.validator.get_safe_filename(original_windows)
        assert safe_windows == "file.pdf"
    
    def test_get_safe_filename_length_truncation(self):
        """Test safe filename generation truncates long names."""
        # Create a filename longer than MAX_FILENAME_LENGTH
        long_name = "a" * (MAX_FILENAME_LENGTH + 10) + ".pdf"
        safe = self.validator.get_safe_filename(long_name)
        
        assert len(safe) <= MAX_FILENAME_LENGTH
        assert safe.endswith(".pdf")
    
    def test_validate_content_type_edge_cases(self):
        """Test content type validation edge cases."""
        # Test None content type
        with pytest.raises(HTTPException):
            self.validator._validate_content_type(None)
        
        # Test empty content type
        with pytest.raises(HTTPException):
            self.validator._validate_content_type("")
        
        # Test valid content types
        for content_type in ALLOWED_CONTENT_TYPES:
            self.validator._validate_content_type(content_type)  # Should not raise
    
    def test_validate_file_extension_edge_cases(self):
        """Test file extension validation edge cases."""
        # Test None filename
        self.validator._validate_file_extension(None)  # Should not raise
        
        # Test empty filename
        self.validator._validate_file_extension("")  # Should not raise
        
        # Test valid extensions
        for ext in ALLOWED_EXTENSIONS:
            filename = f"test{ext}"
            self.validator._validate_file_extension(filename)  # Should not raise
        
        # Test case insensitivity
        self.validator._validate_file_extension("test.PDF")  # Should not raise
        self.validator._validate_file_extension("test.TXT")  # Should not raise
    
    def test_logging_behavior(self):
        """Test that appropriate logging occurs."""
        # Test warning for suspicious filename
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "../suspicious.pdf"
        mock_file.content_type = "application/pdf"
        
        with pytest.raises(HTTPException):
            self.validator.validate_upload(mock_file)
        
        self.logger.warning.assert_called()
    
    def test_configuration_integration(self):
        """Test integration with configuration constants."""
        # Verify validator uses the correct configuration values
        assert MAX_FILE_SIZE > 0
        assert MAX_TEXT_CONTENT_LENGTH > 0
        assert MIN_TEXT_LENGTH > 0
        assert MAX_FILENAME_LENGTH > 0
        assert len(ALLOWED_CONTENT_TYPES) > 0
        assert len(ALLOWED_EXTENSIONS) > 0 