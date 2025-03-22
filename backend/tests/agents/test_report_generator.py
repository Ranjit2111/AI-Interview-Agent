"""
Tests for the report generator agent module.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.report_generator import ReportGeneratorAgent


@pytest.fixture
def report_generator():
    """Create a report generator agent instance for testing."""
    return ReportGeneratorAgent()


@pytest.fixture
def mock_gemini():
    """Create a mock Gemini model."""
    with patch('backend.agents.report_generator.GoogleGenerativeAI') as mock:
        model = MagicMock()
        model.generate_content.return_value = MagicMock(
            text="Test report content"
        )
        mock.return_value = model
        yield mock


class TestReportGeneratorAgent:
    """Tests for the ReportGeneratorAgent class."""
    
    def test_initialization(self, report_generator, mock_gemini):
        """Test that report generator agent initializes properly."""
        assert report_generator.model is not None
        assert report_generator.context is not None
        assert report_generator.report_templates is not None
        assert isinstance(report_generator.report_templates, dict)
    
    def test_process_input(self, report_generator, mock_gemini):
        """Test processing report generation input."""
        # Test input
        test_input = "Generate a report for my interview"
        test_context = {
            "session_id": "test_session",
            "interview_data": {
                "questions": ["Q1", "Q2"],
                "responses": ["R1", "R2"],
                "scores": [0.8, 0.7]
            }
        }
        
        # Process input
        result = report_generator.process_input(test_input, test_context)
        
        # Verify result
        assert result is not None
        assert "report" in result
        assert "summary" in result
        assert "recommendations" in result
        assert isinstance(result["report"], str)
        assert isinstance(result["summary"], str)
        assert isinstance(result["recommendations"], list)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_report(self, report_generator, mock_gemini):
        """Test report generation."""
        # Test data
        test_data = {
            "interview_data": {
                "questions": ["Q1", "Q2"],
                "responses": ["R1", "R2"],
                "scores": [0.8, 0.7]
            }
        }
        
        # Generate report
        report = report_generator._generate_report(test_data)
        
        # Verify report
        assert report is not None
        assert isinstance(report, dict)
        assert "report" in report
        assert "summary" in report
        assert "recommendations" in report
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_summary(self, report_generator, mock_gemini):
        """Test summary generation."""
        # Test data
        test_data = {
            "scores": [0.8, 0.7, 0.9],
            "responses": ["R1", "R2", "R3"]
        }
        
        # Generate summary
        summary = report_generator._generate_summary(test_data)
        
        # Verify summary
        assert summary is not None
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_recommendations(self, report_generator, mock_gemini):
        """Test recommendation generation."""
        # Test data
        test_data = {
            "weaknesses": ["communication", "technical depth"],
            "improvement_areas": ["problem-solving", "code quality"]
        }
        
        # Generate recommendations
        recommendations = report_generator._generate_recommendations(test_data)
        
        # Verify recommendations
        assert recommendations is not None
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_context_management(self, report_generator):
        """Test context management in report generator."""
        # Add some messages
        report_generator.context.add_message("user", "Hello")
        report_generator.context.add_message("assistant", "Hi there!")
        
        # Verify context state
        assert len(report_generator.context.messages) == 2
        assert report_generator.context.messages[0]["content"] == "Hello"
        assert report_generator.context.messages[1]["content"] == "Hi there!"
    
    def test_error_handling(self, report_generator, mock_gemini):
        """Test error handling in report generator."""
        # Set up mock to raise an exception
        mock_gemini.return_value.generate_content.side_effect = Exception("Test error")
        
        # Test input
        test_input = "Generate a report"
        test_context = {"session_id": "test_session"}
        
        # Process input (should handle error gracefully)
        result = report_generator.process_input(test_input, test_context)
        
        # Verify error handling
        assert result is not None
        assert "error" in result
        assert isinstance(result["error"], str)
    
    def test_report_templates(self, report_generator):
        """Test report template management."""
        # Verify templates
        assert "interview" in report_generator.report_templates
        assert "skill_assessment" in report_generator.report_templates
        assert "feedback" in report_generator.report_templates
        
        # Verify template structure
        for template in report_generator.report_templates.values():
            assert "sections" in template
            assert isinstance(template["sections"], list)
            assert len(template["sections"]) > 0
    
    def test_report_formatting(self, report_generator, mock_gemini):
        """Test report formatting."""
        # Set up mock response
        mock_gemini.return_value.generate_content.return_value = MagicMock(
            text="Here's your report:\n1. First section\n2. Second section"
        )
        
        # Test input
        test_input = "Format this report"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = report_generator.process_input(test_input, test_context)
        
        # Verify formatting
        assert result is not None
        assert "report" in result
        assert "1. First section" in result["report"]
        assert "2. Second section" in result["report"]
    
    def test_report_sections(self, report_generator):
        """Test report section generation."""
        # Test data
        test_data = {
            "interview_data": {
                "questions": ["Q1", "Q2"],
                "responses": ["R1", "R2"],
                "scores": [0.8, 0.7]
            }
        }
        
        # Generate sections
        sections = report_generator._generate_sections(test_data)
        
        # Verify sections
        assert sections is not None
        assert isinstance(sections, list)
        assert len(sections) > 0
        assert all(isinstance(s, dict) for s in sections)
        assert all("title" in s for s in sections)
        assert all("content" in s for s in sections)


if __name__ == "__main__":
    pytest.main(["-v"]) 