"""
Session Manager (formerly Agent Orchestrator) for coordinating agents.
Manages session state, history, and agent interactions.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Type
from datetime import datetime
from enum import Enum

from backend.agents.base import BaseAgent, AgentContext
from backend.agents.interviewer import InterviewerAgent
from backend.agents.coach import CoachAgent
from backend.agents.skill_assessor import SkillAssessorAgent
from backend.utils.event_bus import Event, EventBus, EventType
from backend.models.interview import InterviewStyle, InterviewSession
from backend.config import get_logger
from backend.services.llm_service import LLMService

# Default system message (might not be used directly)
SESSION_MANAGER_SYSTEM_MESSAGE = """
System managing an interview preparation session.
"""

class SessionManager:
    """
    Manages the flow of an interview preparation session.
    It routes messages between the user and various agents (Interviewer, Coach, etc.),
    maintains the conversation history, and handles session state.
    """
    
    def __init__(self, session_id: str, user_id: str, session_config: InterviewSession):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_config = session_config
        self.conversation_history: List[Dict[str, Any]] = []
        # Extract relevant config details for easy access if needed
        self.job_role = session_config.job_role
        self.interview_style = session_config.interview_style
        
        self.logger = get_logger(f"SessionManager_{self.session_id}")
        self.event_bus = EventBus() # One event bus per session
        self._llm_service = LLMService() # Centralized LLM service instance per session
        
        # Performance tracking
        self.response_times: List[float] = []
        self.total_response_time = 0.0
        self.total_tokens_used = 0 # TODO: Update when LLM service provides token counts
        self.api_call_count = 0
        
        # Initialize agents (lazy loading dictionary)
        self._agents: Dict[str, BaseAgent] = {}

        self.logger.info(f"Session Manager initialized for session {self.session_id}")
        # Publish SESSION_START event with config for agents to pick up
        self.event_bus.publish(Event(EventType.SESSION_START, {"session_id": self.session_id, "config": session_config.dict()}))
    
    def _get_agent(self, agent_type: str) -> Optional[BaseAgent]: # Return Optional
        """Lazy load agents, passing required dependencies."""
        if agent_type not in self._agents:
            start_time = datetime.utcnow()
            agent_instance: Optional[BaseAgent] = None
            try:
                if agent_type == "interviewer":
                    # Pass dependencies: llm_service, event_bus, logger
                    agent_instance = InterviewerAgent(
                        llm_service=self._llm_service, 
                        event_bus=self.event_bus,
                        logger=self.logger.getChild("InterviewerAgent")
                        # Config like job_role, style is passed via SESSION_START event
                    )
                elif agent_type == "coach":
                    agent_instance = CoachAgent(
                        llm_service=self._llm_service, 
                        event_bus=self.event_bus,
                        logger=self.logger.getChild("CoachAgent")
                    )
                elif agent_type == "skill_assessor":
                    agent_instance = SkillAssessorAgent(
                        llm_service=self._llm_service, 
                        event_bus=self.event_bus,
                        logger=self.logger.getChild("SkillAssessorAgent")
                    )
                else:
                    self.logger.error(f"Attempted to load unknown agent type: {agent_type}")
                    return None # Return None for unknown types
                    
                if agent_instance:
                    self._agents[agent_type] = agent_instance
                    end_time = datetime.utcnow()
                    load_time = (end_time - start_time).total_seconds()
                    self.logger.info(f"Loaded {agent_type} agent in {load_time:.2f} seconds.")
                    self.event_bus.publish(Event(EventType.AGENT_LOAD, {"agent_type": agent_type, "load_time": load_time})) # Use helper
                
            except Exception as e:
                self.logger.exception(f"Failed to initialize agent {agent_type}: {e}")
                return None # Return None if initialization fails
                
        return self._agents.get(agent_type)
    
    def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes a user message, routes it primarily to the InterviewerAgent,
        and returns the agent's response. Other agents listen via events.
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Processing message: '{message[:50]}...'")

        # Construct user message entry
        user_message_data = {
            "role": "user",
            "content": message,
            "timestamp": start_time.isoformat()
        }
        if user_id:
            user_message_data["user_id"] = user_id
        self.conversation_history.append(user_message_data)

        # Publish event for user message (other agents like Coach, SkillAssessor listen)
        self.event_bus.publish(Event(
            EventType.USER_MESSAGE,
            {
                "session_id": self.session_id,
                "message": user_message_data
            }
        ))

        # --- Route to Interviewer Agent --- 
        try:
            interviewer_agent = self._get_agent("interviewer")
            if not interviewer_agent:
                raise Exception("Interviewer agent could not be loaded.")
            
            agent_context = self._get_agent_context() # Prepare context for this call

            # Invoke the interviewer agent's process method
            # Expected return: { "content": str, "response_type": str, "metadata": dict }
            agent_response = interviewer_agent.process(agent_context)
            response_content = agent_response.get("content", "")
            response_type = agent_response.get("response_type", "unknown") # e.g., question, closing, error
            metadata = agent_response.get("metadata", {})
            # TODO: Handle token usage if returned in metadata
            # self.total_tokens_used += metadata.get("tokens_used", 0)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            self.response_times.append(duration)
            self.total_response_time += duration
            self.api_call_count += 1 # Increment API call count (approximation)

            # Construct assistant response entry for history
            assistant_response_data = {
                "role": "assistant",
                "agent": "interviewer", # Identify the source agent
                "content": response_content,
                "response_type": response_type,
                "timestamp": end_time.isoformat(),
                "processing_time": duration,
                "metadata": metadata
            }
            self.conversation_history.append(assistant_response_data)

            # Publish event for assistant response (other agents might listen)
            self.event_bus.publish(Event(
                EventType.ASSISTANT_RESPONSE,
                {
                    "session_id": self.session_id,
                    "response": assistant_response_data
                }
            ))

            self.logger.info(f"Interviewer response generated in {duration:.2f} seconds. Type: {response_type}")
            # Return the response data structure expected by the API layer/frontend
            return assistant_response_data # Return the full entry with metadata

        except Exception as e:
            self.logger.exception(f"Error processing message: {e}") # Use exception logging
            self.event_bus.publish(Event(EventType.ERROR, {"error": str(e), "details": "Error during message processing"}))
            # Return a user-friendly error message, also logged to history
            error_response = {
                "role": "system",
                "content": "Sorry, I encountered an error processing your request. Please try again.",
                "timestamp": datetime.utcnow().isoformat(),
                "is_error": True
            }
            self.conversation_history.append(error_response) # Log error internally
            return error_response # Return error structure

    def _get_agent_context(self) -> AgentContext:
        """Prepare the context object for an agent call."""
        return AgentContext(
            session_id=self.session_id,
            user_id=self.user_id,
            conversation_history=self.conversation_history, # Pass current history
            session_config=self.session_config, # Pass session config
            event_bus=self.event_bus, # Pass event bus
            logger=self.logger # Pass logger
        )

    def end_interview(self) -> Dict[str, Any]:
        """
        Ends the interview session, triggers final analyses from Coach/SkillAssessor,
        and returns a consolidated result.
        """
        self.logger.info(f"Ending interview session {self.session_id}")
        # Publish event to signal agents (like Interviewer) to move to completed state
        self.event_bus.publish(Event(EventType.SESSION_END, {"session_id": self.session_id}))

        final_results = {
            "status": "Interview Ended",
            "session_id": self.session_id,
            "coaching_summary": None,
            "skill_profile": None
        }

        # Trigger Skill Assessor profile generation
        try:
            skill_agent = self._get_agent("skill_assessor")
            if skill_agent and hasattr(skill_agent, 'generate_skill_profile'):
                skill_profile = skill_agent.generate_skill_profile()
                final_results["skill_profile"] = skill_profile
                self.logger.info("Generated skill profile.")
            else:
                self.logger.warning("Skill assessor agent not found or missing generate_skill_profile method.")
                final_results["skill_profile"] = {"error": "Skill profile could not be generated."}
        except Exception as e:
            self.logger.exception(f"Error generating skill profile: {e}")
            final_results["skill_profile"] = {"error": f"Skill profile generation failed: {e}"}

        # Trigger Coach summary generation
        try:
            coach_agent = self._get_agent("coach")
            if coach_agent and hasattr(coach_agent, 'generate_coaching_summary'):
                coaching_summary = coach_agent.generate_coaching_summary(self.session_id) # Pass session ID
                final_results["coaching_summary"] = coaching_summary
                self.logger.info("Generated coaching summary.")
            else:
                self.logger.warning("Coach agent not found or missing generate_coaching_summary method.")
                final_results["coaching_summary"] = {"error": "Coaching summary could not be generated."}
        except Exception as e:
            self.logger.exception(f"Error generating coaching summary: {e}")
            final_results["coaching_summary"] = {"error": f"Coaching summary generation failed: {e}"}

        # Perform any final cleanup if needed (reset_session clears most state)
        # self.reset_session() # Usually called explicitly via API endpoint

        return final_results

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Returns the full conversation history."""
        return self.conversation_history

    def get_session_stats(self) -> Dict[str, Any]:
        """Returns performance and usage statistics for the session."""
        avg_response_time = (self.total_response_time / len(self.response_times)) if self.response_times else 0
        return {
            "session_id": self.session_id,
            "total_messages": len(self.conversation_history),
            "user_messages": sum(1 for msg in self.conversation_history if msg.get("role") == "user"),
            "assistant_messages": sum(1 for msg in self.conversation_history if msg.get("role") == "assistant"),
            "system_messages": sum(1 for msg in self.conversation_history if msg.get("role") == "system"),
            "total_response_time_seconds": round(self.total_response_time, 2),
            "average_response_time_seconds": round(avg_response_time, 2),
            "total_api_calls": self.api_call_count,
            "total_tokens_used": self.total_tokens_used, # Placeholder
        }

    def reset_session(self):
        """Resets the session state, including history and agent instances."""
        self.logger.warning(f"Resetting session {self.session_id}")
        self.conversation_history = []
        self._agents = {} # Clear loaded agent instances
        
        # Reset performance tracking
        self.response_times = []
        self.total_response_time = 0.0
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        # Publish reset event for agents to clear their internal state
        self.event_bus.publish(Event(EventType.SESSION_RESET, {"session_id": self.session_id}))
        self.logger.info(f"Session {self.session_id} has been reset.")

# Example Usage (Conceptual - Needs actual InterviewSession model)
if __name__ == '__main__':
    # This is for basic testing/demonstration
    # Requires a valid InterviewSession instance
    try:
        # Example config (replace with actual model instantiation)
        config_data = {
            "session_id": "test-session-main",
            "user_id": "test-user-main",
            "job_role": "Senior Software Engineer",
            "job_description": "Develop scalable web applications using Python and React.",
            "resume_content": "Experienced SWE with 5 years in backend development.",
            "interview_style": InterviewStyle.FORMAL.value,
            "company_name": "TestCorp",
            "difficulty_level": "medium",
            "question_count": 3 # Short for testing
            # Add other fields required by InterviewSession model
        }
        # Assuming InterviewSession can be created from a dict or **kwargs
        session_config = InterviewSession(**config_data) 
        
        manager = SessionManager(session_id=session_config.session_id, user_id=session_config.user_id, session_config=session_config)

        # Simulate conversation
        print("--- Starting Interview ---")
        # First message is often null/empty to trigger intro+first question
        response1 = manager.process_message("") 
        print(f"[Assistant ({response1.get('agent')})]: {response1.get('content')}")
        
        if response1.get('response_type') == 'question':
            response2 = manager.process_message("I am a highly motivated engineer with experience in Python and cloud platforms. I enjoy building robust systems.")
            print(f"[User]: I am a highly motivated engineer with experience in Python and cloud platforms. I enjoy building robust systems.")
            print(f"[Assistant ({response2.get('agent')})]: {response2.get('content')}")

            if response2.get('response_type') == 'question':
                response3 = manager.process_message("Tell me about a time you faced a significant technical challenge and how you overcame it.")
                print(f"[User]: Tell me about a time you faced a significant technical challenge and how you overcame it.")
                print(f"[Assistant ({response3.get('agent')})]: {response3.get('content')}")

                # ... continue simulation ...

        print("\n--- Ending Interview ---")
        final_results = manager.end_interview()
        print("\nFinal Session Results:")
        # Pretty print the final results dictionary
        print(json.dumps(final_results, indent=2)) 

        print("\n--- Session Stats ---")
        stats = manager.get_session_stats()
        print(json.dumps(stats, indent=2))

        # manager.reset_session()
        # print("\n--- Session Reset --- ")
        
    except ImportError:
        print("Could not import InterviewSession model for example usage.")
    except Exception as e:
        print(f"An error occurred during example usage: {e}")
        logging.exception("Example usage error") # Log traceback

    # This is for basic testing/demonstration
    config = InterviewSession(
        session_id="test-session-123",
        user_id="test-user",
        job_role="Software Engineer",
        interview_style=InterviewStyle.BEHAVIORAL,
    )

    manager = SessionManager(session_id=config.session_id, user_id=config.user_id, session_config=config)

    # Simulate conversation
    response1 = manager.process_message("Tell me about yourself.")
    print("Assistant:", response1['content'])

    response2 = manager.process_message("Tell me about a time you faced a challenge.")
    print("Assistant:", response2['content'])

    stats = manager.get_session_stats()
    print("Session Stats:", stats)

    # End the interview
    final = manager.end_interview()
    print("Final Summary:", final['summary'])

    manager.reset_session()
    print("Session Reset.") 