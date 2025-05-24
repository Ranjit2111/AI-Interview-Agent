"""
Test cases for utils.common module.
"""

import pytest
from datetime import datetime
from backend.utils.common import get_current_timestamp, safe_get_or_default


class TestCommonUtils:
    """Test cases for common utility functions."""
    
    def test_get_current_timestamp_format(self):
        """Test that timestamp is in correct ISO format."""
        timestamp = get_current_timestamp()
        
        # Should be a string
        assert isinstance(timestamp, str)
        
        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)
        
        # Should be recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - parsed).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_get_current_timestamp_consistency(self):
        """Test that consecutive calls return consistent format."""
        timestamp1 = get_current_timestamp()
        timestamp2 = get_current_timestamp()
        
        # Both should be valid ISO format
        datetime.fromisoformat(timestamp1)
        datetime.fromisoformat(timestamp2)
        
        # Should have same format structure
        assert len(timestamp1.split('T')) == 2
        assert len(timestamp2.split('T')) == 2
    
    def test_safe_get_or_default_with_valid_value(self):
        """Test safe_get_or_default with non-empty value."""
        result = safe_get_or_default("valid_value", "default")
        assert result == "valid_value"
    
    def test_safe_get_or_default_with_empty_string(self):
        """Test safe_get_or_default with empty string."""
        result = safe_get_or_default("", "default")
        assert result == "default"
    
    def test_safe_get_or_default_with_none(self):
        """Test safe_get_or_default with None value."""
        result = safe_get_or_default(None, "default")
        assert result == "default"
    
    def test_safe_get_or_default_with_whitespace_only(self):
        """Test safe_get_or_default with whitespace-only string."""
        result = safe_get_or_default("   ", "default")
        assert result == "   "  # Whitespace should be preserved as truthy
    
    def test_safe_get_or_default_with_zero(self):
        """Test safe_get_or_default with numeric zero."""
        result = safe_get_or_default(0, "default")
        assert result == "default"  # 0 is falsy
    
    def test_safe_get_or_default_with_false(self):
        """Test safe_get_or_default with boolean False."""
        result = safe_get_or_default(False, "default")
        assert result == "default"  # False is falsy
    
    def test_safe_get_or_default_preserves_types(self):
        """Test that the function preserves string types."""
        # Test with different string values
        assert safe_get_or_default("test", "default") == "test"
        assert safe_get_or_default("123", "default") == "123"
        assert safe_get_or_default("True", "default") == "True" 