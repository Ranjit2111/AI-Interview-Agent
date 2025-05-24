"""
Tests for llm_chain_processor module.
Tests the ChainResultProcessor class extracted from llm_utils.py.
"""

import pytest
import json
import logging
from unittest.mock import Mock, MagicMock
from backend.utils.llm_chain_processor import ChainResultProcessor


class TestChainResultProcessor:
    """Test the ChainResultProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = Mock(spec=logging.Logger)
        self.processor = ChainResultProcessor(self.logger)
    
    def test_successful_chain_invocation(self):
        """Test successful chain invocation without output_key."""
        # Mock chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"result": "success"}
        
        inputs = {"input": "test"}
        result = self.processor.invoke_with_error_handling(mock_chain, inputs)
        
        assert result == {"result": "success"}
        mock_chain.invoke.assert_called_once_with(inputs)
        self.logger.debug.assert_called()
    
    def test_chain_invocation_with_output_key(self):
        """Test chain invocation with specific output_key."""
        # Mock chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"answer": "test answer", "metadata": "extra"}
        
        inputs = {"input": "test"}
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, output_key="answer"
        )
        
        assert result == "test answer"
        mock_chain.invoke.assert_called_once_with(inputs)
    
    def test_chain_invocation_with_json_string_output(self):
        """Test chain invocation that returns JSON string."""
        # Mock chain
        mock_chain = Mock()
        json_data = {"parsed": "data", "status": "ok"}
        mock_chain.invoke.return_value = {"result": json.dumps(json_data)}
        
        inputs = {"input": "test"}
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, output_key="result"
        )
        
        assert result == json_data
    
    def test_chain_invocation_with_markdown_json(self):
        """Test chain invocation with JSON in markdown code block."""
        # Mock chain
        mock_chain = Mock()
        json_data = {"extracted": "from markdown"}
        markdown_json = f'```json\n{json.dumps(json_data)}\n```'
        mock_chain.invoke.return_value = {"text": markdown_json}
        
        inputs = {"input": "test"}
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, output_key="result", default_creator=lambda: "default"
        )
        
        # Should fall back to parsing text field when output_key not found
        assert result == json_data
    
    def test_chain_invocation_error_handling(self):
        """Test error handling when chain fails."""
        # Mock chain that raises exception
        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("Chain failed")
        
        inputs = {"input": "test"}
        default_value = "fallback"
        
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, default_creator=lambda: default_value
        )
        
        assert result == default_value
        self.logger.exception.assert_called()
    
    def test_empty_result_handling(self):
        """Test handling of empty chain results."""
        # Mock chain that returns None
        mock_chain = Mock()
        mock_chain.invoke.return_value = None
        
        inputs = {"input": "test"}
        default_value = "empty_fallback"
        
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, default_creator=lambda: default_value
        )
        
        assert result == default_value
        self.logger.warning.assert_called()
    
    def test_missing_output_key(self):
        """Test handling when requested output_key is missing."""
        # Mock chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"other_key": "value"}
        
        inputs = {"input": "test"}
        default_value = "missing_key_fallback"
        
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, output_key="missing_key", default_creator=lambda: default_value
        )
        
        assert result == default_value
        self.logger.error.assert_called()
    
    def test_single_value_dict_processing(self):
        """Test processing of single-value dictionary results."""
        # Mock chain
        mock_chain = Mock()
        json_data = {"processed": "single_value"}
        mock_chain.invoke.return_value = {"only_key": json.dumps(json_data)}
        
        inputs = {"input": "test"}
        result = self.processor.invoke_with_error_handling(mock_chain, inputs)
        
        # Should extract and parse the single value
        assert result == json_data
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON strings."""
        # Mock chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"result": "invalid json {not valid}"}
        
        inputs = {"input": "test"}
        result = self.processor.invoke_with_error_handling(
            mock_chain, inputs, output_key="result"
        )
        
        # Should return the string as-is when JSON parsing fails
        assert result == "invalid json {not valid}"
    
    def test_extract_output_key_direct(self):
        """Test direct output key extraction."""
        result = {"target": "direct_value", "other": "ignore"}
        extracted = self.processor._extract_output_key(result, "target", "default")
        assert extracted == "direct_value"
    
    def test_extract_output_key_from_text_json(self):
        """Test output key extraction from text field JSON."""
        json_data = {"target_key": "extracted_value"}
        result = {"text": json.dumps(json_data)}
        extracted = self.processor._extract_output_key(result, "missing", "default")
        assert extracted == json_data
    
    def test_parse_json_with_fallback_markdown(self):
        """Test JSON parsing from markdown code blocks."""
        json_data = {"markdown": "extracted"}
        markdown_text = f'```json\n{json.dumps(json_data)}\n```'
        parsed = self.processor._parse_json_with_fallback(markdown_text)
        assert parsed == json_data
    
    def test_parse_json_with_fallback_direct(self):
        """Test direct JSON parsing."""
        json_data = {"direct": "parsing"}
        json_text = json.dumps(json_data)
        parsed = self.processor._parse_json_with_fallback(json_text)
        assert parsed == json_data
    
    def test_parse_json_with_fallback_invalid(self):
        """Test JSON parsing with invalid input."""
        invalid_json = "not json at all"
        parsed = self.processor._parse_json_with_fallback(invalid_json)
        assert parsed is None
    
    def test_process_extracted_value_string_json(self):
        """Test processing of extracted string value containing JSON."""
        json_data = {"string": "json_value"}
        json_string = json.dumps(json_data)
        processed = self.processor._process_extracted_value(json_string)
        assert processed == json_data
    
    def test_process_extracted_value_non_string(self):
        """Test processing of non-string extracted values."""
        value = {"already": "processed"}
        processed = self.processor._process_extracted_value(value)
        assert processed == value
    
    def test_process_full_result_single_dict(self):
        """Test processing full result with single dictionary entry."""
        json_data = {"single": "result"}
        result = {"only_key": json.dumps(json_data)}
        processed = self.processor._process_full_result(result)
        assert processed == json_data
    
    def test_process_full_result_multiple_keys(self):
        """Test processing full result with multiple dictionary entries."""
        result = {"key1": "value1", "key2": "value2"}
        processed = self.processor._process_full_result(result)
        assert processed == result  # Should return as-is 