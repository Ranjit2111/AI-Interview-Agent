"""
Services module initialization.
Provides initialization functions for creating and configuring service instances.
Refactored for single-session, local-only operation.
"""

import os
from typing import Optional


from backend.utils.event_bus import EventBus
from backend.services.search_service import SearchService
from backend.services.llm_service import LLMService
from backend.agents.orchestrator import AgentSessionManager
from backend.agents.config_models import SessionConfig
from backend.config import get_logger


_llm_service_instance: Optional[LLMService] = None
_event_bus_instance: Optional[EventBus] = None
_search_service_instance: Optional[SearchService] = None
_agent_session_manager_instance: Optional[AgentSessionManager] = None

logger = get_logger(__name__)

def get_llm_service() -> LLMService:
    """
    Get the singleton LLMService instance.
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        logger.info("Creating singleton LLMService instance...")
        try:
            _llm_service_instance = LLMService()
        except ValueError as e:
            logger.error(f"LLMService initialization failed: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating LLMService: {e}")
            raise
        logger.info("Singleton LLMService instance created.")
    return _llm_service_instance

def get_event_bus() -> EventBus:
    """
    Get the singleton EventBus instance.
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        logger.info("Creating singleton EventBus instance...")
        _event_bus_instance = EventBus()
        logger.info("Singleton EventBus instance created.")
    return _event_bus_instance

def get_search_service() -> SearchService:
    """
    Get the singleton SearchService instance.
    """
    global _search_service_instance
    if _search_service_instance is None:
        logger.info("Creating singleton SearchService instance...")
        try:
            _search_service_instance = SearchService()
        except ValueError as e:
            logger.error(f"SearchService initialization failed: {e}. Ensure API keys are set.")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating SearchService: {e}")
            raise
        logger.info(f"Singleton SearchService instance created (Provider: Serper).")
    return _search_service_instance

def get_agent_session_manager() -> AgentSessionManager:
    """
    Get the singleton AgentSessionManager instance.
    """
    global _agent_session_manager_instance
    if _agent_session_manager_instance is None:
        logger.info("Creating singleton AgentSessionManager instance...")
        try:
            agent_logger = get_logger("AgentSessionManager")
            llm_service = get_llm_service()
            event_bus = get_event_bus()
            default_config = SessionConfig()

            _agent_session_manager_instance = AgentSessionManager(
                llm_service=llm_service,
                event_bus=event_bus,
                logger=agent_logger,
                session_config=default_config
            )
        except Exception as e:
            logger.exception(f"Failed to create AgentSessionManager singleton: {e}")
            raise
        logger.info("Singleton AgentSessionManager instance created.")
    return _agent_session_manager_instance


def initialize_services() -> None:
    """
    Initialize all singleton services. Call this on application startup.
    This function now primarily ensures singletons are created eagerly if desired,
    though they will also be created on first access via get_... functions.
    It no longer returns a provider object.
    """
    logger.info("Initializing core services...")
    try:
        get_llm_service()
        get_event_bus()
        get_search_service()
        get_agent_session_manager()
        logger.info("Core services initialized.")
    except Exception as e:
        logger.error(f"Core service initialization failed: {e}")
        raise
