"""
Test cases for agents.question_templates module.
"""

import pytest
from backend.agents.question_templates import (
    QUESTION_TEMPLATES,
    TEMPLATE_VARIABLES,
    GENERAL_QUESTIONS
)
from backend.agents.config_models import InterviewStyle


class TestQuestionTemplates:
    """Test cases for question templates configuration."""
    
    def test_question_templates_structure(self):
        """Test that QUESTION_TEMPLATES has correct structure."""
        # Should be a dictionary
        assert isinstance(QUESTION_TEMPLATES, dict)
        
        # Should have entries for all interview styles
        expected_styles = [style for style in InterviewStyle]
        for style in expected_styles:
            assert style in QUESTION_TEMPLATES
            
            # Each style should have a list of templates
            templates = QUESTION_TEMPLATES[style]
            assert isinstance(templates, list)
            assert len(templates) > 0
            
            # Each template should be a non-empty string
            for template in templates:
                assert isinstance(template, str)
                assert len(template.strip()) > 0
    
    def test_question_templates_have_placeholders(self):
        """Test that question templates contain expected placeholders."""
        expected_placeholders = ["{technology}", "{scenario}", "{problem_type}", "{challenge}", "{quality_aspect}"]
        
        for style, templates in QUESTION_TEMPLATES.items():
            # At least some templates should have placeholders
            placeholder_found = False
            for template in templates:
                for placeholder in expected_placeholders:
                    if placeholder in template:
                        placeholder_found = True
                        break
                if placeholder_found:
                    break
            
            assert placeholder_found, f"No placeholders found in {style} templates"
    
    def test_template_variables_structure(self):
        """Test that TEMPLATE_VARIABLES has correct structure."""
        # Should be a dictionary
        assert isinstance(TEMPLATE_VARIABLES, dict)
        
        # Should have at least basic job roles
        expected_roles = ["Software Engineer", "Data Scientist"]
        for role in expected_roles:
            assert role in TEMPLATE_VARIABLES
            
            # Each role should have variable categories
            role_vars = TEMPLATE_VARIABLES[role]
            assert isinstance(role_vars, dict)
            
            expected_categories = ["technology", "scenario", "problem_type", "challenge", "quality_aspect"]
            for category in expected_categories:
                assert category in role_vars
                
                # Each category should have a list of options
                options = role_vars[category]
                assert isinstance(options, list)
                assert len(options) > 0
                
                # Each option should be a non-empty string
                for option in options:
                    assert isinstance(option, str)
                    assert len(option.strip()) > 0
    
    def test_general_questions_structure(self):
        """Test that GENERAL_QUESTIONS has correct structure."""
        # Should be a list
        assert isinstance(GENERAL_QUESTIONS, list)
        
        # Should have multiple questions
        assert len(GENERAL_QUESTIONS) > 0
        
        # Each question should be a non-empty string
        for question in GENERAL_QUESTIONS:
            assert isinstance(question, str)
            assert len(question.strip()) > 0
    
    def test_general_questions_formatting(self):
        """Test that general questions can be formatted with job_role."""
        job_role = "Software Engineer"
        
        for question in GENERAL_QUESTIONS:
            try:
                # Should be able to format with job_role parameter
                formatted = question.format(job_role=job_role)
                assert isinstance(formatted, str)
                assert len(formatted) > 0
            except KeyError:
                # If it doesn't have {job_role}, should work as-is
                assert "{job_role}" not in question
    
    def test_interview_style_coverage(self):
        """Test that all interview styles are covered."""
        # Get all interview styles from enum
        all_styles = list(InterviewStyle)
        
        # Check that we have templates for all styles
        for style in all_styles:
            assert style in QUESTION_TEMPLATES
            templates = QUESTION_TEMPLATES[style]
            assert len(templates) >= 3  # Should have at least a few templates per style 