"""
Session Manager for coordinating agents.
Manages session state, history, and agent interactions.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Type
from datetime import datetime
from enum import Enum
import json

from backend.agents.base import BaseAgent, AgentContext
from backend.agents.interviewer import InterviewerAgent
from backend.agents.coach import CoachAgent
from backend.agents.skill_assessor import SkillAssessorAgent
from backend.utils.event_bus import Event, EventBus, EventType
from backend.agents.config_models import SessionConfig
from backend.config import get_logger
from backend.services.llm_service import LLMService


class AgentSessionManager:
    """
    Manages the flow of an interview preparation session.
    It routes messages between the user and various agents (Interviewer, Coach, etc.),
    maintains the conversation history, and handles session state.
    NO LONGER manages multiple sessions - only THE single session.
    """
    
    def __init__(self, llm_service: LLMService, event_bus: EventBus, logger: logging.Logger, session_config: SessionConfig):
        self.session_config = session_config
        self.conversation_history: List[Dict[str, Any]] = []
        
        self.logger = logger
        self.event_bus = event_bus
        self._llm_service = llm_service
        
        self.response_times: List[float] = []
        self.total_response_time = 0.0
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        self._agents: Dict[str, BaseAgent] = {}

        self.logger.info("Agent Session Manager initialized")
        config_dict = self.session_config.dict() if hasattr(self.session_config, 'dict') else vars(self.session_config)
        if config_dict:
            self.event_bus.publish(Event(event_type=EventType.SESSION_START, 
                                         source='AgentSessionManager', 
                                         data={"config": config_dict}))
    
    def _get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Lazy load agents, passing required dependencies."""
        if agent_type not in self._agents:
            start_time = datetime.utcnow()
            agent_instance: Optional[BaseAgent] = None
            try:
                if agent_type == "interviewer":
                    agent_instance = InterviewerAgent(
                        llm_service=self._llm_service, 
                        event_bus=self.event_bus,
                        logger=self.logger.getChild("InterviewerAgent")
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
                    return None
                    
                if agent_instance:
                    self._agents[agent_type] = agent_instance
                    end_time = datetime.utcnow()
                    load_time = (end_time - start_time).total_seconds()
                    self.logger.info(f"Loaded {agent_type} agent in {load_time:.2f} seconds.")
                    self.event_bus.publish(Event(EventType.AGENT_LOAD, {"agent_type": agent_type, "load_time": load_time}))
                
            except Exception as e:
                self.logger.exception(f"Failed to initialize agent {agent_type}: {e}")
                return None
                
        return self._agents.get(agent_type)
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Processes a user message, routes it primarily to the InterviewerAgent,
        and returns the agent's response. Other agents listen via events.
        Now assumes only one user (local).
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Processing message: '{message[:50]}...'")

        user_message_data = {
            "role": "user",
            "content": message,
            "timestamp": start_time.isoformat()
        }
        self.conversation_history.append(user_message_data)

        self.event_bus.publish(Event(
            EventType.USER_MESSAGE,
            {
                "message": user_message_data
            }
        ))

        try:
            interviewer_agent = self._get_agent("interviewer")
            if not interviewer_agent:
                raise Exception("Interviewer agent could not be loaded.")
            
            agent_context = self._get_agent_context()

            agent_response = interviewer_agent.process(agent_context)
            response_content = agent_response.get("content", "")
            response_type = agent_response.get("response_type", "unknown")
            metadata = agent_response.get("metadata", {})

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            self.response_times.append(duration)
            self.total_response_time += duration
            self.api_call_count += 1

            assistant_response_data = {
                "role": "assistant",
                "agent": "interviewer",
                "content": response_content,
                "response_type": response_type,
                "timestamp": end_time.isoformat(),
                "processing_time": duration,
                "metadata": metadata
            }
            self.conversation_history.append(assistant_response_data)

            self.event_bus.publish(Event(
                EventType.ASSISTANT_RESPONSE,
                {
                    "response": assistant_response_data
                }
            ))

            self.logger.info(f"Interviewer response generated in {duration:.2f} seconds. Type: {response_type}")
            return assistant_response_data

        except Exception as e:
            self.logger.exception(f"Error processing message: {e}")
            self.event_bus.publish(Event(EventType.ERROR, {"error": str(e), "details": "Error during message processing"}))
            error_response = {
                "role": "system",
                "content": "Sorry, I encountered an error processing your request. Please try again.",
                "timestamp": datetime.utcnow().isoformat(),
                "is_error": True
            }
            self.conversation_history.append(error_response)
            return error_response

    def _get_agent_context(self) -> AgentContext:
        """Prepare the context object for an agent call."""
        return AgentContext(
            session_id="local_session",
            conversation_history=self.conversation_history,
            session_config=self.session_config,
            event_bus=self.event_bus,
            logger=self.logger
        )

    def end_interview(self) -> Dict[str, Any]:
        """
        Ends the interview session, triggers final analyses from Coach/SkillAssessor,
        and returns a consolidated result.
        """
        self.logger.info(f"Ending interview session")
        self.event_bus.publish(Event(EventType.SESSION_END, {}))

        final_results = {
            "status": "Interview Ended",
            "coaching_summary": None,
            "skill_profile": None
        }

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

        try:
            coach_agent = self._get_agent("coach")
            if coach_agent and hasattr(coach_agent, 'generate_coaching_summary'):
                agent_context = self._get_agent_context()
                coaching_summary = coach_agent.generate_coaching_summary(agent_context)
                final_results["coaching_summary"] = coaching_summary
                self.logger.info("Generated coaching summary.")
            else:
                self.logger.warning("Coach agent not found or missing generate_coaching_summary method.")
                final_results["coaching_summary"] = {"error": "Coaching summary could not be generated."}
        except Exception as e:
            self.logger.exception(f"Error generating coaching summary: {e}")
            final_results["coaching_summary"] = {"error": f"Coaching summary generation failed: {e}"}

        return final_results

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
        self.logger.warning(f"Resetting Agent Session Manager state")
        self.conversation_history = []
        self._agents = {}
        
        self.response_times = []
        self.total_response_time = 0.0
        self.total_tokens_used = 0
        self.api_call_count = 0
        
        self.event_bus.publish(Event(EventType.SESSION_RESET, {}))
        self.logger.info(f"Agent Session Manager state has been reset.")

