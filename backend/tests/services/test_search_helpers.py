"""
Tests for search_helpers module.
Tests the refactored helper classes extracted from search_service.py.
"""

import pytest
from backend.services.search_helpers import (
    ResourceType, ResourceClassifier, RelevanceScorer, 
    DomainQualityEvaluator, FallbackResourceGenerator
)


class TestResourceClassifier:
    """Test the ResourceClassifier helper class."""
    
    def test_classify_course_by_domain(self):
        """Test course classification by domain."""
        title = "Machine Learning Tutorial"
        url = "https://coursera.org/learn/machine-learning"
        description = "Learn machine learning fundamentals"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.COURSE
    
    def test_classify_course_by_title(self):
        """Test course classification by title keywords."""
        title = "Learn Python Programming Course"
        url = "https://example.com/python"
        description = "Python programming tutorial"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.COURSE
    
    def test_classify_video_by_domain(self):
        """Test video classification by domain."""
        title = "Python Tutorial"
        url = "https://youtube.com/watch?v=abc123"
        description = "Learn Python programming"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.VIDEO
    
    def test_classify_documentation(self):
        """Test documentation classification."""
        title = "Python Documentation"
        url = "https://docs.python.org/3/"
        description = "Official Python documentation"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.DOCUMENTATION
    
    def test_classify_tutorial(self):
        """Test tutorial classification."""
        title = "How to build REST APIs"
        url = "https://example.com/api-tutorial"
        description = "Step by step guide to building APIs"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.TUTORIAL
    
    def test_classify_community(self):
        """Test community resource classification."""
        title = "Django Questions"
        url = "https://stackoverflow.com/questions/tagged/django"
        description = "Django community discussions"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.COMMUNITY
    
    def test_classify_book(self):
        """Test book classification."""
        title = "Clean Code Book"
        url = "https://amazon.com/clean-code"
        description = "Programming book on clean code"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.BOOK
    
    def test_classify_default_article(self):
        """Test default classification as article."""
        title = "Software Engineering Best Practices"
        url = "https://example.com/blog/engineering"
        description = "Article about software engineering"
        
        result = ResourceClassifier.classify(title, url, description)
        assert result == ResourceType.ARTICLE


class TestRelevanceScorer:
    """Test the RelevanceScorer helper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = RelevanceScorer()
    
    def test_skill_in_title_high_score(self):
        """Test high relevance score when skill is in title."""
        scorer = RelevanceScorer()
        title = "Python Programming Fundamentals"
        url = "https://example.com/python"
        description = "Learn programming basics"
        skill = "python"
        proficiency_level = "beginner"
        
        score = scorer.calculate_score(title, url, description, skill, proficiency_level)
        assert score > 0.4  # Should get skill_in_title weight
    
    def test_skill_in_url_score(self):
        """Test relevance score when skill is in URL."""
        scorer = RelevanceScorer()
        title = "Programming Tutorial"
        url = "https://example.com/learn-python"
        description = "Programming tutorial"
        skill = "python"
        proficiency_level = "intermediate"
        
        score = scorer.calculate_score(title, url, description, skill, proficiency_level)
        assert score > 0.2  # Should get skill_in_url weight
    
    def test_proficiency_level_matching(self):
        """Test proficiency level matching in scoring."""
        scorer = RelevanceScorer()
        title = "Beginner Python Tutorial"
        url = "https://example.com/python"
        description = "Introduction to Python programming"
        skill = "python"
        proficiency_level = "beginner"
        
        score = scorer.calculate_score(title, url, description, skill, proficiency_level)
        # Should get points for skill and level matching
        assert score > 0.5
    
    def test_job_role_bonus(self):
        """Test job role matching bonus."""
        scorer = RelevanceScorer()
        title = "Data Scientist Python Guide"
        url = "https://example.com/python-ds"
        description = "Python for data scientist roles"
        skill = "python"
        proficiency_level = "intermediate"
        job_role = "data scientist"
        
        score = scorer.calculate_score(title, url, description, skill, proficiency_level, job_role)
        # Should get bonus for job role matching
        assert score > 0.4
    
    def test_domain_quality_bonus(self):
        """Test domain quality bonus in scoring."""
        scorer = RelevanceScorer()
        title = "Python Tutorial"
        url = "https://github.com/learn-python"
        description = "Learn Python programming"
        skill = "python"
        proficiency_level = "beginner"
        
        score = scorer.calculate_score(title, url, description, skill, proficiency_level)
        # GitHub is a top quality domain, should get bonus
        assert score > 0.4


class TestDomainQualityEvaluator:
    """Test the DomainQualityEvaluator helper class."""
    
    def test_top_quality_domain(self):
        """Test recognition of top quality domains."""
        url = "https://github.com/python/cpython"
        score = DomainQualityEvaluator.get_quality_score(url)
        assert score == 1.0
    
    def test_medium_quality_domain(self):
        """Test recognition of medium quality domains."""
        url = "https://javatpoint.com/python-tutorial"
        score = DomainQualityEvaluator.get_quality_score(url)
        assert score == 0.7
    
    def test_unknown_domain_default(self):
        """Test default score for unknown domains."""
        url = "https://unknown-site.com/tutorial"
        score = DomainQualityEvaluator.get_quality_score(url)
        assert score == 0.4
    
    def test_multiple_quality_domains(self):
        """Test various quality domain recognitions."""
        test_cases = [
            ("https://stackoverflow.com/questions/python", 1.0),
            ("https://mdn.mozilla.org/docs", 1.0),
            ("https://tutorialspoint.com/python", 0.7),
            ("https://random-blog.com/python", 0.4)
        ]
        
        for url, expected_score in test_cases:
            score = DomainQualityEvaluator.get_quality_score(url)
            assert score == expected_score


class TestFallbackResourceGenerator:
    """Test the FallbackResourceGenerator helper class."""
    
    def test_generate_fallback_resources(self):
        """Test generation of fallback resources."""
        skill = "python"
        proficiency_level = "beginner"
        
        resources = FallbackResourceGenerator.generate_fallback_resources(skill, proficiency_level)
        
        # Should generate multiple fallback resources
        assert len(resources) > 0
        
        # Each resource should have required fields
        for resource in resources:
            assert "title" in resource
            assert "url" in resource
            assert "description" in resource
            assert "type" in resource
            assert "source" in resource
            assert resource["source"] == "fallback"
            assert "relevance_score" in resource
    
    def test_fallback_resource_content(self):
        """Test content of generated fallback resources."""
        skill = "javascript"
        proficiency_level = "intermediate"
        
        resources = FallbackResourceGenerator.generate_fallback_resources(skill, proficiency_level)
        
        # Should contain skill name in titles/descriptions
        skill_mentioned = any(skill.lower() in resource["title"].lower() for resource in resources)
        assert skill_mentioned
        
        # Should have various resource types
        types = {resource["type"] for resource in resources}
        assert len(types) > 1  # Should have multiple types
    
    def test_fallback_url_formatting(self):
        """Test proper URL formatting in fallback resources."""
        skill = "machine learning"
        proficiency_level = "advanced"
        
        resources = FallbackResourceGenerator.generate_fallback_resources(skill, proficiency_level)
        
        # All URLs should be valid format
        for resource in resources:
            url = resource["url"]
            assert url.startswith("https://")
            # Should contain skill in some form
            assert any(word in url.lower() for word in skill.lower().split()) 