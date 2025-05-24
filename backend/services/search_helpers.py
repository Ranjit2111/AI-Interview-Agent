"""
Helper classes for search service functionality.
Extracts the resource classification and relevance scoring logic.
"""

from typing import Optional
from .search_config import (
    COURSE_DOMAINS, VIDEO_DOMAINS, DOCUMENTATION_DOMAINS, COMMUNITY_DOMAINS, BOOK_DOMAINS,
    COURSE_INDICATORS, VIDEO_INDICATORS, DOCUMENTATION_INDICATORS, 
    TUTORIAL_INDICATORS, COMMUNITY_INDICATORS, BOOK_INDICATORS,
    TOP_QUALITY_DOMAINS, MEDIUM_QUALITY_DOMAINS,
    PROFICIENCY_LEVEL_TERMS, RELEVANCE_WEIGHTS, DOMAIN_QUALITY_SCORES
)


class ResourceType:
    """Resource type constants."""
    ARTICLE = "article"
    COURSE = "course"
    VIDEO = "video"
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    BOOK = "book"
    TOOL = "tool"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class ResourceClassifier:
    """Handles resource type classification based on content and URL."""
    
    @staticmethod
    def classify(title: str, url: str, description: str) -> str:
        """
        Classify a resource based on its characteristics.
        
        Args:
            title: Resource title
            url: Resource URL
            description: Resource description
            
        Returns:
            Resource type
        """
        title_lower = title.lower()
        url_lower = url.lower()
        
        # Check courses first (highest priority)
        if ResourceClassifier._matches_patterns(title_lower, COURSE_INDICATORS) or \
           ResourceClassifier._matches_domains(url_lower, COURSE_DOMAINS):
            return ResourceType.COURSE
        
        # Check videos
        if ResourceClassifier._matches_patterns(title_lower, VIDEO_INDICATORS) or \
           ResourceClassifier._matches_domains(url_lower, VIDEO_DOMAINS):
            return ResourceType.VIDEO
        
        # Check documentation
        if ResourceClassifier._matches_patterns(title_lower, DOCUMENTATION_INDICATORS) or \
           ResourceClassifier._matches_domains(url_lower, DOCUMENTATION_DOMAINS):
            return ResourceType.DOCUMENTATION
        
        # Check tutorials
        if ResourceClassifier._matches_patterns(title_lower, TUTORIAL_INDICATORS):
            return ResourceType.TUTORIAL
        
        # Check communities
        if ResourceClassifier._matches_patterns(title_lower, COMMUNITY_INDICATORS) or \
           ResourceClassifier._matches_domains(url_lower, COMMUNITY_DOMAINS):
            return ResourceType.COMMUNITY
        
        # Check books
        if ResourceClassifier._matches_patterns(title_lower, BOOK_INDICATORS) or \
           ResourceClassifier._matches_domains(url_lower, BOOK_DOMAINS):
            return ResourceType.BOOK
        
        # Default to article
        return ResourceType.ARTICLE
    
    @staticmethod
    def _matches_patterns(text: str, patterns: set) -> bool:
        """Check if text contains any of the patterns."""
        return any(pattern in text for pattern in patterns)
    
    @staticmethod 
    def _matches_domains(url: str, domains: set) -> bool:
        """Check if URL contains any of the domains."""
        return any(domain in url for domain in domains)


class RelevanceScorer:
    """Handles relevance score calculation for resources."""
    
    def __init__(self):
        self.weights = RELEVANCE_WEIGHTS
    
    def calculate_score(
        self,
        title: str,
        url: str,
        description: str,
        skill: str,
        proficiency_level: str,
        job_role: Optional[str] = None
    ) -> float:
        """
        Calculate relevance score for a resource.
        
        Args:
            title: Resource title
            url: Resource URL
            description: Resource description
            skill: The skill being searched
            proficiency_level: The proficiency level
            job_role: Optional job role context
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Prepare text for matching
        title_lower = title.lower()
        url_lower = url.lower()
        description_lower = description.lower()
        skill_lower = skill.lower()
        
        # Skill matching
        score += self._calculate_skill_score(title_lower, url_lower, description_lower, skill_lower)
        
        # Proficiency level matching
        score += self._calculate_level_score(title_lower, description_lower, proficiency_level)
        
        # Job role matching
        if job_role:
            score += self._calculate_job_role_score(title_lower, description_lower, job_role)
        
        # Domain quality bonus
        domain_quality = DomainQualityEvaluator.get_quality_score(url_lower)
        score += domain_quality * self.weights["domain_quality_multiplier"]
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    def _calculate_skill_score(self, title: str, url: str, description: str, skill: str) -> float:
        """Calculate score based on skill presence."""
        score = 0.0
        
        if skill in title:
            score += self.weights["skill_in_title"]
        
        if skill in url:
            score += self.weights["skill_in_url"]
        
        if skill in description:
            score += self.weights["skill_in_description"]
        
        return score
    
    def _calculate_level_score(self, title: str, description: str, proficiency_level: str) -> float:
        """Calculate score based on proficiency level."""
        level = proficiency_level.lower()
        if level not in PROFICIENCY_LEVEL_TERMS:
            return 0.0
        
        level_terms = PROFICIENCY_LEVEL_TERMS[level]
        
        # Check title first (higher weight)
        for term in level_terms:
            if term in title:
                return self.weights["level_in_title"]
        
        # Then check description
        for term in level_terms:
            if term in description:
                return self.weights["level_in_description"]
        
        return 0.0
    
    def _calculate_job_role_score(self, title: str, description: str, job_role: str) -> float:
        """Calculate score based on job role presence."""
        job_role_lower = job_role.lower()
        
        if job_role_lower in title:
            return self.weights["job_role_in_title"]
        elif job_role_lower in description:
            return self.weights["job_role_in_description"]
        
        return 0.0


class DomainQualityEvaluator:
    """Evaluates domain quality for scoring purposes."""
    
    @staticmethod
    def get_quality_score(url: str) -> float:
        """
        Estimate domain quality based on known educational sites.
        
        Args:
            url: Resource URL
            
        Returns:
            Domain quality score (0.0 to 1.0)
        """
        # Check top quality domains first
        for domain in TOP_QUALITY_DOMAINS:
            if domain in url:
                return DOMAIN_QUALITY_SCORES["top"]
        
        # Check medium quality domains
        for domain in MEDIUM_QUALITY_DOMAINS:
            if domain in url:
                return DOMAIN_QUALITY_SCORES["medium"]
        
        # Return default score for unknown domains
        return DOMAIN_QUALITY_SCORES["default"]


class FallbackResourceGenerator:
    """Generates fallback resources when search fails."""
    
    @staticmethod
    def generate_fallback_resources(skill: str, proficiency_level: str) -> list:
        """
        Generate fallback resources for a skill.
        
        Args:
            skill: Skill to get resources for
            proficiency_level: Proficiency level
            
        Returns:
            List of fallback resource dictionaries
        """
        from .search_config import FALLBACK_PLATFORMS
        
        resources = []
        skill_tag = skill.lower().replace(' ', '-')
        
        for idx, platform in enumerate(FALLBACK_PLATFORMS):
            resource_data = {
                "title": platform["title_template"].format(skill=skill),
                "url": platform["url_template"].format(
                    skill=skill, 
                    proficiency_level=proficiency_level,
                    skill_tag=skill_tag
                ),
                "description": platform["description_template"].format(skill=skill, proficiency_level=proficiency_level),
                "type": platform["type"],
                "source": "fallback",
                "relevance_score": 0.5,  # Medium relevance for fallbacks
                "metadata": {"fallback_rank": idx}
            }
            resources.append(resource_data)
        
        return resources 