"""
Learning Resource Search Tool for the Coach Agent.
Provides intelligent search capabilities for finding educational resources.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from backend.services.search_service import SearchService, Resource
from backend.services.search_config import BOOK_DOMAINS


class SearchInput(BaseModel):
    """Input schema for the learning resource search tool."""
    skill: str = Field(description="The skill or topic to search for learning resources")
    proficiency_level: str = Field(
        description="The user's proficiency level: 'beginner', 'intermediate', 'advanced', or 'expert'",
        default="intermediate"
    )
    job_role: Optional[str] = Field(
        description="The job role context for the search (optional)",
        default=None
    )
    num_results: int = Field(
        description="Number of resources to return (3-10)", 
        default=8,
        ge=3,
        le=10
    )


class LearningResourceSearchTool(BaseTool):
    """
    Tool for searching learning resources based on skill gaps identified during coaching.
    Filters out paid content and focuses on free, accessible resources.
    """
    
    name: str = "learning_resource_search"
    description: str = """
    Search for learning resources related to a specific skill or topic.
    This tool finds educational content like tutorials, documentation, free courses, 
    videos, and community resources. It automatically filters out paid content 
    and focuses on freely accessible materials.
    
    Use this tool when:
    - A user needs to improve in a specific skill area
    - You want to find relevant learning materials for skill gaps
    - You need resources appropriate for the user's proficiency level
    
    Input parameters:
    - skill: The specific skill or topic to search for
    - proficiency_level: User's current level (beginner/intermediate/advanced/expert)  
    - job_role: Optional job context to make search more relevant
    - num_results: How many resources to return (3-10)
    """
    args_schema: type[BaseModel] = SearchInput
    
    def __init__(self, search_service: SearchService, logger: Optional[logging.Logger] = None):
        """
        Initialize the search tool.
        
        Args:
            search_service: Instance of SearchService for performing searches
            logger: Logger for the tool
        """
        super().__init__()
        # Store these as object attributes (not Pydantic fields)
        object.__setattr__(self, 'search_service', search_service)
        object.__setattr__(self, 'logger', logger or logging.getLogger(__name__))
    
    def _filter_free_resources(self, resources: List[Resource]) -> List[Resource]:
        """
        Filter out paid/book resources, keeping only free accessible content.
        
        Args:
            resources: List of resources from search
            
        Returns:
            Filtered list of free resources
        """
        free_resources = []
        
        for resource in resources:
            # Skip book-related domains (these are usually paid)
            url_lower = resource.url.lower()
            is_book_domain = any(domain in url_lower for domain in BOOK_DOMAINS)
            
            if is_book_domain:
                self.logger.debug(f"Filtering out book resource: {resource.title}")
                continue
            
            # Skip titles that indicate paid content
            title_lower = resource.title.lower()
            paid_indicators = ["buy", "purchase", "paid", "premium", "subscription", "kindle", "paperback"]
            has_paid_indicator = any(indicator in title_lower for indicator in paid_indicators)
            
            if has_paid_indicator:
                self.logger.debug(f"Filtering out paid resource: {resource.title}")
                continue
            
            # Keep the resource if it passes filters
            free_resources.append(resource)
        
        return free_resources
    
    def _run(self, skill: str, proficiency_level: str = "intermediate", 
             job_role: Optional[str] = None, num_results: int = 5) -> str:
        """
        Synchronous wrapper for the search operation.
        
        Returns:
            String representation of search results for the LLM
        """
        try:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - create a task and wait for it
                import concurrent.futures
                import threading
                
                # Create a future to hold the result
                future = concurrent.futures.Future()
                
                def run_async_search():
                    """Run the async search in a separate thread with its own event loop"""
                    try:
                        # Create new event loop for this thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result = new_loop.run_until_complete(
                                self._perform_search(skill, proficiency_level, job_role, num_results)
                            )
                            future.set_result(result)
                        finally:
                            new_loop.close()
                    except Exception as e:
                        future.set_exception(e)
                
                # Run in a separate thread to avoid event loop conflicts
                thread = threading.Thread(target=run_async_search)
                thread.start()
                thread.join()
                
                # Get the result
                return future.result()
                
            except RuntimeError:
                # No running loop, safe to create one
                return asyncio.run(self._perform_search(skill, proficiency_level, job_role, num_results))
            
        except Exception as e:
            self.logger.error(f"Error in sync search tool: {e}")
            return f"Search failed: {str(e)}"
    
    async def _arun(self, skill: str, proficiency_level: str = "intermediate", 
                    job_role: Optional[str] = None, num_results: int = 5) -> str:
        """
        Async implementation for LangGraph and other async contexts.
        
        Returns:
            String representation of search results for the LLM
        """
        try:
            return await self._perform_search(skill, proficiency_level, job_role, num_results)
        except Exception as e:
            self.logger.error(f"Error in async search tool: {e}")
            return f"Search failed: {str(e)}"
    
    async def _perform_search(self, skill: str, proficiency_level: str,
                             job_role: Optional[str], num_results: int) -> str:
        """
        Core search functionality used by both sync and async methods.
        
        Returns:
            Formatted search results for LLM
        """
        try:
            # Search for significantly more results than needed since we'll filter
            search_count = min(num_results * 4, 40)  # Get 4x more to account for filtering
            
            all_resources = await self.search_service.search_resources(
                skill=skill,
                proficiency_level=proficiency_level,
                job_role=job_role,
                num_results=search_count,
                use_cache=True
            )
            
            # Filter out paid content
            free_resources = self._filter_free_resources(all_resources)
            
            # Return top results, ensuring we try to meet the requested number
            final_resources = free_resources[:num_results]
            
            return self._format_results_for_llm(final_resources, skill)
            
        except Exception as e:
            self.logger.error(f"Error in search operation: {e}")
            return f"Search failed for '{skill}': {str(e)}"
    
    def _format_results_for_llm(self, resources: List[Resource], skill: str) -> str:
        """
        Format search results in a way the LLM can understand and use.
        
        Args:
            resources: List of resources found
            skill: The skill that was searched for
            
        Returns:
            Formatted string for LLM consumption
        """
        if not resources:
            return f"No suitable free learning resources found for '{skill}'. You may want to suggest the user search for more general terms or foundational concepts."
        
        result_text = f"Found {len(resources)} free learning resources for '{skill}':\n\n"
        
        for i, resource in enumerate(resources, 1):
            result_text += f"{i}. **{resource.title}**\n"
            result_text += f"   Type: {resource.resource_type}\n"
            result_text += f"   URL: {resource.url}\n"
            result_text += f"   Description: {resource.description}\n"
            result_text += f"   Relevance Score: {resource.relevance_score:.2f}\n"
            
            if resource.metadata:
                domain_quality = resource.metadata.get('domain_quality', 'unknown')
                result_text += f"   Domain Quality: {domain_quality}\n"
            
            result_text += "\n"
        
        result_text += "\nAll resources have been filtered to exclude paid content, books, and premium services."
        return result_text 