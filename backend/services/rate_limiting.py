"""
Rate limiting service for external API concurrency management.
Provides semaphore-based limiting for AssemblyAI, Polly, Deepgram, and Search APIs.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from backend.config import get_logger

logger = get_logger(__name__)


class APIRateLimiter:
    """
    Manages rate limiting for external APIs using semaphores.
    Prevents overwhelming external services with concurrent requests.
    """
    
    def __init__(self):
        # API concurrency limits based on free tier documentation
        self.assemblyai_limit = 5  # 5 concurrent transcriptions
        self.polly_limit = 26      # 26 concurrent generative voice requests
        self.deepgram_limit = 10   # Conservative limit for streaming connections
        self.search_limit = 3      # Conservative limit for search API (Serper.dev)
        
        # Initialize semaphores directly
        self.assemblyai_semaphore = asyncio.Semaphore(self.assemblyai_limit)
        self.polly_semaphore = asyncio.Semaphore(self.polly_limit)
        self.deepgram_semaphore = asyncio.Semaphore(self.deepgram_limit)
        self.search_semaphore = asyncio.Semaphore(self.search_limit)
        
        # Rate limiting metrics
        self.api_usage_stats = {
            'assemblyai': {'active': 0, 'total_requests': 0, 'errors': 0},
            'polly': {'active': 0, 'total_requests': 0, 'errors': 0},
            'deepgram': {'active': 0, 'total_requests': 0, 'errors': 0},
            'search': {'active': 0, 'total_requests': 0, 'errors': 0}
        }
        
        logger.info("APIRateLimiter initialized with limits: AssemblyAI=5, Polly=26, Deepgram=10, Search=3")
    
    async def acquire_assemblyai(self) -> bool:
        """
        Acquire a slot for AssemblyAI API call.
        
        Returns:
            bool: True if slot acquired successfully
        """
        try:
            # Use timeout to prevent indefinite hanging in production
            await asyncio.wait_for(self.assemblyai_semaphore.acquire(), timeout=5.0)
            self.api_usage_stats['assemblyai']['active'] += 1
            self.api_usage_stats['assemblyai']['total_requests'] += 1
            logger.debug(f"AssemblyAI slot acquired. Active: {self.api_usage_stats['assemblyai']['active']}")
            return True
        except asyncio.TimeoutError:
            logger.warning("AssemblyAI service unavailable - all slots occupied")
            self.api_usage_stats['assemblyai']['errors'] += 1
            return False
        except Exception as e:
            logger.error(f"Failed to acquire AssemblyAI slot: {e}")
            self.api_usage_stats['assemblyai']['errors'] += 1
            return False
    
    def release_assemblyai(self):
        """Release AssemblyAI API slot."""
        try:
            self.assemblyai_semaphore.release()
            self.api_usage_stats['assemblyai']['active'] -= 1
            logger.debug(f"AssemblyAI slot released. Active: {self.api_usage_stats['assemblyai']['active']}")
        except Exception as e:
            logger.error(f"Failed to release AssemblyAI slot: {e}")
    
    async def acquire_polly(self) -> bool:
        """
        Acquire a slot for Amazon Polly API call.
        
        Returns:
            bool: True if slot acquired successfully
        """
        try:
            # Use timeout to prevent indefinite hanging in production
            await asyncio.wait_for(self.polly_semaphore.acquire(), timeout=5.0)
            self.api_usage_stats['polly']['active'] += 1
            self.api_usage_stats['polly']['total_requests'] += 1
            logger.debug(f"Polly slot acquired. Active: {self.api_usage_stats['polly']['active']}")
            return True
        except asyncio.TimeoutError:
            logger.warning("Polly service unavailable - all slots occupied")
            self.api_usage_stats['polly']['errors'] += 1
            return False
        except Exception as e:
            logger.error(f"Failed to acquire Polly slot: {e}")
            self.api_usage_stats['polly']['errors'] += 1
            return False
    
    def release_polly(self):
        """Release Amazon Polly API slot."""
        try:
            self.polly_semaphore.release()
            self.api_usage_stats['polly']['active'] -= 1
            logger.debug(f"Polly slot released. Active: {self.api_usage_stats['polly']['active']}")
        except Exception as e:
            logger.error(f"Failed to release Polly slot: {e}")
    
    async def acquire_deepgram(self) -> bool:
        """
        Acquire a slot for Deepgram API call.
        
        Returns:
            bool: True if slot acquired successfully
        """
        try:
            # Use timeout to prevent indefinite hanging in production
            await asyncio.wait_for(self.deepgram_semaphore.acquire(), timeout=5.0)
            self.api_usage_stats['deepgram']['active'] += 1
            self.api_usage_stats['deepgram']['total_requests'] += 1
            logger.debug(f"Deepgram slot acquired. Active: {self.api_usage_stats['deepgram']['active']}")
            return True
        except asyncio.TimeoutError:
            logger.warning("Deepgram service unavailable - all slots occupied")
            self.api_usage_stats['deepgram']['errors'] += 1
            return False
        except Exception as e:
            logger.error(f"Failed to acquire Deepgram slot: {e}")
            self.api_usage_stats['deepgram']['errors'] += 1
            return False
    
    def release_deepgram(self):
        """Release Deepgram API slot."""
        try:
            self.deepgram_semaphore.release()
            self.api_usage_stats['deepgram']['active'] -= 1
            logger.debug(f"Deepgram slot released. Active: {self.api_usage_stats['deepgram']['active']}")
        except Exception as e:
            logger.error(f"Failed to release Deepgram slot: {e}")
    
    async def acquire_search(self) -> bool:
        """
        Acquire a slot for Search API call (Serper.dev).
        
        Returns:
            bool: True if slot acquired successfully
        """
        try:
            # Use timeout to prevent indefinite hanging in production
            await asyncio.wait_for(self.search_semaphore.acquire(), timeout=5.0)
            self.api_usage_stats['search']['active'] += 1
            self.api_usage_stats['search']['total_requests'] += 1
            logger.debug(f"Search slot acquired. Active: {self.api_usage_stats['search']['active']}")
            return True
        except asyncio.TimeoutError:
            logger.warning("Search service unavailable - all slots occupied")
            self.api_usage_stats['search']['errors'] += 1
            return False
        except Exception as e:
            logger.error(f"Failed to acquire Search slot: {e}")
            self.api_usage_stats['search']['errors'] += 1
            return False
    
    def release_search(self):
        """Release Search API slot."""
        try:
            self.search_semaphore.release()
            self.api_usage_stats['search']['active'] -= 1
            logger.debug(f"Search slot released. Active: {self.api_usage_stats['search']['active']}")
        except Exception as e:
            logger.error(f"Failed to release Search slot: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.
        
        Returns:
            Dict containing usage stats for all APIs
        """
        return {
            'assemblyai': {
                'active_connections': self.api_usage_stats['assemblyai']['active'],
                'available_slots': self.assemblyai_semaphore._value,
                'total_requests': self.api_usage_stats['assemblyai']['total_requests'],
                'errors': self.api_usage_stats['assemblyai']['errors']
            },
            'polly': {
                'active_connections': self.api_usage_stats['polly']['active'],
                'available_slots': self.polly_semaphore._value,
                'total_requests': self.api_usage_stats['polly']['total_requests'],
                'errors': self.api_usage_stats['polly']['errors']
            },
            'deepgram': {
                'active_connections': self.api_usage_stats['deepgram']['active'],
                'available_slots': self.deepgram_semaphore._value,
                'total_requests': self.api_usage_stats['deepgram']['total_requests'],
                'errors': self.api_usage_stats['deepgram']['errors']
            },
            'search': {
                'active_connections': self.api_usage_stats['search']['active'],
                'available_slots': self.search_semaphore._value,
                'total_requests': self.api_usage_stats['search']['total_requests'],
                'errors': self.api_usage_stats['search']['errors']
            }
        }
    
    def is_api_available(self, api_name: str) -> bool:
        """
        Check if API has available slots.
        
        Args:
            api_name: Name of the API ('assemblyai', 'polly', 'deepgram', 'search')
            
        Returns:
            bool: True if slots are available
        """
        if api_name == 'assemblyai':
            return self.assemblyai_semaphore._value > 0
        elif api_name == 'polly':
            return self.polly_semaphore._value > 0
        elif api_name == 'deepgram':
            return self.deepgram_semaphore._value > 0
        elif api_name == 'search':
            return self.search_semaphore._value > 0
        else:
            return False


# Global rate limiter instance
_rate_limiter: Optional[APIRateLimiter] = None


def get_rate_limiter() -> APIRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        logger.debug("Creating global rate limiter instance")
        _rate_limiter = APIRateLimiter()
    return _rate_limiter