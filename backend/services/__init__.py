"""
Services module initialization.
Provides initialization functions for creating and configuring service instances.
Refactored for single-session, local-only operation.
"""

import logging
import os
from typing import Optional, Any

# Local imports
# Remove database imports
# from backend.database.connection import init_db
from backend.utils.event_bus import EventBus
# Remove unused service imports
# from backend.services.data_management import DataManagementService
# from backend.services.session_manager import SessionManager as ServiceSessionManager
from backend.services.search_service import SearchService
# from backend.services.transcript_service import TranscriptService
from backend.services.llm_service import LLMService # Keep LLMService
from backend.agents.orchestrator import AgentSessionManager # Import AgentSessionManager
from backend.agents.config_models import SessionConfig # Import SessionConfig
from backend.config import get_logger # Import logger config


# Simplified Singleton Management
# Store instances directly in the module scope or use a simplified provider

_llm_service_instance: Optional[LLMService] = None
_event_bus_instance: Optional[EventBus] = None
_search_service_instance: Optional[SearchService] = None
_agent_session_manager_instance: Optional[AgentSessionManager] = None

logger = get_logger(__name__) # Use central logger config

def get_llm_service() -> LLMService:
    """
    Get the singleton LLMService instance.
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        logger.info("Creating singleton LLMService instance...")
        try:
            _llm_service_instance = LLMService() # Uses env vars for API key
        except ValueError as e:
            logger.error(f"LLMService initialization failed: {e}")
            raise # Re-raise critical error
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
            # Assumes API keys are in env vars (SERPAPI_API_KEY or SERPER_API_KEY)
            provider_name = os.environ.get("SEARCH_PROVIDER", "serpapi")
            _search_service_instance = SearchService(provider_name=provider_name)
        except ValueError as e:
            logger.error(f"SearchService initialization failed: {e}. Ensure API keys are set.")
            # Decide if this is critical - maybe return None or raise?
            # For now, raise as SkillAssessorAgent might depend on it.
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating SearchService: {e}")
            raise
        logger.info(f"Singleton SearchService instance created (Provider: {provider_name}).")
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
            llm_service = get_llm_service() # Depends on LLMService
            event_bus = get_event_bus()     # Depends on EventBus
            default_config = SessionConfig() # Create default config

            _agent_session_manager_instance = AgentSessionManager(
                llm_service=llm_service,
                event_bus=event_bus,
                logger=agent_logger,
                session_config=default_config
            )
        except Exception as e:
            logger.exception(f"Failed to create AgentSessionManager singleton: {e}")
            raise # Critical failure if the main agent cannot start
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
        get_search_service() # Initialize search service as well
        get_agent_session_manager() # Initialize the main agent manager
        logger.info("Core services initialized.")
    except Exception as e:
        logger.error(f"Core service initialization failed: {e}")
        # Depending on the app's needs, you might want to exit or handle this
        raise

# Remove old provider class and related functions
# class ServiceProvider:
#     ...
# def get_session_manager(): ...
# def get_data_service(): ...
# def get_transcript_service(): ...


# The following functions are obsolete and should be removed
# def get_session_manager() -> SessionManager:
#     """
#     Get the global session manager instance.
#     
#     Returns:
#         Session manager instance
#     """
#     return service_provider.session_manager
# 
# 
# def get_data_service() -> DataManagementService:
#     """
#     Get the global data management service instance.
#     
#     Returns:
#         Data management service instance
#     """
#     return service_provider.data_service
# 
# 
# def get_transcript_service() -> TranscriptService:
#     """
#     Get the transcript service instance.
#     
#     Returns:
#         TranscriptService: The transcript service instance.
#     """
#     return ServiceProvider().get("transcript_service")
# 
# # The second initialize_services and ServiceProvider class definitions are also obsolete
# def initialize_services(config: Optional[Dict[str, Any]] = None) -> ServiceProvider:
#    ...
# class ServiceProvider:
#    ... 