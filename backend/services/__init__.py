"""
Services module initialization.
Provides initialization functions for creating and configuring service instances.
"""

import logging
import os
from typing import Dict, Any, Optional

# Local imports
from backend.database.connection import init_db
from backend.utils.event_bus import EventBus
from backend.utils.vector_store import VectorStore
from backend.services.data_management import DataManagementService
from backend.services.session_manager import SessionManager
from backend.services.search_service import SearchService
from backend.services.transcript_service import TranscriptService


class ServiceProvider:
    """
    Service provider class that manages global service instances.
    Implements a singleton pattern for service access.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize service provider and register services."""
        if not hasattr(self, "initialized"):
            self.logger = logging.getLogger(__name__)
            self.logger.info("Initializing service provider")
            
            # Configure service registry
            self.services = {}
            
            # Initialize event bus
            self.event_bus = EventBus()
            self.services["event_bus"] = self.event_bus
            
            # Initialize session manager
            self.session_manager = SessionManager(event_bus=self.event_bus)
            self.services["session_manager"] = self.session_manager
            
            # Initialize data management service
            self.data_service = DataManagementService(event_bus=self.event_bus)
            self.services["data_service"] = self.data_service
            
            # Initialize search service
            self.search_service = SearchService()
            self.services["search_service"] = self.search_service
            
            # Initialize transcript service
            
            # Configure vector store for transcript embeddings
            vector_store_dir = os.environ.get("VECTOR_DB_PATH", "./data/vector_store")
            embedding_model = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            
            vector_store = VectorStore(
                embedding_model_name=embedding_model,
                index_dir=vector_store_dir
            )
            
            self.transcript_service = TranscriptService(
                event_bus=self.event_bus,
                vector_store=vector_store,
                embedding_model_name=embedding_model,
                vector_store_dir=vector_store_dir
            )
            self.services["transcript_service"] = self.transcript_service
            
            # Mark as initialized
            self.initialized = True
            self.logger.info("Service provider initialized successfully")
    
    def get(self, service_name: str) -> Any:
        """
        Get a service instance by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service not found
        """
        if service_name not in self.services:
            raise KeyError(f"Service {service_name} not found")
        
        return self.services[service_name]
    
    def configure_logging(self, level=logging.INFO):
        """
        Configure logging for all services.
        
        Args:
            level: Logging level
        """
        # Configure root logger
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Update service loggers
        self.logger.setLevel(level)
        for service_name, service in self.services.items():
            if hasattr(service, "logger"):
                service.logger.setLevel(level)


# Global service provider instance
service_provider = ServiceProvider()


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        Event bus instance
    """
    return service_provider.event_bus


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        Session manager instance
    """
    return service_provider.session_manager


def get_data_service() -> DataManagementService:
    """
    Get the global data management service instance.
    
    Returns:
        Data management service instance
    """
    return service_provider.data_service


def get_search_service() -> SearchService:
    """
    Get the global search service instance.
    
    Returns:
        Search service instance
    """
    return service_provider.search_service


def get_transcript_service() -> TranscriptService:
    """
    Get the transcript service instance.
    
    Returns:
        TranscriptService: The transcript service instance.
    """
    return ServiceProvider().get("transcript_service")


def initialize_services(config: Optional[Dict[str, Any]] = None) -> ServiceProvider:
    """
    Initialize all services and return the service provider.
    
    Args:
        config: Optional configuration dictionary.
        
    Returns:
        ServiceProvider: The service provider instance.
    """
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
    
    # Create and return service provider
    provider = ServiceProvider()
    provider.configure_logging()
    
    # Apply configuration if provided
    if config:
        # Apply configuration to services as needed
        pass
    
    return provider 