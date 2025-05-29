"""
Rate limiting service for external API concurrency management.
Provides semaphore-based limiting for AssemblyAI, Polly, and Deepgram.
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
        # Lazy initialization - create semaphores on first use to avoid event loop issues
        self._assemblyai_semaphore: Optional[asyncio.Semaphore] = None
        self._polly_semaphore: Optional[asyncio.Semaphore] = None
        self._deepgram_semaphore: Optional[asyncio.Semaphore] = None
        
        # API concurrency limits based on free tier documentation
        self.assemblyai_limit = 5  # 5 concurrent transcriptions
        self.polly_limit = 26      # 26 concurrent generative voice requests
        self.deepgram_limit = 10   # Conservative limit for streaming connections
        
        # Rate limiting metrics
        self.api_usage_stats = {
            'assemblyai': {'active': 0, 'total_requests': 0, 'errors': 0},
            'polly': {'active': 0, 'total_requests': 0, 'errors': 0},
            'deepgram': {'active': 0, 'total_requests': 0, 'errors': 0}
        }
        
        try:
            logger.info("APIRateLimiter initialized with limits: AssemblyAI=5, Polly=26, Deepgram=10")
        except Exception:
            # Ignore logging errors during initialization
            pass
    
    @property
    def assemblyai_semaphore(self) -> asyncio.Semaphore:
        """Get or create AssemblyAI semaphore."""
        if self._assemblyai_semaphore is None:
            self._assemblyai_semaphore = asyncio.Semaphore(self.assemblyai_limit)
        return self._assemblyai_semaphore
    
    @property
    def polly_semaphore(self) -> asyncio.Semaphore:
        """Get or create Polly semaphore."""
        if self._polly_semaphore is None:
            self._polly_semaphore = asyncio.Semaphore(self.polly_limit)
        return self._polly_semaphore
    
    @property
    def deepgram_semaphore(self) -> asyncio.Semaphore:
        """Get or create Deepgram semaphore."""
        if self._deepgram_semaphore is None:
            self._deepgram_semaphore = asyncio.Semaphore(self.deepgram_limit)
        return self._deepgram_semaphore
    
    async def acquire_assemblyai(self) -> bool:
        """
        Acquire a slot for AssemblyAI API call.
        
        Returns:
            bool: True if slot acquired successfully
        """
        try:
            await self.assemblyai_semaphore.acquire()
            self.api_usage_stats['assemblyai']['active'] += 1
            self.api_usage_stats['assemblyai']['total_requests'] += 1
            logger.debug(f"AssemblyAI slot acquired. Active: {self.api_usage_stats['assemblyai']['active']}")
            return True
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
            await self.polly_semaphore.acquire()
            self.api_usage_stats['polly']['active'] += 1
            self.api_usage_stats['polly']['total_requests'] += 1
            logger.debug(f"Polly slot acquired. Active: {self.api_usage_stats['polly']['active']}")
            return True
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
            await self.deepgram_semaphore.acquire()
            self.api_usage_stats['deepgram']['active'] += 1
            self.api_usage_stats['deepgram']['total_requests'] += 1
            logger.debug(f"Deepgram slot acquired. Active: {self.api_usage_stats['deepgram']['active']}")
            return True
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
            }
        }
    
    def is_api_available(self, api_name: str) -> bool:
        """
        Check if API has available slots.
        
        Args:
            api_name: Name of the API ('assemblyai', 'polly', 'deepgram')
            
        Returns:
            bool: True if slots are available
        """
        if api_name == 'assemblyai':
            return self.assemblyai_semaphore._value > 0
        elif api_name == 'polly':
            return self.polly_semaphore._value > 0
        elif api_name == 'deepgram':
            return self.deepgram_semaphore._value > 0
        else:
            return False


# Global rate limiter instance
_rate_limiter: Optional[APIRateLimiter] = None


def get_rate_limiter() -> APIRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = APIRateLimiter()
    return _rate_limiter