"""
Services module initialization.
Provides initialization functions for creating and configuring service instances.
Refactored for multi-session support with database persistence and API rate limiting.
"""

import os
from typing import Optional

from backend.utils.event_bus import EventBus
from backend.services.search_service import SearchService
from backend.services.llm_service import LLMService
from backend.database.db_manager import DatabaseManager
from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.services.rate_limiting import APIRateLimiter
from backend.config import get_logger


class ServiceRegistry:
    """Registry for singleton service instances."""
    
    def __init__(self):
        self._llm_service: Optional[LLMService] = None
        self._event_bus: Optional[EventBus] = None
        self._search_service: Optional[SearchService] = None
        self._database_manager: Optional[DatabaseManager] = None
        self._session_registry: Optional[ThreadSafeSessionRegistry] = None
        self._rate_limiter: Optional[APIRateLimiter] = None
        self.logger = get_logger(__name__)
    
    def get_llm_service(self) -> LLMService:
        """Get the singleton LLMService instance."""
        if self._llm_service is None:
            self.logger.info("Creating singleton LLMService instance...")
            try:
                self._llm_service = LLMService()
            except ValueError as e:
                self.logger.error(f"LLMService initialization failed: {e}")
                raise
            except Exception as e:
                self.logger.exception(f"Unexpected error creating LLMService: {e}")
                raise
            self.logger.info("Singleton LLMService instance created.")
        return self._llm_service

    def get_event_bus(self) -> EventBus:
        """Get the singleton EventBus instance."""
        if self._event_bus is None:
            self.logger.info("Creating singleton EventBus instance...")
            self._event_bus = EventBus()
            self.logger.info("Singleton EventBus instance created.")
        return self._event_bus

    def get_search_service(self) -> SearchService:
        """Get the singleton SearchService instance."""
        if self._search_service is None:
            self.logger.info("Creating singleton SearchService instance...")
            try:
                self._search_service = SearchService()
            except ValueError as e:
                self.logger.error(f"SearchService initialization failed: {e}. Ensure API keys are set.")
                raise
            except Exception as e:
                self.logger.exception(f"Unexpected error creating SearchService: {e}")
                raise
            self.logger.info(f"Singleton SearchService instance created (Provider: Serper).")
        return self._search_service

    def get_database_manager(self) -> DatabaseManager:
        """Get the singleton DatabaseManager instance."""
        if self._database_manager is None:
            self.logger.info("Creating singleton DatabaseManager instance...")
            try:
                self._database_manager = DatabaseManager()
            except ValueError as e:
                self.logger.error(f"DatabaseManager initialization failed: {e}. Ensure Supabase credentials are set.")
                raise
            except Exception as e:
                self.logger.exception(f"Unexpected error creating DatabaseManager: {e}")
                raise
            self.logger.info("Singleton DatabaseManager instance created.")
        return self._database_manager

    def get_session_registry(self) -> ThreadSafeSessionRegistry:
        """Get the singleton ThreadSafeSessionRegistry instance."""
        if self._session_registry is None:
            self.logger.info("Creating singleton ThreadSafeSessionRegistry instance...")
            try:
                database_manager = self.get_database_manager()
                llm_service = self.get_llm_service()
                event_bus = self.get_event_bus()
                
                self._session_registry = ThreadSafeSessionRegistry(
                    db_manager=database_manager,
                    llm_service=llm_service,
                    event_bus=event_bus
                )
            except Exception as e:
                self.logger.exception(f"Failed to create ThreadSafeSessionRegistry: {e}")
                raise
            self.logger.info("Singleton ThreadSafeSessionRegistry instance created.")
        return self._session_registry

    def get_rate_limiter(self) -> APIRateLimiter:
        """Get the singleton APIRateLimiter instance."""
        if self._rate_limiter is None:
            self.logger.info("Creating singleton APIRateLimiter instance...")
            try:
                self._rate_limiter = APIRateLimiter()
            except Exception as e:
                self.logger.exception(f"Failed to create APIRateLimiter: {e}")
                raise
            self.logger.info("Singleton APIRateLimiter instance created.")
        return self._rate_limiter

    def initialize_all_services(self) -> None:
        """Initialize all singleton services. Call this on application startup."""
        self.logger.info("Initializing core services...")
        try:
            self.get_llm_service()
            self.get_event_bus()
            self.get_search_service()
            self.get_database_manager()
            self.get_session_registry()
            self.get_rate_limiter()
            self.logger.info("Core services initialized.")
        except Exception as e:
            self.logger.error(f"Core service initialization failed: {e}")
            raise


# Global registry instance
_service_registry = ServiceRegistry()

# Convenience functions for backward compatibility
def get_llm_service() -> LLMService:
    """Get the singleton LLMService instance."""
    return _service_registry.get_llm_service()

def get_event_bus() -> EventBus:
    """Get the singleton EventBus instance."""
    return _service_registry.get_event_bus()

def get_search_service() -> SearchService:
    """Get the singleton SearchService instance."""
    return _service_registry.get_search_service()

def get_database_manager() -> DatabaseManager:
    """Get the singleton DatabaseManager instance."""
    return _service_registry.get_database_manager()

def get_session_registry() -> ThreadSafeSessionRegistry:
    """Get the singleton ThreadSafeSessionRegistry instance."""
    return _service_registry.get_session_registry()

def get_rate_limiter() -> APIRateLimiter:
    """Get the singleton APIRateLimiter instance."""
    return _service_registry.get_rate_limiter()

def initialize_services() -> None:
    """Initialize all singleton services. Call this on application startup."""
    _service_registry.initialize_all_services()
