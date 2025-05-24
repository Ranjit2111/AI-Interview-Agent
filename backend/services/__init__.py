"""
Services module initialization.
Provides initialization functions for creating and configuring service instances.
Refactored for single-session, local-only operation with improved singleton pattern.
"""

import os
from typing import Optional

from backend.utils.event_bus import EventBus
from backend.services.search_service import SearchService
from backend.services.llm_service import LLMService
from backend.agents.config_models import SessionConfig
from backend.config import get_logger


class ServiceRegistry:
    """Registry for singleton service instances."""
    
    def __init__(self):
        self._llm_service: Optional[LLMService] = None
        self._event_bus: Optional[EventBus] = None
        self._search_service: Optional[SearchService] = None
        self._agent_session_manager = None
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

    def get_agent_session_manager(self):
        """Get the singleton AgentSessionManager instance."""
        if self._agent_session_manager is None:
            # Import here to avoid circular imports
            from backend.agents.orchestrator import AgentSessionManager
            
            self.logger.info("Creating singleton AgentSessionManager instance...")
            try:
                agent_logger = get_logger("AgentSessionManager")
                llm_service = self.get_llm_service()
                event_bus = self.get_event_bus()
                default_config = SessionConfig()

                self._agent_session_manager = AgentSessionManager(
                    llm_service=llm_service,
                    event_bus=event_bus,
                    logger=agent_logger,
                    session_config=default_config
                )
            except Exception as e:
                self.logger.exception(f"Failed to create AgentSessionManager singleton: {e}")
                raise
            self.logger.info("Singleton AgentSessionManager instance created.")
        return self._agent_session_manager

    def initialize_all_services(self) -> None:
        """Initialize all singleton services. Call this on application startup."""
        self.logger.info("Initializing core services...")
        try:
            self.get_llm_service()
            self.get_event_bus()
            self.get_search_service()
            self.get_agent_session_manager()
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

def get_agent_session_manager():
    """Get the singleton AgentSessionManager instance."""
    return _service_registry.get_agent_session_manager()

def initialize_services() -> None:
    """Initialize all singleton services. Call this on application startup."""
    _service_registry.initialize_all_services()
