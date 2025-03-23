"""
Services module initialization.
Provides initialization functions for creating and configuring service instances.
"""

import logging
from typing import Dict, Any, Optional

from backend.utils.event_bus import EventBus
from backend.services.data_management import DataManagementService
from backend.services.session_manager import SessionManager
from backend.services.search_service import SearchService


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
        if self._initialized:
            return
        
        # Create logger
        self.logger = logging.getLogger(__name__)
        
        # Create event bus
        self.event_bus = EventBus()
        
        # Create services
        self.session_manager = SessionManager(
            event_bus=self.event_bus,
            logger=self.logger
        )
        
        self.data_service = DataManagementService(
            event_bus=self.event_bus,
            logger=self.logger
        )
        
        # Create search service
        self.search_service = SearchService(
            logger=self.logger
        )
        
        # Track service instances
        self.services = {
            "event_bus": self.event_bus,
            "session_manager": self.session_manager,
            "data_service": self.data_service,
            "search_service": self.search_service
        }
        
        self._initialized = True
    
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


def initialize_services(config: Optional[Dict[str, Any]] = None) -> ServiceProvider:
    """
    Initialize all services with optional configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Service provider instance
    """
    # Configure logging
    log_level = logging.INFO
    if config and "log_level" in config:
        log_level = config["log_level"]
    
    service_provider.configure_logging(level=log_level)
    
    # Log initialization
    service_provider.logger.info("Initializing services...")
    
    # Return service provider
    return service_provider 