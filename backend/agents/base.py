"""
Base agent module.
Provides the foundation for all specialized agents in the system.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.utils.event_bus import EventBus, Event, EventType
from backend.models.interview import InterviewSession
from backend.services.llm_service import LLMService


class AgentContext:
    """
    Context object passed to agents during processing.
    Holds session information, history, configuration, and communication channels.
    """
    def __init__(self,
                 session_id: str,
                 conversation_history: List[Dict[str, Any]],
                 session_config: InterviewSession,
                 event_bus: EventBus,
                 logger: logging.Logger,
                 user_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None
                 ):
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_history = conversation_history
        self.session_config = session_config
        self.event_bus = event_bus
        self.logger = logger
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)

    def get_last_user_message(self) -> Optional[str]:
        """Gets the content of the last user message in the history."""
        for message in reversed(self.conversation_history):
            if message.get("role") == "user":
                return message.get("content")
        return None

    def get_history_as_text(self) -> str:
        """
        Get the conversation history as a formatted text string.
        
        Returns:
            The conversation history as a formatted string
        """
        history = ""
        for message in self.conversation_history:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            history += f"{role.capitalize()}: {content}\n\n"
        
        return history.strip()
    
    def get_langchain_messages(self) -> List[Any]:
        """
        Convert conversation history to LangChain message format.
        
        Returns:
            List of LangChain message objects
        """
        messages = []
        for message in self.conversation_history:
            role = message.get("role")
            content = message.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        return messages
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary (for logging/serialization if needed).
        Note: event_bus and logger are not typically serialized.
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_history": self.conversation_history,
            "session_config": self.session_config.dict() if self.session_config else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    Provides common initialization and utilities.
    """
    def __init__(self,
                 llm_service: LLMService,
                 event_bus: Optional[EventBus] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the base agent.
        
        Args:
            llm_service: Instance of LLMService to use for language model calls.
            event_bus: Event bus for inter-agent communication.
            logger: Logger for the agent.
        """
        if not llm_service:
            raise ValueError("LLMService instance is required.")
            
        self.llm_service = llm_service
        self.llm = llm_service.get_llm()

        # Set up event bus
        self.event_bus = event_bus or EventBus()
        
        # Set up logger
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def _get_system_prompt(self) -> str:
        """
        Get the base system prompt for the agent.
        Should be overridden in subclasses for specific roles.
        
        Returns:
            System prompt string
        """
        return "You are an AI assistant."
    
    @abstractmethod
    def process(self, context: AgentContext) -> Any:
        """
        Process the given context and generate a response or perform an action.
        This is the main entry point for agent logic.
        
        Args:
            context: The current AgentContext containing history, config, etc.
            
        Returns:
            The result of the agent's processing (e.g., response text, structured data).
            The exact type depends on the specific agent implementation.
        """
        pass
    
    def publish_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """
        Publish an event to the event bus.
        
        Args:
            event_type: The type of event (use EventType enum).
            data: The event data.
        """
        if not self.event_bus:
            self.logger.warning("Event bus not available, cannot publish event.")
            return
            
        event = Event(
            event_type=event_type,
            source=self.__class__.__name__,
            data=data
        )
        self.event_bus.publish(event)
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to (use EventType enum).
            callback: The callback function to call when an event is received.
        """
        if not self.event_bus:
            self.logger.warning("Event bus not available, cannot subscribe to events.")
            return
            
        self.event_bus.subscribe(event_type, callback) 