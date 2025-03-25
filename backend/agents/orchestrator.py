"""
Agent orchestrator for coordinating multiple agents in the AI interview system.
This module manages communication between agents and determines which agent should respond to user input.
"""

import logging
import traceback
import time
import uuid
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Type
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from enum import Enum

from backend.agents.base import BaseAgent, AgentContext
from backend.agents.interviewer import InterviewerAgent
from backend.agents.coach import CoachAgent
from backend.agents.skill_assessor import SkillAssessorAgent
from backend.agents.feedback_agent import FeedbackAgent
from backend.utils.event_bus import Event, EventBus, EventType
from backend.models.interview import InterviewStyle, SessionMode, InterviewSession, SkillAssessment, Resource

import backoff
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

# Default system message for the orchestrator
ORCHESTRATOR_SYSTEM_MESSAGE = """
You are an orchestrator managing an interview preparation session. Your goal is to help the user prepare for job interviews
by coordinating specialized agents to provide tailored assistance.
"""

class OrchestratorMode(str, Enum):
    """Orchestrator operating modes."""
    INTERVIEW = "interview"  # Standard interview mode with questions
    SKILL_ASSESSMENT = "skill_assessment"  # Focused skill assessment
    FEEDBACK = "feedback"  # Providing feedback on user answers

# Cache expiration time in seconds
RESPONSE_CACHE_TTL = 120  # 2 minutes

class AgentOrchestrator:
    """
    Orchestrator that coordinates multiple agents in the interview system.
    
    The orchestrator is responsible for:
    - Managing the lifecycle of multiple agents
    - Routing user input to appropriate agents
    - Aggregating responses from multiple agents
    - Maintaining session state and mode
    - Handling skill assessment events
    """
    
    def __init__(
        self,
        session_id: str,
        job_role: Optional[str] = None,
        job_description: Optional[str] = None,
        interview_style: Optional[str] = None,
        mode: OrchestratorMode = OrchestratorMode.INTERVIEW,
        system_message: Optional[str] = None,
        event_bus: Optional[EventBus] = None,
        db_session: Optional[Session] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            session_id: Unique identifier for the interview session
            job_role: The role the user is interviewing for
            job_description: Description of the job
            interview_style: Style of interview (e.g., behavioral, technical)
            mode: Operating mode for the orchestrator
            system_message: Custom system message for the orchestrator
            event_bus: Event bus for publishing events
            db_session: Database session for persistence
            logger: Logger for recording orchestrator activity
        """
        self.session_id = session_id
        self.job_role = job_role or "Software Engineer"
        self.job_description = job_description or "A general software engineering role requiring coding skills and problem-solving abilities."
        self.interview_style = interview_style or "technical"
        self.mode = mode
        self.system_message = system_message or ORCHESTRATOR_SYSTEM_MESSAGE
        self.event_bus = event_bus or EventBus()
        self.db_session = db_session
        self.logger = logger or logging.getLogger(__name__)
        
        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.last_response_time = 0
        self.avg_response_time = 0
        self.response_time_samples = 0
        
        # LLM API call stats
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        # Caching for better performance
        self._last_processed_msg_index = -1
        self._agent_cache = {}
        self._response_cache = {}
        self._response_cache_timestamps = {}
        self._message_hash_cache = {}
        
        # History window settings
        self._history_window_size = 20  # Maximum number of messages to include
        self._summarized_history = None  # Summary of older messages
        self._summarization_threshold = 10  # When to summarize older messages
        
        # Initialize agents (lazy loading - will be created when needed)
        self._interviewer_agent: Optional[InterviewerAgent] = None
        self._feedback_agent: Optional[FeedbackAgent] = None
        self._skill_assessor_agent: Optional[SkillAssessorAgent] = None
        
        # In case we need quick access to the current agent being used
        self.current_agent_type = None
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Log orchestrator initialization
        self.logger.info(
            f"Initialized orchestrator for session {session_id} - "
            f"Job: {job_role}, Style: {interview_style}, Mode: {mode}"
        )
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for the orchestrator."""
        self.event_bus.subscribe("interview_start", self._handle_interview_start)
        self.event_bus.subscribe("interview_end", self._handle_interview_end)
        self.event_bus.subscribe("mode_change", self._handle_mode_change)
    
    @property
    def interviewer_agent(self) -> InterviewerAgent:
        """Get or create the interviewer agent."""
        if not self._interviewer_agent:
            # Lazy initialization of the interviewer agent
            self._interviewer_agent = InterviewerAgent(
                session_id=self.session_id,
                job_role=self.job_role,
                job_description=self.job_description,
                interview_style=self.interview_style,
                event_bus=self.event_bus,
                logger=self.logger
            )
        return self._interviewer_agent
    
    @property
    def feedback_agent(self) -> FeedbackAgent:
        """Get or create the feedback agent."""
        if not self._feedback_agent:
            # Lazy initialization of the feedback agent
            self._feedback_agent = FeedbackAgent(
                session_id=self.session_id,
                job_role=self.job_role,
                job_description=self.job_description,
                event_bus=self.event_bus,
                logger=self.logger
            )
        return self._feedback_agent
    
    @property
    def skill_assessor_agent(self) -> SkillAssessorAgent:
        """Get or create the skill assessor agent."""
        if not self._skill_assessor_agent:
            # Lazy initialization of the skill assessor agent
            self._skill_assessor_agent = SkillAssessorAgent(
                session_id=self.session_id, 
                job_role=self.job_role,
                job_description=self.job_description,
                event_bus=self.event_bus,
                logger=self.logger
            )
        return self._skill_assessor_agent
    
    def _get_relevant_history(self) -> List[Dict[str, Any]]:
        """
        Get relevant conversation history, with potential summarization 
        of older messages if the history is long.
        
        Returns:
            Optimized conversation history for agent processing
        """
        history_length = len(self.conversation_history)
        
        # If history is short, just return it all
        if history_length <= self._history_window_size:
            return self.conversation_history
        
        # If history is long, only include most recent messages
        if self._summarized_history is None and history_length > self._summarization_threshold:
            # Create a summary if needed
            older_history = self.conversation_history[:history_length - self._history_window_size]
            
            # Count older messages by role
            user_msgs = sum(1 for msg in older_history if msg.get("role") == "user")
            assistant_msgs = sum(1 for msg in older_history if msg.get("role") == "assistant")
            
            # Create a simple summary message
            self._summarized_history = {
                "role": "system",
                "content": f"[History summary: {len(older_history)} earlier messages ({user_msgs} from user, {assistant_msgs} from assistant) discussing {self.job_role} interview preparation]",
                "is_summary": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Return summary + recent messages
        if self._summarized_history:
            recent_history = self.conversation_history[history_length - self._history_window_size:]
            return [self._summarized_history] + recent_history
        
        return self.conversation_history
    
    def _get_message_hash(self, message: str) -> str:
        """
        Generate a hash for a message for caching purposes.
        
        Args:
            message: The message to hash
            
        Returns:
            Hash string of the message
        """
        # Check cache first
        if message in self._message_hash_cache:
            return self._message_hash_cache[message]
        
        # Generate a hash of the message
        hash_obj = hashlib.md5(message.encode())
        hash_str = hash_obj.hexdigest()
        
        # Cache and return
        self._message_hash_cache[message] = hash_str
        return hash_str
    
    def _get_conversation_hash(self) -> str:
        """
        Generate a hash representing the current conversation state.
        
        Returns:
            Hash string representing the conversation state
        """
        # Create a string from the last 5 messages or all if less
        recent_msgs = self.conversation_history[-5:] if len(self.conversation_history) >= 5 else self.conversation_history
        conv_str = json.dumps([{
            "role": msg.get("role", ""),
            "content": msg.get("content", "")[:100],  # Only hash first 100 chars
            "agent": msg.get("agent", "")
        } for msg in recent_msgs])
        
        # Create a hash from the string
        hash_obj = hashlib.md5(conv_str.encode())
        return hash_obj.hexdigest()
    
    def start_interview(self) -> Dict[str, Any]:
        """
        Start a new interview session.
        
        Returns:
            Initial agent response to start the interview
        """
        start_time = time.time()
        
        # Publish event for session start
        self.event_bus.publish(Event(
            event_type="interview_start",
            data={
                "session_id": self.session_id,
                "job_role": self.job_role,
                "interview_style": self.interview_style,
                "mode": self.mode
            }
        ))
        
        # Get a response based on the current mode
        if self.mode == OrchestratorMode.INTERVIEW:
            agent_response = self.interviewer_agent.start_interview()
            self.current_agent_type = "interviewer"
        elif self.mode == OrchestratorMode.SKILL_ASSESSMENT:
            agent_response = self.skill_assessor_agent.start_assessment()
            self.current_agent_type = "skill_assessor"
        elif self.mode == OrchestratorMode.FEEDBACK:
            agent_response = self.feedback_agent.start_feedback()
            self.current_agent_type = "feedback"
        else:
            raise ValueError(f"Unknown orchestrator mode: {self.mode}")
        
        # Add response to history
        response_data = {
            "role": "assistant",
            "content": agent_response["message"],
            "agent": agent_response.get("agent_type", self.current_agent_type),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"mode": self.mode.value}
        }
        self.conversation_history.append(response_data)
        
        # Track token usage
        if "tokens_used" in agent_response:
            self.total_tokens_used += agent_response["tokens_used"]
            self.api_call_count += 1
        
        # Track response time
        elapsed = time.time() - start_time
        self._update_response_time_stats(elapsed)
        
        # Log success
        self.logger.info(
            f"Started interview session {self.session_id} in {self.mode} mode, "
            f"response generated in {elapsed:.2f}s"
        )
        
        return response_data
    
    def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and get an agent response.
        
        Args:
            message: User's message
            user_id: Optional user identifier
            
        Returns:
            Agent response
        """
        start_time = time.time()
        
        # Add user message to history
        user_message = {
            "role": "user",
            "content": message,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"mode": self.mode.value}
        }
        self.conversation_history.append(user_message)
        
        # Clear cached summary since history changed
        self._summarized_history = None
        
        # Check if we have a cached response for similar message + conversation state
        msg_hash = self._get_message_hash(message)
        conv_hash = self._get_conversation_hash()
        cache_key = f"{msg_hash}_{conv_hash}_{self.mode.value}"
        
        now = datetime.utcnow()
        if (cache_key in self._response_cache and
            cache_key in self._response_cache_timestamps and
            (now - self._response_cache_timestamps[cache_key]).total_seconds() < RESPONSE_CACHE_TTL):
            
            # Use cached response but generate a new timestamp
            cached_response = self._response_cache[cache_key].copy()
            cached_response["timestamp"] = datetime.utcnow().isoformat()
            self.conversation_history.append(cached_response)
            
            self.logger.info(f"Used cached response for message in session {self.session_id}")
            return cached_response
        
        # Publish event for user message
        self.event_bus.publish(Event(
            event_type="user_response",
            data={
                "session_id": self.session_id,
                "message": message,
                "user_id": user_id,
                "mode": self.mode
            }
        ))
        
        # Get response based on current mode with optimized history
        relevant_history = self._get_relevant_history()
        
        try:
            if self.mode == OrchestratorMode.INTERVIEW:
                agent_response = self._process_interview_message(message, relevant_history)
                self.current_agent_type = "interviewer"
            elif self.mode == OrchestratorMode.SKILL_ASSESSMENT:
                agent_response = self._process_skill_assessment_message(message, relevant_history)
                self.current_agent_type = "skill_assessor"
            elif self.mode == OrchestratorMode.FEEDBACK:
                agent_response = self._process_feedback_message(message, relevant_history)
                self.current_agent_type = "feedback"
            else:
                raise ValueError(f"Unknown orchestrator mode: {self.mode}")
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Return error response
            agent_response = {
                "message": "I apologize, but I encountered an error processing your message. Please try again.",
                "agent_type": self.current_agent_type or "system"
            }
        
        # Add response to history
        response_data = {
            "role": "assistant",
            "content": agent_response["message"],
            "agent": agent_response.get("agent_type", self.current_agent_type),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"mode": self.mode.value}
        }
        self.conversation_history.append(response_data)
        
        # Cache the response
        self._response_cache[cache_key] = response_data
        self._response_cache_timestamps[cache_key] = now
        
        # Track token usage
        if "tokens_used" in agent_response:
            self.total_tokens_used += agent_response["tokens_used"]
            self.api_call_count += 1
        
        # Track response time
        elapsed = time.time() - start_time
        self._update_response_time_stats(elapsed)
        
        # Publish event for agent response
        self.event_bus.publish(Event(
            event_type="agent_response",
            data={
                "session_id": self.session_id,
                "message": agent_response["message"],
                "agent_type": agent_response.get("agent_type", self.current_agent_type),
                "mode": self.mode
            }
        ))
        
        # Log success
        self.logger.info(
            f"Processed message in session {self.session_id}, mode: {self.mode}, "
            f"response generated in {elapsed:.2f}s, tokens: {agent_response.get('tokens_used', 'unknown')}"
        )
        
        return response_data
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _process_interview_message(self, message: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Process a message in interview mode.
        
        Args:
            message: User message
            history: Optional conversation history, uses full history if None
            
        Returns:
            Agent response dictionary
        """
        return self.interviewer_agent.generate_response(
            message, history or self.conversation_history
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _process_feedback_message(self, message: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Process a message in feedback mode.
        
        Args:
            message: User message
            history: Optional conversation history, uses full history if None
            
        Returns:
            Agent response dictionary
        """
        return self.feedback_agent.generate_response(
            message, history or self.conversation_history
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _process_skill_assessment_message(self, message: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Process a message in skill assessment mode.
        
        Args:
            message: User message
            history: Optional conversation history, uses full history if None
            
        Returns:
            Agent response dictionary
        """
        return self.skill_assessor_agent.generate_response(
            message, history or self.conversation_history
        )
    
    def switch_mode(self, new_mode: OrchestratorMode) -> Dict[str, Any]:
        """
        Switch to a different orchestration mode.
        
        Args:
            new_mode: New mode to switch to
            
        Returns:
            Agent response after switching modes
        """
        start_time = time.time()
        
        # Don't do anything if already in this mode
        if self.mode == new_mode:
            return {
                "role": "assistant",
                "content": f"Already in {new_mode} mode.",
                "agent": "system",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"mode": self.mode.value}
            }
        
        # Update mode
        old_mode = self.mode
        self.mode = new_mode
        
        # Clear caches when switching modes
        self._clear_response_cache()
        self._summarized_history = None
        
        # Publish mode change event
        self.event_bus.publish(Event(
            event_type="mode_change",
            data={
                "session_id": self.session_id,
                "old_mode": old_mode,
                "new_mode": new_mode
            }
        ))
        
        # Get response for the new mode
        if new_mode == OrchestratorMode.INTERVIEW:
            agent_response = self.interviewer_agent.handle_mode_switch(old_mode)
            self.current_agent_type = "interviewer"
        elif new_mode == OrchestratorMode.SKILL_ASSESSMENT:
            agent_response = self.skill_assessor_agent.handle_mode_switch(old_mode)
            self.current_agent_type = "skill_assessor"
        elif new_mode == OrchestratorMode.FEEDBACK:
            agent_response = self.feedback_agent.handle_mode_switch(old_mode)
            self.current_agent_type = "feedback"
        else:
            raise ValueError(f"Unknown orchestrator mode: {new_mode}")
        
        # Add response to history
        response_data = {
            "role": "assistant",
            "content": agent_response["message"],
            "agent": agent_response.get("agent_type", self.current_agent_type),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"mode": self.mode.value}
        }
        self.conversation_history.append(response_data)
        
        # Track token usage
        if "tokens_used" in agent_response:
            self.total_tokens_used += agent_response["tokens_used"]
            self.api_call_count += 1
        
        # Track response time
        elapsed = time.time() - start_time
        self._update_response_time_stats(elapsed)
        
        # Log mode switch
        self.logger.info(
            f"Switched mode in session {self.session_id} from {old_mode} to {new_mode}, "
            f"response generated in {elapsed:.2f}s"
        )
        
        return response_data
    
    def end_interview(self) -> Dict[str, Any]:
        """
        End the interview session.
        
        Returns:
            Final summary message
        """
        start_time = time.time()
        
        # Generate summary based on current mode
        if self.mode == OrchestratorMode.INTERVIEW:
            agent_response = self.interviewer_agent.end_interview(self.conversation_history)
            self.current_agent_type = "interviewer"
        elif self.mode == OrchestratorMode.SKILL_ASSESSMENT:
            agent_response = self.skill_assessor_agent.end_assessment(self.conversation_history)
            self.current_agent_type = "skill_assessor"
        elif self.mode == OrchestratorMode.FEEDBACK:
            agent_response = self.feedback_agent.end_feedback(self.conversation_history)
            self.current_agent_type = "feedback"
        else:
            raise ValueError(f"Unknown orchestrator mode: {self.mode}")
        
        # Add summary to history
        response_data = {
            "role": "assistant",
            "content": agent_response["message"],
            "agent": agent_response.get("agent_type", self.current_agent_type),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"mode": self.mode.value, "is_summary": True}
        }
        self.conversation_history.append(response_data)
        
        # Track token usage
        if "tokens_used" in agent_response:
            self.total_tokens_used += agent_response["tokens_used"]
            self.api_call_count += 1
        
        # Publish event for session end
        self.event_bus.publish(Event(
            event_type="interview_end",
            data={
                "session_id": self.session_id,
                "summary": agent_response["message"],
                "total_messages": len(self.conversation_history),
                "total_tokens": self.total_tokens_used,
                "total_api_calls": self.api_call_count,
                "avg_response_time": self.avg_response_time
            }
        ))
        
        # Track response time
        elapsed = time.time() - start_time
        self._update_response_time_stats(elapsed)
        
        # Clear all caches after session ends
        self._clear_response_cache()
        self._agent_cache = {}
        self._message_hash_cache = {}
        
        # Log session end
        self.logger.info(
            f"Ended interview session {self.session_id} in {self.mode} mode, "
            f"summary generated in {elapsed:.2f}s, "
            f"total messages: {len(self.conversation_history)}, "
            f"total tokens: {self.total_tokens_used}"
        )
        
        return response_data
    
    def get_agent_instance(self, agent_type: str) -> Optional[BaseAgent]:
        """
        Get an agent instance by type, using cache if available.
        
        Args:
            agent_type: Type of agent to retrieve
            
        Returns:
            Agent instance or None if type is unknown
        """
        # Check cache first
        if agent_type in self._agent_cache:
            return self._agent_cache[agent_type]
        
        # Get appropriate agent
        agent = None
        if agent_type == "interviewer":
            agent = self.interviewer_agent
        elif agent_type == "feedback":
            agent = self.feedback_agent
        elif agent_type == "skill_assessor":
            agent = self.skill_assessor_agent
        
        # Cache the agent if found
        if agent:
            self._agent_cache[agent_type] = agent
        
        return agent
    
    def _clear_response_cache(self) -> None:
        """Clear the response cache."""
        self._response_cache = {}
        self._response_cache_timestamps = {}
    
    def _update_response_time_stats(self, elapsed_time: float) -> None:
        """
        Update response time statistics.
        
        Args:
            elapsed_time: Time taken for the last response
        """
        self.last_response_time = elapsed_time
        self.response_time_samples += 1
        
        # Update running average
        self.avg_response_time = (
            (self.avg_response_time * (self.response_time_samples - 1) + elapsed_time) 
            / self.response_time_samples
        )
    
    def _handle_interview_start(self, event: Event) -> None:
        """
        Handle interview start events.
        
        Args:
            event: The interview start event
        """
        self.logger.debug(f"Orchestrator received interview_start event for session {event.data.get('session_id')}")
    
    def _handle_interview_end(self, event: Event) -> None:
        """
        Handle interview end events.
        
        Args:
            event: The interview end event
        """
        self.logger.debug(f"Orchestrator received interview_end event for session {event.data.get('session_id')}")
    
    def _handle_mode_change(self, event: Event) -> None:
        """
        Handle mode change events.
        
        Args:
            event: The mode change event
        """
        session_id = event.data.get('session_id')
        old_mode = event.data.get('old_mode')
        new_mode = event.data.get('new_mode')
        self.logger.debug(f"Orchestrator handled mode change for session {session_id} from {old_mode} to {new_mode}")
    
    def reset(self) -> None:
        """Reset the orchestrator state."""
        # Clear conversation history but keep configuration
        self.conversation_history = []
        self._last_processed_msg_index = -1
        self._agent_cache = {}
        self._response_cache = {}
        self._response_cache_timestamps = {}
        self._message_hash_cache = {}
        self._summarized_history = None
        
        # Reset performance tracking
        self.last_response_time = 0
        self.avg_response_time = 0
        self.response_time_samples = 0
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        # Reset or reinitialize agents if needed
        if self._interviewer_agent:
            self._interviewer_agent.reset()
        
        if self._feedback_agent:
            self._feedback_agent.reset()
        
        if self._skill_assessor_agent:
            self._skill_assessor_agent.reset()
        
        self.logger.info(f"Reset orchestrator state for session {self.session_id}")
    
    def get_agent_for_message(self, user_message: str) -> Tuple[str, BaseAgent]:
        """
        Determine which agent should handle a user message.
        This is a simplified implementation that always returns the current agent.
        A more advanced implementation could analyze the message content
        to dynamically select the most appropriate agent.
        
        Args:
            user_message: User's message
            
        Returns:
            Tuple of (agent_type, agent_instance)
        """
        # For now, just use the agent for the current mode
        if self.mode == OrchestratorMode.INTERVIEW:
            return "interviewer", self.interviewer_agent
        elif self.mode == OrchestratorMode.SKILL_ASSESSMENT:
            return "skill_assessor", self.skill_assessor_agent
        elif self.mode == OrchestratorMode.FEEDBACK:
            return "feedback", self.feedback_agent
        else:
            # Default to interviewer if mode is unknown
            return "interviewer", self.interviewer_agent 