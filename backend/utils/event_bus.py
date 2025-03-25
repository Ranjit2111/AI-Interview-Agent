"""
Event bus module for inter-agent communication.
Implements a publish/subscribe pattern for event-based communication.
"""

import uuid
import json
from typing import Dict, List, Any, Callable, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict
import enum


class EventType(str, enum.Enum):
    """
    Enumeration of event types used in the application.
    """
    # Interview events
    INTERVIEW_START = "interview_start"
    INTERVIEW_END = "interview_end"
    INTERVIEWER_RESPONSE = "interviewer_response"
    USER_RESPONSE = "user_response"
    INTERVIEW_SUMMARY = "interview_summary"
    
    # Coaching events
    COACHING_REQUEST = "coaching_request"
    COACHING_RESPONSE = "coaching_response"
    
    # Skill assessment events
    SKILL_IDENTIFIED = "skill_identified"
    SKILL_ASSESSED = "skill_assessed"
    
    # Generic events
    ERROR = "error"
    STATUS_UPDATE = "status_update"


@dataclass
class Event:
    """
    Event class for message passing between agents.
    """
    event_type: str
    source: str
    data: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert the event to a JSON string.
        
        Returns:
            JSON string representation of the event
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """
        Create an event from a dictionary.
        
        Args:
            data: Dictionary representation of the event
            
        Returns:
            Event object
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """
        Create an event from a JSON string.
        
        Args:
            json_str: JSON string representation of the event
            
        Returns:
            Event object
        """
        return cls.from_dict(json.loads(json_str))


class EventBus:
    """
    Event bus for agent communication using a publish/subscribe pattern.
    """
    def __init__(self):
        """
        Initialize the event bus.
        """
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        # Store in history
        self.event_history.append(event)
        
        # Trim history if it gets too large
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Notify subscribers
        event_type = event.event_type
        
        # Call specific subscribers for this event type
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in subscriber callback for event type {event_type}: {e}")
        
        # Call wildcard subscribers
        if "*" in self.subscribers:
            for callback in self.subscribers["*"]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in wildcard subscriber callback: {e}")
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to (use "*" for all events)
            callback: The function to call when an event is received
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
    
    def get_event_types(self) -> Set[str]:
        """
        Get all event types that have subscribers.
        
        Returns:
            Set of event types
        """
        return set(self.subscribers.keys())
    
    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """
        Get the event history, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type:
            filtered = [e for e in self.event_history if e.event_type == event_type]
            return filtered[-limit:]
        else:
            return self.event_history[-limit:] 