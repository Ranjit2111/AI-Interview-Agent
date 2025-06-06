"""
Session Manager for coordinating agents.
"""

import logging
import json
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from backend.agents.base import BaseAgent, AgentContext
from backend.agents.interviewer import InterviewerAgent
from backend.agents.agentic_coach import AgenticCoachAgent
from backend.utils.event_bus import Event, EventBus, EventType
from backend.agents.config_models import SessionConfig
from backend.services.llm_service import LLMService
from backend.services import get_search_service
from backend.utils.common import get_current_timestamp
from backend.agents.constants import (
    ERROR_AGENT_LOAD_FAILED, ERROR_PROCESSING_REQUEST,
    COACH_FEEDBACK_ERROR, COACH_FEEDBACK_UNAVAILABLE
)


class AgentSessionManager:
    """
    Manages the flow of an interview preparation session.
    Routes messages between user and agents, maintains conversation history.
    """
    
    def __init__(self, llm_service: LLMService, event_bus: EventBus, logger: logging.Logger, 
                 session_config: SessionConfig, session_id: Optional[str] = None):
        """
        Initialize the AgentSessionManager.
        
        Args:
            llm_service: LLM service for agent interactions
            event_bus: Event bus for communication
            logger: Logger instance for debugging
            session_config: Configuration for the session
            session_id: Optional session ID (generated if not provided)
        """
        self.llm_service = llm_service
        self.event_bus = event_bus
        self.logger = logger
        self.session_config = session_config
        self.session_id = session_id or str(uuid.uuid4())
        
        # Session state tracking
        self.session_status = "active"  # Track session status: active, completed, failed
        self.final_summary_generating: bool = False  # Track if final summary is being generated
        self.needs_database_save: bool = False  # Track if session needs to be saved to database
        
        # Initialize conversation and feedback tracking
        self.conversation_history: List[Dict[str, Any]] = []
        self.per_turn_coaching_feedback_log: List[Dict[str, str]] = []
        
        # Initialize final summary storage
        self.final_summary: Optional[Dict[str, Any]] = None
        
        # Initialize agents dictionary
        self._agents: Dict[str, BaseAgent] = {}
        
        # Initialize performance tracking
        self.response_times: List[float] = []
        self.total_response_time = 0.0
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        # Publish session start event
        config_dict = self.session_config.model_dump() if hasattr(self.session_config, 'model_dump') else vars(self.session_config)
        if config_dict:
            # Manually convert enum values to strings for JSON serialization
            for key, value in config_dict.items():
                if hasattr(value, 'value'):  # This is an enum
                    config_dict[key] = value.value
                    
            self.event_bus.publish(Event(
                event_type=EventType.SESSION_START, 
                source='AgentSessionManager', 
                data={"config": config_dict, "session_id": self.session_id}
            ))
    
    def _get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Lazy load agents with required dependencies."""
        if agent_type not in self._agents:
            agent_instance = self._create_agent(agent_type)
            if agent_instance:
                self._agents[agent_type] = agent_instance
                self.event_bus.publish(Event(
                    event_type=EventType.AGENT_LOAD, 
                    source='AgentSessionManager',
                    data={"agent_type": agent_type}
                ))
                
        return self._agents.get(agent_type)
    
    def _create_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Create agent instance based on type."""
        try:
            if agent_type == "interviewer":
                self.logger.info(f"DEBUG Creating InterviewerAgent with config: job_role={self.session_config.job_role}, style={self.session_config.style}")
                return InterviewerAgent(
                    llm_service=self.llm_service, 
                    event_bus=self.event_bus,
                    logger=self.logger.getChild("InterviewerAgent"),
                    interview_style=self.session_config.style,
                    job_role=self.session_config.job_role,
                    job_description=self.session_config.job_description,
                    resume_content=self.session_config.resume_content,
                    difficulty_level=self.session_config.difficulty,
                    question_count=self.session_config.target_question_count,
                    company_name=self.session_config.company_name,
                    interview_duration_minutes=self.session_config.interview_duration_minutes,
                    use_time_based_interview=self.session_config.use_time_based_interview
                )
            elif agent_type == "coach":
                return AgenticCoachAgent(
                    llm_service=self.llm_service, 
                    search_service=get_search_service(),
                    event_bus=self.event_bus,
                    logger=self.logger.getChild("AgenticCoachAgent"),
                    resume_content=self.session_config.resume_content,
                    job_description=self.session_config.job_description
                )
            return None
        except Exception as e:
            self.logger.exception(f"Failed to initialize agent {agent_type}: {e}")
            return None
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Processes a user message and returns the agent's response.
        Per-turn coaching feedback is collected internally.
        """
        start_time = datetime.utcnow()

        # Add user message to history
        user_message_data = self._create_user_message(message, start_time)
        self.conversation_history.append(user_message_data)
        self._publish_user_message_event(user_message_data)

        try:
            # Get interviewer response
            interviewer_response = self._get_interviewer_response(start_time)
            
            # Generate coaching feedback if applicable
            self._generate_coaching_feedback(user_message_data)
            
            return interviewer_response

        except Exception as e:
            return self._handle_processing_error(e)
    
    def _create_user_message(self, message: str, timestamp: datetime) -> Dict[str, Any]:
        """Create user message data structure."""
        return {
            "role": "user",
            "content": message,
            "timestamp": timestamp.isoformat()
        }
    
    def _publish_user_message_event(self, user_message_data: Dict[str, Any]) -> None:
        """Publish user message event."""
        self.event_bus.publish(Event(
            event_type=EventType.USER_MESSAGE,
            source='AgentSessionManager',
            data={"message": user_message_data}
        ))
    
    def _get_interviewer_response(self, start_time: datetime) -> Dict[str, Any]:
        """Get response from interviewer agent."""
        interviewer_agent = self._get_agent("interviewer")
        if not interviewer_agent:
            raise Exception(ERROR_AGENT_LOAD_FAILED)
        
        agent_context = self._get_agent_context()
        interviewer_response = interviewer_agent.process(agent_context)
        
        # Create response data
        response_timestamp = datetime.utcnow()
        duration = (response_timestamp - start_time).total_seconds()
        self.api_call_count += 1

        assistant_response_data = {
            "role": "assistant",
            "agent": "interviewer",
            "content": interviewer_response.get("content", ""),
            "response_type": interviewer_response.get("response_type", "unknown"),
            "timestamp": response_timestamp.isoformat(),
            "processing_time": duration,
            "metadata": interviewer_response.get("metadata", {})
        }
        
        self.conversation_history.append(assistant_response_data)
        self._publish_assistant_response_event(assistant_response_data)
        
        return assistant_response_data
    
    def _publish_assistant_response_event(self, response_data: Dict[str, Any]) -> None:
        """Publish assistant response event."""
        self.event_bus.publish(Event(
            event_type=EventType.ASSISTANT_RESPONSE, 
            source='AgentSessionManager',
            data={"response": response_data}
        ))
    def _generate_coaching_feedback(self, user_message_data: Dict[str, Any]) -> None:
        """
        Collects live feedback from the agentic coach agent if available.
        Operates within the session to log feedback for retrieval.
        """
        try:
            question = self._find_last_interviewer_question()
            answer = user_message_data.get("content", "")

            if question and answer:
                coach_agent = self._get_agent("coach")
                if coach_agent:
                    feedback = self._get_coach_feedback(coach_agent, question, answer)
                    self._log_coach_feedback(question, answer, feedback)
                else:
                    self._log_coach_feedback_unavailable(question, answer)
        except Exception as e:
            self.logger.exception(f"Error generating coaching feedback: {e}")

    def _find_last_interviewer_question(self) -> Optional[str]:
        """Find the most recent question from the interviewer."""
        for message in reversed(self.conversation_history):
            if (message.get("role") == "assistant" and
                    message.get("agent") == "interviewer"):
                return message.get("content", "")
        return None

    def _get_coach_feedback(self, coach_agent: AgenticCoachAgent, question: str, answer: str) -> str:
        """Get feedback from coach agent for a specific Q&A pair."""
        try:
            filtered_history = self._create_filtered_history_for_coach()
            
            # Use the existing evaluate_answer method with the correct parameters
            feedback_response = coach_agent.evaluate_answer(
                question=question,
                answer=answer,
                justification=None,  # We don't have justification in this context
                conversation_history=filtered_history
            )
            
            # evaluate_answer returns a string directly, not a dict
            return feedback_response if feedback_response else COACH_FEEDBACK_UNAVAILABLE
        except Exception as e:
            self.logger.exception(f"Error getting coach feedback: {e}")
            return COACH_FEEDBACK_ERROR

    def _create_filtered_history_for_coach(self) -> List[Dict[str, Any]]:
        """Create a filtered conversation history for coach agent context."""
        filtered_history = []
        for message in self.conversation_history:
            if message.get("role") in ["user", "assistant"]:
                filtered_message = {
                    "role": message["role"],
                    "content": message.get("content", ""),
                    "timestamp": message.get("timestamp", "")
                }
                if message.get("role") == "assistant":
                    filtered_message["agent"] = message.get("agent", "unknown")
                    filtered_history.append(filtered_message)
        return filtered_history
    
    def _log_coach_feedback(self, question: str, answer: str, feedback: str) -> None:
        """Log coaching feedback for later retrieval."""
        self.per_turn_coaching_feedback_log.append({
            "question": question[:200],
            "answer": answer[:200], 
            "feedback": feedback
        })
    
    def _log_coach_feedback_unavailable(self, question: str, answer: str) -> None:
        """Log when coaching feedback is unavailable."""
        self._log_coach_feedback(question, answer, COACH_FEEDBACK_UNAVAILABLE)
    
    def _handle_processing_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors in message processing."""
        error_message = f"{ERROR_PROCESSING_REQUEST}: {str(error)}"
        self.logger.exception(error_message)
        
        self.event_bus.publish(Event(
            event_type=EventType.ERROR,
            source='AgentSessionManager',
            data={"error": error_message, "session_id": self.session_id}
        ))
        
        return {
            "role": "system",
            "content": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "error": True
        }

    def _get_agent_context(self) -> AgentContext:
        """Create agent context for processing."""
        return AgentContext(
            session_id=self.session_id,
            conversation_history=self.conversation_history,
            session_config=self.session_config,
            event_bus=self.event_bus,
            logger=self.logger
        )

    def end_interview(self) -> Dict[str, Any]:
        """
        Ends the interview session and returns consolidated results.
        Starts background generation of final summary while returning per-turn feedback immediately.
        NOTE: Final summary is NEVER included in this response to ensure frontend polling and loading states.
        """
        self.event_bus.publish(Event(
            event_type=EventType.SESSION_END,
            source='AgentSessionManager',
            data={}
        ))

        # Return per-turn feedback immediately, but NEVER include final summary
        final_results = {
            "status": "Interview Ended",
            "coaching_summary": None,  # Always None - frontend must poll for final summary
            "per_turn_feedback": self.per_turn_coaching_feedback_log
        }

        # Start background generation of final summary
        if not self.final_summary_generating:
            self.final_summary_generating = True
            # Start async background task for final summary generation
            asyncio.create_task(self._generate_final_summary_background())
            self.logger.info(f"Started background final summary generation for session {self.session_id}")

        # REMOVED: Never include final summary even if already available
        # This ensures frontend always sees loading states and polls for completion

        return final_results

    async def _generate_final_summary_background(self) -> None:
        """Generate final coaching summary in background async task."""
        start_time = datetime.utcnow()
        try:
            self.logger.info(f"🚀 Background final summary generation STARTED for session {self.session_id} at {start_time.isoformat()}")
            
            coaching_summary = self._generate_final_coaching_summary()
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            if coaching_summary:
                self.final_summary = coaching_summary
                self.session_status = "completed"
                
                self.logger.info(f"✅ Background final summary COMPLETED for session {self.session_id}: {len(str(coaching_summary))} chars in {generation_time:.2f}s")
                self.logger.info(f"DEBUG Background Task - Final summary result preview:")
                self.logger.info(f"  - Keys: {list(coaching_summary.keys()) if isinstance(coaching_summary, dict) else 'Not a dict'}")
                self.logger.info(f"  - Has recommended_resources: {bool(coaching_summary.get('recommended_resources')) if isinstance(coaching_summary, dict) else False}")
                self.logger.info(f"  - Resources count: {len(coaching_summary.get('recommended_resources', [])) if isinstance(coaching_summary, dict) else 0}")
                self.logger.info(f"  - Session status set to: {self.session_status}")
                self.logger.info(f"  - Generation time: {generation_time:.2f} seconds")
            else:
                error_msg = "Final coaching summary generation returned None"
                self.final_summary = {"error": error_msg}
                self.session_status = "completed"  # Still mark as completed but with error
                self.logger.error(f"❌ Background final summary FAILED for session {self.session_id} after {generation_time:.2f}s: {error_msg}")
                
        except Exception as e:
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Final coaching summary generation failed: {e}"
            self.final_summary = {"error": error_msg}
            self.session_status = "completed"  # Still mark as completed but with error
            self.logger.exception(f"💥 Background final summary ERROR for session {self.session_id} after {generation_time:.2f}s: {e}")
        
        finally:
            final_time = (datetime.utcnow() - start_time).total_seconds()
            self.final_summary_generating = False
            
            self.logger.info(f"🏁 Background Task FINALIZED for session {self.session_id} after {final_time:.2f}s:")
            self.logger.info(f"  - Session ID: {self.session_id}")
            self.logger.info(f"  - Session status: {self.session_status}")
            self.logger.info(f"  - Final summary generating: {self.final_summary_generating}")
            self.logger.info(f"  - Has final summary: {bool(self.final_summary)}")
            self.logger.info(f"  - Total processing time: {final_time:.2f} seconds")
            
            # CRITICAL FIX: Save session state to database after final summary completion
            # This ensures that subsequent API calls will have access to the final summary
            try:
                # Import session registry to trigger a save
                # Note: We need to access the session registry from the app state
                # Since we don't have direct access here, we'll add a method to handle this
                self.logger.info(f"🔄 Attempting to save session state after final summary completion...")
                # This will be handled by a callback mechanism or direct save call
                self.needs_database_save = True  # Flag for external save trigger
            except Exception as save_error:
                self.logger.error(f"Failed to trigger session save after final summary: {save_error}")

    def _generate_final_coaching_summary(self) -> Optional[Dict[str, Any]]:
        """Generate final coaching summary using agentic coach agent."""
        coach_agent = self._get_agent("coach")
        if not coach_agent:
            return None
            
        # Use the new agentic method that includes resource search
        return coach_agent.generate_final_summary_with_resources(self.conversation_history)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Returns the full conversation history."""
        return self.conversation_history

    def get_session_stats(self) -> Dict[str, Any]:
        """Returns performance and usage statistics for the session."""
        avg_response_time = (self.total_response_time / len(self.response_times)) if self.response_times else 0
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": sum(1 for msg in self.conversation_history if msg.get("role") == "user"),
            "assistant_messages": sum(1 for msg in self.conversation_history if msg.get("role") == "assistant"),
            "system_messages": sum(1 for msg in self.conversation_history if msg.get("role") == "system"),
            "total_response_time_seconds": round(self.total_response_time, 2),
            "average_response_time_seconds": round(avg_response_time, 2),
            "total_api_calls": self.api_call_count,
            "total_tokens_used": self.total_tokens_used,
        }

    def reset_session(self):
        """Resets the session state, including history and agent instances."""
        self.conversation_history = []
        self.per_turn_coaching_feedback_log = []
        self.final_summary = None  # CRITICAL FIX: Clear final summary on reset
        self.final_summary_generating = False  # Reset background generation flag
        self.needs_database_save = False  # Reset save flag
        self._agents = {}
        
        self.response_times = []
        self.total_response_time = 0.0
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        # Reset session status back to active
        self.session_status = "active"
        
        self.event_bus.publish(Event(event_type=EventType.SESSION_RESET, source='AgentSessionManager', data={}))

    @classmethod
    def from_session_data(cls, session_data: Dict, llm_service: LLMService, 
                         event_bus: EventBus, logger: logging.Logger) -> 'AgentSessionManager':
        """
        Create manager from database session data.
        
        Args:
            session_data: Session data from database
            llm_service: LLM service instance
            event_bus: Event bus instance
            logger: Logger instance
            
        Returns:
            AgentSessionManager: Initialized manager with restored state
        """
        # Create SessionConfig from stored data
        config_data = session_data.get("session_config", {})
        session_config = SessionConfig(**config_data) if config_data else SessionConfig()
        
        # Create manager instance
        manager = cls(
            llm_service=llm_service,
            event_bus=event_bus,
            logger=logger,
            session_config=session_config,
            session_id=session_data["session_id"]
        )
        
        # Restore state from database
        manager.conversation_history = session_data.get("conversation_history", [])
        manager.per_turn_coaching_feedback_log = session_data.get("per_turn_feedback_log", [])
        manager.final_summary = session_data.get("final_summary")  # CRITICAL FIX: Restore final summary from database
        manager.final_summary_generating = session_data.get("final_summary_generating", False)  # Restore generation flag
        manager.needs_database_save = session_data.get("needs_database_save", False)  # Restore save flag
        manager.total_response_time = session_data.get("session_stats", {}).get("total_response_time_seconds", 0.0)
        manager.total_tokens_used = session_data.get("session_stats", {}).get("total_tokens_used", 0)
        manager.api_call_count = session_data.get("session_stats", {}).get("total_api_calls", 0)
        
        # Restore session status from database
        manager.session_status = session_data.get("status", "active")
        
        logger.info(f"Restored session manager from database: {manager.session_id}")
        return manager

    def to_dict(self) -> Dict:
        """
        Serialize manager state for database storage.
        
        Returns:
            Dict: Serialized session state
        """
        # Serialize session config and manually convert enums to strings
        session_config_dict = self.session_config.model_dump() if hasattr(self.session_config, 'model_dump') else vars(self.session_config)
        
        # Manually convert enum values to strings for JSON serialization
        for key, value in session_config_dict.items():
            if hasattr(value, 'value'):  # This is an enum
                session_config_dict[key] = value.value
        
        return {
            "session_id": self.session_id,
            "session_config": session_config_dict,
            "conversation_history": self.conversation_history,
            "per_turn_feedback_log": self.per_turn_coaching_feedback_log,
            "final_summary": self.final_summary,
            "final_summary_generating": self.final_summary_generating,
            "needs_database_save": self.needs_database_save,
            "session_stats": self.get_session_stats(),
            "status": self.session_status
        }

    def get_langchain_config(self) -> Dict:
        """
        Get LangChain configuration with thread_id for session isolation.
        
        Returns:
            Dict: Configuration for LangChain calls
        """
        return {"configurable": {"thread_id": self.session_id}}

