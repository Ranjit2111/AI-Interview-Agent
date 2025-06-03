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

from .search_helpers import (
    ResourceType, ResourceClassifier, RelevanceScorer, 
    DomainQualityEvaluator, FallbackResourceGenerator
)
from backend.services.rate_limiting import get_rate_limiter

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
    """Serper.dev search provider with rate limiting."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Serper provider."""
        super().__init__(api_key or SERPER_KEY)
        self.base_url = "https://google.serper.dev/search"
        self.rate_limiter = get_rate_limiter()
    
    @backoff.on_exception(backoff.expo, 
                         (httpx.HTTPError, httpx.TimeoutException),
                         max_tries=3)
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform a search using Serper.dev with rate limiting.
        
        Args:
            query: Search query string
            **kwargs: Additional search parameters
            
        Returns:
            Search results in Serper format
        """
        if not self.api_key:
            raise ValueError("Serper.dev API key not provided")
        
        # Acquire rate limit slot
        if not await self.rate_limiter.acquire_search():
            raise Exception("Search API rate limit exceeded - no available slots")
        
        try:
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
                
        finally:
            # Always release the rate limit slot
            self.rate_limiter.release_search()


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
    Provides caching and result processing with rate limiting.
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
        
        # Initialize helper components
        self.classifier = ResourceClassifier()
        self.relevance_scorer = RelevanceScorer()
        
        # Initialize cache
        self._search_cache = {}
        self._search_cache_timestamps = {}
        
        self.logger.info("Initialized search service with helper components and rate limiting")
    
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
            search_results = await self.provider.search(query, num_results=num_results)
            
            # Log the number of results from search provider
            organic_count = len(search_results.get("organic", []))
            self.logger.info(f"Search provider returned {organic_count} organic results")
            
            # Process results
            resources = self._process_search_results(
                search_results, skill, proficiency_level, job_role
            )
            
            # Cache results
            if use_cache:
                self._search_cache[cache_key] = resources
                self._search_cache_timestamps[cache_key] = now
            
            self.logger.info(f"Found {len(resources)} processed resources for: {query}")
            
            # If we got very few results, log warning but still return them
            if len(resources) < 3:
                self.logger.warning(f"Only found {len(resources)} resources for query '{query}'. This may indicate search provider issues.")
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            self.logger.warning(f"Falling back to fallback resources for skill: {skill}")
            # Return fallback resources
            fallback_data = FallbackResourceGenerator.generate_fallback_resources(skill, proficiency_level)
            fallback_resources = [Resource(**data) for data in fallback_data]
            self.logger.info(f"Generated {len(fallback_resources)} fallback resources")
            return fallback_resources
    
    def _generate_query(
        self,
        skill: str,
        proficiency_level: str,
        job_role: Optional[str] = None
    ) -> str:
        """
        Generate search query based on parameters.
        
        Args:
            skill: Skill to search for
            proficiency_level: Proficiency level
            job_role: Optional job role context
            
        Returns:
            Search query string
        """
        # Base query with skill and level
        query_parts = [
            skill,
            proficiency_level,
            "tutorial",
            "learn"
        ]
        
        # Add job role if provided
        if job_role:
            query_parts.append(job_role)
        
        return " ".join(query_parts)
    
    def _process_search_results(
        self,
        search_results: Dict[str, Any],
        skill: str,
        proficiency_level: str,
        job_role: Optional[str] = None
    ) -> List[Resource]:
        """
        Process and filter search results.
        
        Args:
            search_results: Raw search results from provider
            skill: Skill being searched
            proficiency_level: Proficiency level
            job_role: Optional job role context
            
        Returns:
            List of processed resources
        """
        resources = []
        
        # Process organic results
        organic_results = search_results.get("organic", [])
        
        for result in organic_results:
            try:
                title = result.get("title", "")
                url = result.get("link", "")
                description = result.get("snippet", "")
                
                if not all([title, url, description]):
                    continue
                
                # Classify resource type
                resource_type = self.classifier.classify(title, url, description)
                
                # Calculate relevance score
                relevance_score = self.relevance_scorer.calculate_score(
                    title, url, description, skill, proficiency_level, job_role
                )
                
                # Create resource
                resource = Resource(
                    title=title,
                    url=url,
                    description=description,
                    resource_type=resource_type,
                    source="search",
                    relevance_score=relevance_score,
                    metadata={
                        "search_rank": len(resources),
                        "domain_quality": DomainQualityEvaluator.get_quality_score(url)
                    }
                )
                
                resources.append(resource)
        
            except Exception as e:
                self.logger.warning(f"Error processing search result: {e}")
                continue
        
        # Sort by relevance score (descending)
        resources.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return resources
    
    def clear_cache(self) -> None:
        """Clear the search cache."""
        self._search_cache = {}
        self._search_cache_timestamps = {}
        self.logger.info("Search cache cleared") 