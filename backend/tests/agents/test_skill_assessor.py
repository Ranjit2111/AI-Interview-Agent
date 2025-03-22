"""
Tests for the skill assessor agent module.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.skill_assessor import SkillAssessorAgent


@pytest.fixture
def skill_assessor():
    """Create a skill assessor agent instance for testing."""
    return SkillAssessorAgent()


@pytest.fixture
def mock_gemini():
    """Create a mock Gemini model."""
    with patch('backend.agents.skill_assessor.GoogleGenerativeAI') as mock:
        model = MagicMock()
        model.generate_content.return_value = MagicMock(
            text="Test assessment response"
        )
        mock.return_value = model
        yield mock


class TestSkillAssessorAgent:
    """Tests for the SkillAssessorAgent class."""
    
    def test_initialization(self, skill_assessor, mock_gemini):
        """Test that skill assessor agent initializes properly."""
        assert skill_assessor.model is not None
        assert skill_assessor.context is not None
        assert skill_assessor.skill_keywords is not None
        assert isinstance(skill_assessor.skill_keywords, dict)
    
    def test_process_input(self, skill_assessor, mock_gemini):
        """Test processing assessment input."""
        # Test input
        test_input = "I have experience with Python and SQL"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = skill_assessor.process_input(test_input, test_context)
        
        # Verify result
        assert result is not None
        assert "skills" in result
        assert "proficiency" in result
        assert "feedback" in result
        assert isinstance(result["skills"], list)
        assert isinstance(result["proficiency"], dict)
        assert isinstance(result["feedback"], str)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_identify_skills(self, skill_assessor):
        """Test skill identification."""
        # Test input
        test_input = "I work with Python, SQL, and JavaScript"
        
        # Identify skills
        skills = skill_assessor._identify_skills_in_text(test_input)
        
        # Verify skills
        assert isinstance(skills, list)
        assert "Python" in skills
        assert "SQL" in skills
        assert "JavaScript" in skills
    
    def test_estimate_proficiency(self, skill_assessor, mock_gemini):
        """Test proficiency estimation."""
        # Test input
        test_input = "I have 3 years of Python experience"
        test_skills = ["Python"]
        
        # Estimate proficiency
        proficiency = skill_assessor._estimate_proficiency(test_input, test_skills)
        
        # Verify proficiency
        assert isinstance(proficiency, dict)
        assert "Python" in proficiency
        assert isinstance(proficiency["Python"], float)
        assert 0 <= proficiency["Python"] <= 1
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_skill_profile(self, skill_assessor, mock_gemini):
        """Test generating skill profile."""
        # Test input
        test_input = "I'm proficient in Python and learning SQL"
        test_skills = ["Python", "SQL"]
        test_proficiency = {"Python": 0.8, "SQL": 0.3}
        
        # Generate profile
        profile = skill_assessor._generate_skill_profile(
            test_input, test_skills, test_proficiency
        )
        
        # Verify profile
        assert profile is not None
        assert isinstance(profile, str)
        assert "Python" in profile
        assert "SQL" in profile
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_skill_keywords_initialization(self, skill_assessor):
        """Test skill keywords initialization."""
        # Verify skill keywords
        assert "programming_languages" in skill_assessor.skill_keywords
        assert "frameworks" in skill_assessor.skill_keywords
        assert "databases" in skill_assessor.skill_keywords
        
        # Verify keyword lists are not empty
        assert len(skill_assessor.skill_keywords["programming_languages"]) > 0
        assert len(skill_assessor.skill_keywords["frameworks"]) > 0
        assert len(skill_assessor.skill_keywords["databases"]) > 0
    
    def test_context_management(self, skill_assessor):
        """Test context management in skill assessor."""
        # Add some messages
        skill_assessor.context.add_message("user", "Hello")
        skill_assessor.context.add_message("assistant", "Hi there!")
        
        # Verify context state
        assert len(skill_assessor.context.messages) == 2
        assert skill_assessor.context.messages[0]["content"] == "Hello"
        assert skill_assessor.context.messages[1]["content"] == "Hi there!"
    
    def test_error_handling(self, skill_assessor, mock_gemini):
        """Test error handling in skill assessor."""
        # Set up mock to raise an exception
        mock_gemini.return_value.generate_content.side_effect = Exception("Test error")
        
        # Test input
        test_input = "What are my skills?"
        test_context = {"session_id": "test_session"}
        
        # Process input (should handle error gracefully)
        result = skill_assessor.process_input(test_input, test_context)
        
        # Verify error handling
        assert result is not None
        assert "error" in result
        assert isinstance(result["error"], str)
    
    def test_skill_normalization(self, skill_assessor):
        """Test skill name normalization."""
        # Test cases
        test_cases = [
            ("python", "Python"),
            ("PYTHON", "Python"),
            ("Python 3", "Python"),
            ("JavaScript/JS", "JavaScript")
        ]
        
        for input_skill, expected_skill in test_cases:
            normalized = skill_assessor._normalize_skill_name(input_skill)
            assert normalized == expected_skill
    
    def test_proficiency_thresholds(self, skill_assessor):
        """Test proficiency level thresholds."""
        # Test cases
        test_cases = [
            (0.8, "Expert"),
            (0.6, "Proficient"),
            (0.4, "Intermediate"),
            (0.2, "Beginner")
        ]
        
        for score, expected_level in test_cases:
            level = skill_assessor._get_proficiency_level(score)
            assert level == expected_level


if __name__ == "__main__":
    pytest.main(["-v"]) 