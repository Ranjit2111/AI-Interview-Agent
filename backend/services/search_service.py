"""
Web search service for finding learning resources.
Provides functionality to search for resources related to specific skills.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import httpx
from dotenv import load_dotenv
import backoff 

load_dotenv()

DEFAULT_SEARCH_PROVIDER = "serper"
SERPER_KEY = os.environ.get("SERPER_API_KEY", "")
SEARCH_CACHE_TTL = 3600 

class SearchProvider:
    """Base class for search providers."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the search provider."""
        self.api_key = api_key
    
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform a search query.
        
        Args:
            query: Search query string
            **kwargs: Additional search parameters
            
        Returns:
            Search results
        """
        raise NotImplementedError("Subclasses must implement search method")


class SerperProvider(SearchProvider):
    """Serper.dev search provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Serper provider."""
        super().__init__(api_key or SERPER_KEY)
        self.base_url = "https://serper.dev/search"
    
    @backoff.on_exception(backoff.expo, 
                         (httpx.HTTPError, httpx.TimeoutException),
                         max_tries=3)
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform a search using Serper.dev.
        
        Args:
            query: Search query string
            **kwargs: Additional search parameters
            
        Returns:
            Search results in Serper format
        """
        if not self.api_key:
            raise ValueError("Serper.dev API key not provided")
        
        params = {
            "q": query,
            "num": kwargs.get("num_results", 10),
            "gl": kwargs.get("country", "us"),
            "hl": kwargs.get("language", "en"),
        }
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url, 
                json=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()


class ResourceType:
    """Resource type enum."""
    ARTICLE = "article"
    COURSE = "course"
    VIDEO = "video"
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    BOOK = "book"
    TOOL = "tool"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class Resource:
    """Resource class for representing a learning resource."""
    
    def __init__(
        self,
        title: str,
        url: str,
        description: str,
        resource_type: str,
        source: str,
        relevance_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a resource."""
        self.title = title
        self.url = url
        self.description = description
        self.resource_type = resource_type
        self.source = source
        self.relevance_score = relevance_score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "resource_type": self.resource_type,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata
        }


class SearchService:
    """
    Service for searching and retrieving learning resources.
    Provides caching and result processing.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the search service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize provider
        self.provider = SerperProvider()
        
        # Initialize cache
        self._search_cache = {}
        self._search_cache_timestamps = {}
        
        self.logger.info(f"Initialized search service with Serper provider")
    
    async def search_resources(
        self,
        skill: str,
        proficiency_level: str,
        job_role: Optional[str] = None,
        num_results: int = 10,
        use_cache: bool = True
    ) -> List[Resource]:
        """
        Search for learning resources for a specific skill.
        
        Args:
            skill: Skill to search for
            proficiency_level: Proficiency level (beginner, intermediate, advanced, expert)
            job_role: Optional job role context
            num_results: Number of results to return
            use_cache: Whether to use cached results
            
        Returns:
            List of resources
        """
        # Generate search query
        query = self._generate_query(skill, proficiency_level, job_role)
        cache_key = f"{query}_{num_results}"
        
        # Check cache
        now = datetime.utcnow()
        if use_cache and cache_key in self._search_cache:
            cache_time = self._search_cache_timestamps.get(cache_key)
            if cache_time and (now - cache_time).total_seconds() < SEARCH_CACHE_TTL:
                self.logger.debug(f"Using cached search results for: {query}")
                return self._search_cache[cache_key]
        
        try:
            # Perform search
            self.logger.info(f"Searching for resources: {query}")
            
            # Get raw search results
            search_results = await self.provider.search(
                query,
                num_results=num_results
            )
            
            # Process results
            resources = self._process_search_results(
                search_results,
                skill,
                proficiency_level,
                job_role
            )
            
            # Sort by relevance
            resources.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            resources = resources[:num_results]
            
            # Cache results
            if use_cache:
                self._search_cache[cache_key] = resources
                self._search_cache_timestamps[cache_key] = now
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Error searching for resources: {str(e)}")
            # Return fallback resources if search fails
            return self._get_fallback_resources(skill, proficiency_level)
    
    def _generate_query(
        self,
        skill: str,
        proficiency_level: str,
        job_role: Optional[str] = None
    ) -> str:
        """
        Generate a search query based on skill and proficiency level.
        
        Args:
            skill: Skill to search for
            proficiency_level: Proficiency level
            job_role: Optional job role context
            
        Returns:
            Search query string
        """
        level_terms = {
            "beginner": ["beginner", "introduction", "basics", "learn", "start"],
            "basic": ["beginner", "introduction", "basics", "learn", "start"],
            "intermediate": ["intermediate", "improve", "practice", "tutorial"],
            "advanced": ["advanced", "expert", "mastering", "deep dive"],
            "expert": ["expert", "mastering", "advanced techniques", "professional"]
        }
        
        # Get appropriate level terms
        level = proficiency_level.lower()
        terms = level_terms.get(level, level_terms["intermediate"])
        level_term = terms[0]
        
        # Base query
        query = f"{skill} {level_term} tutorial resources"
        
        # Add job role context if provided
        if job_role:
            query += f" for {job_role}"
        
        return query
    
    def _process_search_results(
        self,
        search_results: Dict[str, Any],
        skill: str,
        proficiency_level: str,
        job_role: Optional[str] = None
    ) -> List[Resource]:
        """
        Process raw search results into resources.
        
        Args:
            search_results: Raw search results
            skill: The skill being searched
            proficiency_level: The proficiency level
            job_role: Optional job role context
            
        Returns:
            List of processed resources
        """
        resources = []
        
        # Handle Serper results
        if "organic" in search_results:
            organic_results = search_results["organic"]
            
            for result in organic_results:
                # Extract basic information
                title = result.get("title", "")
                url = result.get("link", "")
                snippet = result.get("snippet", "")
                
                if not (title and url):
                    continue
                
                # Determine resource type
                resource_type = self._classify_resource_type(title, url, snippet)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance(
                    title, url, snippet, skill, proficiency_level, job_role
                )
                
                # Create resource
                resource = Resource(
                    title=title,
                    url=url,
                    description=snippet,
                    resource_type=resource_type,
                    source="serper",
                    relevance_score=relevance_score,
                    metadata={
                        "position": result.get("position")
                    }
                )
                
                resources.append(resource)
        
        return resources
    
    def _classify_resource_type(
        self,
        title: str,
        url: str,
        description: str
    ) -> str:
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
        description_lower = description.lower()
        
        # Check for courses
        course_indicators = ["course", "class", "learn", "training", "bootcamp", "academy"]
        course_domains = ["coursera.org", "udemy.com", "edx.org", "pluralsight.com", 
                         "linkedin.com/learning", "udacity.com", "skillshare.com"]
        
        if any(indicator in title_lower for indicator in course_indicators) or \
           any(domain in url_lower for domain in course_domains):
            return ResourceType.COURSE
        
        # Check for videos
        video_indicators = ["video", "watch", "tutorial"]
        video_domains = ["youtube.com", "vimeo.com", "youtube", "youtu.be"]
        
        if any(indicator in title_lower for indicator in video_indicators) or \
           any(domain in url_lower for domain in video_domains):
            return ResourceType.VIDEO
        
        # Check for documentation
        doc_indicators = ["documentation", "docs", "reference", "manual", "guide"]
        doc_domains = ["docs.", ".io/docs", "developer.", "reference"]
        
        if any(indicator in title_lower for indicator in doc_indicators) or \
           any(domain in url_lower for domain in doc_domains):
            return ResourceType.DOCUMENTATION
        
        # Check for tutorials
        tutorial_indicators = ["tutorial", "how to", "guide", "learn", "step by step"]
        
        if any(indicator in title_lower for indicator in tutorial_indicators):
            return ResourceType.TUTORIAL
        
        # Check for communities
        community_indicators = ["forum", "community", "discussion", "stack overflow", "reddit"]
        community_domains = ["stackoverflow.com", "reddit.com", "forum.", "community."]
        
        if any(indicator in title_lower for indicator in community_indicators) or \
           any(domain in url_lower for domain in community_domains):
            return ResourceType.COMMUNITY
        
        # Check for books
        book_indicators = ["book", "ebook", "reading", "publication"]
        book_domains = ["amazon.com", "goodreads.com", "oreilly.com", "manning.com"]
        
        if any(indicator in title_lower for indicator in book_indicators) or \
           any(domain in url_lower for domain in book_domains):
            return ResourceType.BOOK
        
        # Default to article
        return ResourceType.ARTICLE
    
    def _calculate_relevance(
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
        # Initialize score
        score = 0.0
        
        # Prepare text for matching
        title_lower = title.lower()
        url_lower = url.lower()
        description_lower = description.lower()
        skill_lower = skill.lower()
        
        # Check for skill in title (high importance)
        if skill_lower in title_lower:
            score += 0.4
        
        # Check for skill in URL (medium importance)
        if skill_lower in url_lower:
            score += 0.2
        
        # Check for skill in description (low importance)
        if skill_lower in description_lower:
            score += 0.1
        
        # Check for proficiency level in title or description
        level_terms = {
            "beginner": ["beginner", "introduction", "basics", "start", "learn"],
            "basic": ["beginner", "introduction", "basics", "start", "learn"],
            "intermediate": ["intermediate", "improve", "practice"],
            "advanced": ["advanced", "expert", "mastering", "deep dive"],
            "expert": ["expert", "mastering", "advanced techniques", "professional"]
        }
        
        level = proficiency_level.lower()
        if level in level_terms:
            for term in level_terms[level]:
                if term in title_lower:
                    score += 0.15
                    break
                elif term in description_lower:
                    score += 0.05
                    break
        
        # Check for job role if provided
        if job_role:
            job_role_lower = job_role.lower()
            if job_role_lower in title_lower:
                score += 0.15
            elif job_role_lower in description_lower:
                score += 0.05
        
        # Adjust based on domain quality
        domain_quality = self._get_domain_quality(url_lower)
        score += domain_quality * 0.1
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    def _get_domain_quality(self, url: str) -> float:
        """
        Estimate domain quality based on known educational sites.
        
        Args:
            url: Resource URL
            
        Returns:
            Domain quality score (0.0 to 1.0)
        """
        # High-quality educational domains
        top_domains = [
            "github.com", "stackoverflow.com", "mdn.mozilla.org", "freecodecamp.org",
            "coursera.org", "udemy.com", "pluralsight.com", "edx.org",
            "medium.com", "dev.to", "docs.microsoft.com", "developer.mozilla.org",
            "w3schools.com", "geeksforgeeks.org", "youtube.com", "linkedin.com/learning",
            "udacity.com", "tutorialspoint.com", "khanacademy.org", "harvard.edu",
            "mit.edu", "stanford.edu", "educative.io", "reddit.com", "hackernoon.com"
        ]
        
        for domain in top_domains:
            if domain in url:
                return 1.0
        
        # Medium-quality domains - generic educational sites
        medium_domains = [
            "guru99.com", "javatpoint.com", "educba.com", "simplilearn.com", 
            "educba.com", "bitdegree.org", "digitalocean.com/community/tutorials",
            "towardsdatascience.com", "css-tricks.com", "hackr.io", "baeldung.com",
            "tutorialrepublic.com", "programiz.com", "learnpython.org"
        ]
        
        for domain in medium_domains:
            if domain in url:
                return 0.7
        
        # Return default score for unknown domains
        return 0.4
    
    def _get_fallback_resources(
        self,
        skill: str,
        proficiency_level: str
    ) -> List[Resource]:
        """
        Get fallback resources when search fails.
        
        Args:
            skill: Skill to get resources for
            proficiency_level: Proficiency level
            
        Returns:
            List of fallback resources
        """
        # Common educational platforms
        platforms = [
            {
                "title": f"Learn {skill} on Coursera",
                "url": f"https://www.coursera.org/courses?query={skill}",
                "description": f"Find online courses on {skill} from leading universities and companies.",
                "type": ResourceType.COURSE
            },
            {
                "title": f"{skill} tutorials on Udemy",
                "url": f"https://www.udemy.com/courses/search/?q={skill}",
                "description": f"Explore a wide range of {skill} courses for all skill levels.",
                "type": ResourceType.COURSE
            },
            {
                "title": f"{skill} on YouTube",
                "url": f"https://www.youtube.com/results?search_query={skill}+{proficiency_level}+tutorial",
                "description": f"Watch free video tutorials on {skill} at {proficiency_level} level.",
                "type": ResourceType.VIDEO
            },
            {
                "title": f"{skill} community on Stack Overflow",
                "url": f"https://stackoverflow.com/questions/tagged/{skill.lower().replace(' ', '-')}",
                "description": f"Find answers to your {skill} questions from the developer community.",
                "type": ResourceType.COMMUNITY
            },
            {
                "title": f"{skill} on GitHub",
                "url": f"https://github.com/topics/{skill.lower().replace(' ', '-')}",
                "description": f"Explore {skill} projects, libraries, and resources on GitHub.",
                "type": ResourceType.COMMUNITY
            }
        ]
        
        # Convert to Resource objects
        resources = []
        for idx, platform in enumerate(platforms):
            resource = Resource(
                title=platform["title"],
                url=platform["url"],
                description=platform["description"],
                resource_type=platform["type"],
                source="fallback",
                relevance_score=0.5,  # Medium relevance for fallbacks
                metadata={"fallback_rank": idx}
            )
            resources.append(resource)
        
        return resources
    
    def clear_cache(self) -> None:
        """Clear the search cache."""
        self._search_cache = {}
        self._search_cache_timestamps = {}
        self.logger.info("Search cache cleared") 