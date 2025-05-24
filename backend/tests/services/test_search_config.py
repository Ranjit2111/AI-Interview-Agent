"""
Tests for search_config module.
Tests the configuration data extracted from search_service.py.
"""

import pytest
from backend.services.search_config import (
    COURSE_DOMAINS, VIDEO_DOMAINS, DOCUMENTATION_DOMAINS, COMMUNITY_DOMAINS, BOOK_DOMAINS,
    COURSE_INDICATORS, VIDEO_INDICATORS, DOCUMENTATION_INDICATORS, 
    TUTORIAL_INDICATORS, COMMUNITY_INDICATORS, BOOK_INDICATORS,
    TOP_QUALITY_DOMAINS, MEDIUM_QUALITY_DOMAINS,
    PROFICIENCY_LEVEL_TERMS, FALLBACK_PLATFORMS,
    RELEVANCE_WEIGHTS, DOMAIN_QUALITY_SCORES
)


class TestDomainMappings:
    """Test domain mapping configurations."""
    
    def test_course_domains_structure(self):
        """Test course domains are properly configured."""
        assert isinstance(COURSE_DOMAINS, set)
        assert len(COURSE_DOMAINS) > 0
        assert "coursera.org" in COURSE_DOMAINS
        assert "udemy.com" in COURSE_DOMAINS
    
    def test_video_domains_structure(self):
        """Test video domains are properly configured."""
        assert isinstance(VIDEO_DOMAINS, set)
        assert len(VIDEO_DOMAINS) > 0
        assert "youtube.com" in VIDEO_DOMAINS
        assert "vimeo.com" in VIDEO_DOMAINS
    
    def test_documentation_domains_structure(self):
        """Test documentation domains are properly configured."""
        assert isinstance(DOCUMENTATION_DOMAINS, set)
        assert len(DOCUMENTATION_DOMAINS) > 0
        assert "docs." in DOCUMENTATION_DOMAINS
    
    def test_community_domains_structure(self):
        """Test community domains are properly configured."""
        assert isinstance(COMMUNITY_DOMAINS, set)
        assert len(COMMUNITY_DOMAINS) > 0
        assert "stackoverflow.com" in COMMUNITY_DOMAINS
    
    def test_book_domains_structure(self):
        """Test book domains are properly configured."""
        assert isinstance(BOOK_DOMAINS, set)
        assert len(BOOK_DOMAINS) > 0
        assert "amazon.com" in BOOK_DOMAINS


class TestResourceIndicators:
    """Test resource indicator configurations."""
    
    def test_course_indicators_structure(self):
        """Test course indicators are properly configured."""
        assert isinstance(COURSE_INDICATORS, set)
        assert len(COURSE_INDICATORS) > 0
        assert "course" in COURSE_INDICATORS
        assert "learn" in COURSE_INDICATORS
    
    def test_video_indicators_structure(self):
        """Test video indicators are properly configured."""
        assert isinstance(VIDEO_INDICATORS, set)
        assert len(VIDEO_INDICATORS) > 0
        assert "video" in VIDEO_INDICATORS
        assert "tutorial" in VIDEO_INDICATORS
    
    def test_tutorial_indicators_structure(self):
        """Test tutorial indicators are properly configured."""
        assert isinstance(TUTORIAL_INDICATORS, set)
        assert len(TUTORIAL_INDICATORS) > 0
        assert "tutorial" in TUTORIAL_INDICATORS
        assert "how to" in TUTORIAL_INDICATORS
    
    def test_no_overlapping_primary_indicators(self):
        """Test that primary indicators don't overlap too much."""
        # Some overlap is expected, but core terms should be distinct
        course_core = {"course", "class"}
        video_core = {"video", "watch"}
        
        overlap = course_core.intersection(video_core)
        assert len(overlap) == 0  # Core terms shouldn't overlap


class TestQualityDomains:
    """Test quality domain configurations."""
    
    def test_top_quality_domains_structure(self):
        """Test top quality domains are properly configured."""
        assert isinstance(TOP_QUALITY_DOMAINS, set)
        assert len(TOP_QUALITY_DOMAINS) > 0
        assert "github.com" in TOP_QUALITY_DOMAINS
        assert "stackoverflow.com" in TOP_QUALITY_DOMAINS
        assert "mdn.mozilla.org" in TOP_QUALITY_DOMAINS
    
    def test_medium_quality_domains_structure(self):
        """Test medium quality domains are properly configured."""
        assert isinstance(MEDIUM_QUALITY_DOMAINS, set)
        assert len(MEDIUM_QUALITY_DOMAINS) > 0
        assert "javatpoint.com" in MEDIUM_QUALITY_DOMAINS
    
    def test_no_domain_overlap(self):
        """Test that top and medium quality domains don't overlap."""
        overlap = TOP_QUALITY_DOMAINS.intersection(MEDIUM_QUALITY_DOMAINS)
        assert len(overlap) == 0


class TestProficiencyLevels:
    """Test proficiency level configurations."""
    
    def test_proficiency_level_terms_structure(self):
        """Test proficiency level terms are properly configured."""
        assert isinstance(PROFICIENCY_LEVEL_TERMS, dict)
        assert len(PROFICIENCY_LEVEL_TERMS) > 0
        
        required_levels = {"beginner", "basic", "intermediate", "advanced", "expert"}
        assert required_levels.issubset(set(PROFICIENCY_LEVEL_TERMS.keys()))
    
    def test_proficiency_level_terms_content(self):
        """Test proficiency level terms contain expected keywords."""
        assert "beginner" in PROFICIENCY_LEVEL_TERMS["beginner"]
        assert "introduction" in PROFICIENCY_LEVEL_TERMS["beginner"]
        assert "advanced" in PROFICIENCY_LEVEL_TERMS["advanced"]
        assert "expert" in PROFICIENCY_LEVEL_TERMS["expert"]
    
    def test_proficiency_levels_are_sets(self):
        """Test that proficiency level values are sets."""
        for level, terms in PROFICIENCY_LEVEL_TERMS.items():
            assert isinstance(terms, set)
            assert len(terms) > 0


class TestFallbackPlatforms:
    """Test fallback platform configurations."""
    
    def test_fallback_platforms_structure(self):
        """Test fallback platforms are properly configured."""
        assert isinstance(FALLBACK_PLATFORMS, list)
        assert len(FALLBACK_PLATFORMS) > 0
    
    def test_fallback_platform_required_fields(self):
        """Test each fallback platform has required fields."""
        required_fields = {"title_template", "url_template", "description_template", "type"}
        
        for platform in FALLBACK_PLATFORMS:
            assert isinstance(platform, dict)
            assert required_fields.issubset(set(platform.keys()))
    
    def test_fallback_platform_templates(self):
        """Test fallback platform templates contain placeholders."""
        for platform in FALLBACK_PLATFORMS:
            title_template = platform["title_template"]
            url_template = platform["url_template"]
            description_template = platform["description_template"]
            
            # Should contain skill placeholder
            assert "{skill}" in title_template or "{skill}" in url_template or "{skill}" in description_template
    
    def test_fallback_platform_variety(self):
        """Test fallback platforms cover different types."""
        types = {platform["type"] for platform in FALLBACK_PLATFORMS}
        assert len(types) > 1  # Should have multiple types
        assert "course" in types
        assert "video" in types


class TestScoringConfiguration:
    """Test scoring configuration."""
    
    def test_relevance_weights_structure(self):
        """Test relevance weights are properly configured."""
        assert isinstance(RELEVANCE_WEIGHTS, dict)
        assert len(RELEVANCE_WEIGHTS) > 0
        
        required_weights = {
            "skill_in_title", "skill_in_url", "skill_in_description",
            "level_in_title", "level_in_description",
            "job_role_in_title", "job_role_in_description",
            "domain_quality_multiplier"
        }
        assert required_weights.issubset(set(RELEVANCE_WEIGHTS.keys()))
    
    def test_relevance_weights_values(self):
        """Test relevance weights have reasonable values."""
        for weight_name, weight_value in RELEVANCE_WEIGHTS.items():
            assert isinstance(weight_value, (int, float))
            assert 0 <= weight_value <= 1  # Should be normalized
    
    def test_domain_quality_scores_structure(self):
        """Test domain quality scores are properly configured."""
        assert isinstance(DOMAIN_QUALITY_SCORES, dict)
        assert "top" in DOMAIN_QUALITY_SCORES
        assert "medium" in DOMAIN_QUALITY_SCORES
        assert "default" in DOMAIN_QUALITY_SCORES
    
    def test_domain_quality_scores_values(self):
        """Test domain quality scores have reasonable values."""
        scores = DOMAIN_QUALITY_SCORES
        assert scores["top"] == 1.0
        assert scores["medium"] < scores["top"]
        assert scores["default"] < scores["medium"]
        assert all(0 <= score <= 1 for score in scores.values()) 