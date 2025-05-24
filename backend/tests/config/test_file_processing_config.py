"""
Tests for file_processing_config module.
Tests the configuration constants and settings for file processing.
"""

import pytest
from backend.config.file_processing_config import (
    MAX_FILE_SIZE, MAX_TEXT_CONTENT_LENGTH, MIN_TEXT_LENGTH, MAX_FILENAME_LENGTH,
    ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS,
    ENABLE_VIRUS_SCAN, QUARANTINE_SUSPICIOUS_FILES,
    ERROR_MESSAGES, UPLOAD_RATE_LIMIT
)


class TestFileSizeLimits:
    """Test file size limit configurations."""
    
    def test_max_file_size_is_reasonable(self):
        """Test MAX_FILE_SIZE is set to a reasonable value."""
        assert MAX_FILE_SIZE > 0
        assert MAX_FILE_SIZE == 10 * 1024 * 1024  # 10 MB
        assert isinstance(MAX_FILE_SIZE, int)
    
    def test_max_text_content_length_is_reasonable(self):
        """Test MAX_TEXT_CONTENT_LENGTH is set to a reasonable value."""
        assert MAX_TEXT_CONTENT_LENGTH > 0
        assert MAX_TEXT_CONTENT_LENGTH == 1000 * 1024  # 1 MB
        assert isinstance(MAX_TEXT_CONTENT_LENGTH, int)
        assert MAX_TEXT_CONTENT_LENGTH <= MAX_FILE_SIZE  # Text should be smaller than file
    
    def test_min_text_length_is_reasonable(self):
        """Test MIN_TEXT_LENGTH is set to a reasonable value."""
        assert MIN_TEXT_LENGTH > 0
        assert MIN_TEXT_LENGTH == 10
        assert isinstance(MIN_TEXT_LENGTH, int)
        assert MIN_TEXT_LENGTH < MAX_TEXT_CONTENT_LENGTH
    
    def test_max_filename_length_is_reasonable(self):
        """Test MAX_FILENAME_LENGTH is set to a reasonable value."""
        assert MAX_FILENAME_LENGTH > 0
        assert MAX_FILENAME_LENGTH == 255
        assert isinstance(MAX_FILENAME_LENGTH, int)


class TestAllowedFileTypes:
    """Test allowed file type configurations."""
    
    def test_allowed_content_types_structure(self):
        """Test ALLOWED_CONTENT_TYPES is properly configured."""
        assert isinstance(ALLOWED_CONTENT_TYPES, set)
        assert len(ALLOWED_CONTENT_TYPES) > 0
    
    def test_allowed_content_types_content(self):
        """Test ALLOWED_CONTENT_TYPES contains expected types."""
        expected_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        }
        assert expected_types.issubset(ALLOWED_CONTENT_TYPES)
    
    def test_allowed_extensions_structure(self):
        """Test ALLOWED_EXTENSIONS is properly configured."""
        assert isinstance(ALLOWED_EXTENSIONS, set)
        assert len(ALLOWED_EXTENSIONS) > 0
    
    def test_allowed_extensions_content(self):
        """Test ALLOWED_EXTENSIONS contains expected extensions."""
        expected_extensions = {".pdf", ".docx", ".txt"}
        assert expected_extensions.issubset(ALLOWED_EXTENSIONS)
    
    def test_extensions_start_with_dot(self):
        """Test all extensions start with a dot."""
        for ext in ALLOWED_EXTENSIONS:
            assert ext.startswith(".")
            assert len(ext) > 1  # More than just the dot


class TestSecuritySettings:
    """Test security setting configurations."""
    
    def test_virus_scan_setting(self):
        """Test ENABLE_VIRUS_SCAN is properly configured."""
        assert isinstance(ENABLE_VIRUS_SCAN, bool)
        # Currently expected to be False
        assert ENABLE_VIRUS_SCAN is False
    
    def test_quarantine_setting(self):
        """Test QUARANTINE_SUSPICIOUS_FILES is properly configured."""
        assert isinstance(QUARANTINE_SUSPICIOUS_FILES, bool)
        assert QUARANTINE_SUSPICIOUS_FILES is True
    
    def test_upload_rate_limit(self):
        """Test UPLOAD_RATE_LIMIT is properly configured."""
        assert isinstance(UPLOAD_RATE_LIMIT, int)
        assert UPLOAD_RATE_LIMIT > 0
        assert UPLOAD_RATE_LIMIT == 10  # 10 uploads per minute


class TestErrorMessages:
    """Test error message configurations."""
    
    def test_error_messages_structure(self):
        """Test ERROR_MESSAGES is properly configured."""
        assert isinstance(ERROR_MESSAGES, dict)
        assert len(ERROR_MESSAGES) > 0
    
    def test_error_messages_content(self):
        """Test ERROR_MESSAGES contains expected keys."""
        expected_keys = {
            "file_too_large",
            "unsupported_type", 
            "empty_content",
            "invalid_filename",
            "text_too_large",
            "processing_failed"
        }
        assert expected_keys.issubset(set(ERROR_MESSAGES.keys()))
    
    def test_error_messages_not_empty(self):
        """Test all error messages are non-empty strings."""
        for key, message in ERROR_MESSAGES.items():
            assert isinstance(message, str)
            assert len(message.strip()) > 0
    
    def test_error_messages_contain_limits(self):
        """Test error messages contain relevant limit information."""
        # File size message should mention the limit
        file_size_msg = ERROR_MESSAGES["file_too_large"]
        assert str(MAX_FILE_SIZE // (1024 * 1024)) in file_size_msg
        
        # Text size message should mention the limit
        text_size_msg = ERROR_MESSAGES["text_too_large"]
        assert str(MAX_TEXT_CONTENT_LENGTH // 1024) in text_size_msg
        
        # Filename message should mention the limit
        filename_msg = ERROR_MESSAGES["invalid_filename"]
        assert str(MAX_FILENAME_LENGTH) in filename_msg


class TestConfigurationConsistency:
    """Test consistency between different configuration values."""
    
    def test_size_limits_hierarchy(self):
        """Test that size limits follow logical hierarchy."""
        assert MIN_TEXT_LENGTH < MAX_TEXT_CONTENT_LENGTH
        assert MAX_TEXT_CONTENT_LENGTH <= MAX_FILE_SIZE
    
    def test_content_types_and_extensions_consistency(self):
        """Test consistency between content types and extensions."""
        # PDF
        assert "application/pdf" in ALLOWED_CONTENT_TYPES
        assert ".pdf" in ALLOWED_EXTENSIONS
        
        # DOCX
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in ALLOWED_CONTENT_TYPES
        assert ".docx" in ALLOWED_EXTENSIONS
        
        # TXT
        assert "text/plain" in ALLOWED_CONTENT_TYPES
        assert ".txt" in ALLOWED_EXTENSIONS
    
    def test_no_duplicate_extensions(self):
        """Test that there are no duplicate extensions."""
        extensions_list = list(ALLOWED_EXTENSIONS)
        extensions_set = set(ALLOWED_EXTENSIONS)
        assert len(extensions_list) == len(extensions_set)
    
    def test_no_duplicate_content_types(self):
        """Test that there are no duplicate content types."""
        content_types_list = list(ALLOWED_CONTENT_TYPES)
        content_types_set = set(ALLOWED_CONTENT_TYPES)
        assert len(content_types_list) == len(content_types_set)


class TestConfigurationValidation:
    """Test that configuration values are valid."""
    
    def test_file_size_is_positive(self):
        """Test that all size limits are positive."""
        assert MAX_FILE_SIZE > 0
        assert MAX_TEXT_CONTENT_LENGTH > 0
        assert MIN_TEXT_LENGTH > 0
        assert MAX_FILENAME_LENGTH > 0
    
    def test_content_types_are_valid_format(self):
        """Test that content types follow valid format."""
        for content_type in ALLOWED_CONTENT_TYPES:
            assert "/" in content_type
            parts = content_type.split("/")
            assert len(parts) == 2
            assert all(len(part) > 0 for part in parts)
    
    def test_extensions_are_valid_format(self):
        """Test that extensions follow valid format."""
        for extension in ALLOWED_EXTENSIONS:
            assert extension.startswith(".")
            assert len(extension) > 1
            # Should contain only alphanumeric characters after the dot
            ext_part = extension[1:]
            assert ext_part.isalnum() or ext_part in ["docx"]  # docx is special case
    
    def test_rate_limit_is_reasonable(self):
        """Test that rate limit is reasonable."""
        assert 1 <= UPLOAD_RATE_LIMIT <= 100  # Between 1 and 100 per minute 