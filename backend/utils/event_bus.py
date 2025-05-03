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
    # Session Lifecycle
    SESSION_START = "session_start" # Published by AgentSessionManager on init
    SESSION_END = "session_end"     # Published by AgentSessionManager on end_interview call
    SESSION_RESET = "session_reset" # Published by AgentSessionManager on reset_session call
    AGENT_LOAD = "agent_load"       # Published by AgentSessionManager when an agent is lazy-loaded

    # Core Interaction
    USER_MESSAGE = "user_message" # Published by AgentSessionManager when user message received
    ASSISTANT_RESPONSE = "assistant_response" # Published by AgentSessionManager after getting agent response

    # Agent Specific - Interviewer
    INTERVIEWER_RESPONSE = "interviewer_response" # Published by InterviewerAgent (contains question)
    INTERVIEW_COMPLETED = "interview_completed" # Published by InterviewerAgent when done
    # INTERVIEW_SUMMARY = "interview_summary" # Potentially published by Interviewer or Coach? Review usage.

    # Agent Specific - Coach
    COACHING_REQUEST = "coaching_request" # Published via ServiceSessionManager proxy, handled by CoachAgent
    COACH_FEEDBACK = "coach_feedback"     # Published by CoachAgent with feedback
    COACH_ANALYSIS = "coach_analysis"     # Published by CoachAgent with structured analysis

    # Agent Specific - Skill Assessor
    SKILL_ASSESSMENT = "skill_assessment" # Published by SkillAssessorAgent (e.g., with final profile or updates)
    # SKILL_IDENTIFIED = "skill_identified" # Potentially useful for real-time feedback, but maybe covered by SKILL_ASSESSMENT
    # SKILL_ASSESSED = "skill_assessed"

    # Data / Service Events
    TRANSCRIPT_CREATED = "transcript_created" # Published by TranscriptService
    TRANSCRIPT_UPDATED = "transcript_updated" # Published by TranscriptService
    TRANSCRIPT_DELETED = "transcript_deleted" # Published by TranscriptService
    SESSION_PERSISTED = "session_persisted" # Optional: Published by ServiceSessionManager after successful save

    # Generic Events
    ERROR = "error"                 # Published on errors
    STATUS_UPDATE = "status_update" # Generic status update


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