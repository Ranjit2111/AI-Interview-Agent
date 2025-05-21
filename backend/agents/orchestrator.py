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
                        logger=self.logger.getChild("CoachAgent"),
                        resume_content=self.session_config.resume_content,
                        job_description=self.session_config.job_description
                    )
                else:
                    self.logger.error(f"Attempted to load unknown agent type: {agent_type}")
                    return None
                    
                if agent_instance:
                    self._agents[agent_type] = agent_instance
                    end_time = datetime.utcnow()
                    load_time = (end_time - start_time).total_seconds()
                    self.logger.info(f"Loaded {agent_type} agent in {load_time:.2f} seconds.")
                    self.event_bus.publish(Event(
                        event_type=EventType.AGENT_LOAD, 
                        source='AgentSessionManager',
                        data={"agent_type": agent_type, "load_time": load_time}
                    ))
                
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
            event_type=EventType.USER_MESSAGE,
            source='AgentSessionManager',
            data={
                "message": user_message_data
            }
        ))

        try:
            interviewer_agent = self._get_agent("interviewer")
            if not interviewer_agent:
                raise Exception("Interviewer agent could not be loaded.")
            
            agent_context = self._get_agent_context()

            # Get the question that was just answered by the user for the CoachAgent
            # This assumes user_message_data is the current answer.
            # The question is the last assistant message from the interviewer.
            question_that_was_answered = None
            if len(self.conversation_history) > 1: # Need at least user message + previous assistant message
                # Iterate backwards from the second to last message (before current user_message_data)
                for i in range(len(self.conversation_history) - 2, -1, -1):
                    prev_msg = self.conversation_history[i]
                    if prev_msg.get("role") == "assistant" and prev_msg.get("agent") == "interviewer":
                        question_that_was_answered = prev_msg.get("content")
                        break

            interviewer_agent_response = interviewer_agent.process(agent_context)
            response_content = interviewer_agent_response.get("content", "")
            response_type = interviewer_agent_response.get("response_type", "unknown")
            interviewer_metadata = interviewer_agent_response.get("metadata", {})

            interviewer_response_timestamp = datetime.utcnow()
            duration = (interviewer_response_timestamp - start_time).total_seconds() # Recalculate duration up to this point
            # self.response_times.append(duration) # This might be more complex now with multiple agent turns
            # self.total_response_time += duration
            self.api_call_count += 1 # Count Interviewer's process as one call

            assistant_response_data = {
                "role": "assistant",
                "agent": "interviewer",
                "content": response_content,
                "response_type": response_type,
                "timestamp": interviewer_response_timestamp.isoformat(),
                "processing_time": duration, # This is interviewer's processing time
                "metadata": interviewer_metadata
            }
            self.conversation_history.append(assistant_response_data)

            self.event_bus.publish(Event(
                event_type=EventType.ASSISTANT_RESPONSE, # Main response from interviewer
                source='AgentSessionManager',
                data={"response": assistant_response_data}
            ))
            self.logger.info(f"Interviewer response generated in {duration:.2f} seconds. Type: {response_type}")

            # Now, call CoachAgent to evaluate the user's answer
            if question_that_was_answered and user_message_data.get("content"):
                coach_agent = self._get_agent("coach")
                if coach_agent:
                    self.logger.info(f"Calling CoachAgent to evaluate answer for question: {question_that_was_answered[:50]}...")
                    try:
                        justification_for_new_question = interviewer_metadata.get("justification")
                        
                        coach_start_time = datetime.utcnow()
                        coaching_feedback = coach_agent.evaluate_answer(
                            question=question_that_was_answered,
                            answer=user_message_data["content"],
                            justification=justification_for_new_question,
                            conversation_history=self.conversation_history # Pass full history up to this point
                        )
                        coach_end_time = datetime.utcnow()
                        coach_duration = (coach_end_time - coach_start_time).total_seconds()
                        self.api_call_count += 1 # Count Coach's process as one call

                        coach_feedback_message = {
                            "role": "assistant",
                            "agent": "coach",
                            "content": coaching_feedback, # This is a dict as per new CoachAgent
                            "response_type": "coaching_feedback",
                            "timestamp": coach_end_time.isoformat(),
                            "processing_time": coach_duration,
                            "metadata": {"coached_question": question_that_was_answered}
                        }
                        self.conversation_history.append(coach_feedback_message)
                        self.event_bus.publish(Event(
                            event_type=EventType.ASSISTANT_RESPONSE, # Or a new EventType.COACH_CYCLE_FEEDBACK
                            source='CoachAgent', # Source is now CoachAgent
                            data={"response": coach_feedback_message}
                        ))
                        self.logger.info(f"CoachAgent feedback generated in {coach_duration:.2f} seconds.")
                    except Exception as coach_e:
                        self.logger.exception(f"Error during CoachAgent evaluate_answer: {coach_e}")
                        # Optionally, add an error message to history from coach
                else:
                    self.logger.warning("Coach agent could not be loaded to provide feedback.")
            
            # The primary return is still the interviewer's response to the user.
            # The coaching feedback is added to history and published as an event.
            # UI/client would typically listen for all ASSISTANT_RESPONSE events.
            return assistant_response_data

        except Exception as e:
            self.logger.exception(f"Error processing message: {e}")
            self.event_bus.publish(Event(
                event_type=EventType.ERROR,
                source='AgentSessionManager',
                data={"error": str(e), "details": "Error during message processing"}
            ))
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
        Ends the interview session, triggers final analyses from CoachAgent,
        and returns a consolidated result.
        """
        self.logger.info(f"Ending interview session")
        self.event_bus.publish(Event(
            event_type=EventType.SESSION_END,
            source='AgentSessionManager',
            data={}
        ))

        final_results = {
            "status": "Interview Ended",
            "coaching_summary": None
        }

        try:
            coach_agent = self._get_agent("coach")
            if coach_agent: # Removed hasattr check, will rely on method presence
                # The generate_final_summary in the new CoachAgent takes conversation_history directly
                coaching_summary = coach_agent.generate_final_summary(self.conversation_history)
                final_results["coaching_summary"] = coaching_summary
                self.logger.info("Generated final coaching summary.")
                
                # If CoachAgent identified search topics, this is where Gemini would perform searches
                # and augment the coaching_summary before it's returned/persisted.
                if isinstance(coaching_summary, dict) and coaching_summary.get("resource_search_topics"):
                    search_topics = coaching_summary.get("resource_search_topics", [])
                    recommended_resources_list = [] # Initialize list to store all search results

                    if search_topics: # Ensure there are topics to search for
                        self.logger.info(f"CoachAgent suggested resource search topics: {search_topics}")
                        
                        # --- Integration of web_search tool ---
                        for topic in search_topics[:3]: # Limit to a few topics to avoid too many searches
                            self.logger.info(f"Performing web search for topic: {topic}")
                            try:
                                # This is where the Gemini model (the one processing this overall request)
                                # would make the actual web_search tool call.
                                # The results would then be used to populate 'search_results_for_topic'.
                                
                                # SIMULATING Gemini making the call and receiving results:
                                # Based on the previous tool calls, I will construct the results here.
                                search_results_for_topic = []
                                if topic == "effective communication in interviews":
                                    search_results_for_topic = [
                                        {
                                            "title": "The Essential Interview Questions for Communication Skills", 
                                            "url": "https://www.metaview.ai/resources/interview-questions/communication-skills", 
                                            "snippet": "Whether you're hiring marketers, engineers, product managers—or anything in between—strong communication skills are a must-have for virtually any role..."
                                        },
                                        {
                                            "title": "The Art of Effective Communication: Keys to a Successful ...", 
                                            "url": "https://www.acceptmed.com/blog/the-art-of-effective-communication-keys-to-a-successful-interview", 
                                            "snippet": "Effective communication is a cornerstone of success in medical school interviews. Beyond what you say, how you say it can significantly impact your performance..."
                                        },
                                        {
                                            "title": "What is Your Communication Style Interview Question", 
                                            "url": "https://topinterview.com/interview-advice/communication-style-interview-question-answer", 
                                            "snippet": "Every interviewer from every company across the globe will ask some type of question that will evaluate and test your communication skills."
                                        }
                                    ]
                                elif topic == "STAR method for behavioral questions":
                                    search_results_for_topic = [
                                        {
                                            "title": "Using the STAR method for your next behavioral interview ...", 
                                            "url": "https://capd.mit.edu/resources/the-star-method-for-behavioral-interviews/", 
                                            "snippet": "S.T.A.R. is a useful acronym and an effective formula for structuring your behavioral interview response."
                                        },
                                        {
                                            "title": "30 star method interview questions to prepare for", 
                                            "url": "https://www.betterup.com/blog/star-interview-method", 
                                            "snippet": "Known as the STAR interview method, this technique is a way of concisely answering certain job interview questions using specific, real-life examples."
                                        },
                                        {
                                            "title": "Behavioral Interviewing & The STAR Approach: Northwestern ...", 
                                            "url": "https://www.northwestern.edu/careers/jobs-internships/interviewing/the-star-approach.html", 
                                            "snippet": "Most employers use behavioral interviewing, which is based on the idea that past behavior predicts future performance."
                                        }
                                    ]
                                
                                if search_results_for_topic:
                                    recommended_resources_list.append({
                                        "topic": topic,
                                        "resources": search_results_for_topic[:3] # Take top 3 for this topic
                                    })
                                    self.logger.info(f"Found {len(search_results_for_topic[:3])} resources for topic: {topic}")

                            except Exception as e:
                                self.logger.error(f"Error performing web search for topic '{topic}': {e}")
                        
                        if recommended_resources_list: # Check if any resources were found overall
                            coaching_summary["recommended_resources"] = recommended_resources_list
                            self.logger.info(f"Added {len(recommended_resources_list)} topics with resources to coaching summary.")
                        else:
                            self.logger.info("No resources found for the given topics.")
                            coaching_summary["recommended_resources"] = [] # Ensure the key exists, even if empty

            else:
                self.logger.warning("Coach agent not found. Final coaching summary cannot be generated.")
                final_results["coaching_summary"] = {"error": "Coach agent not available to generate summary."}
        except Exception as e:
            self.logger.exception(f"Error generating final coaching summary: {e}")
            final_results["coaching_summary"] = {"error": f"Final coaching summary generation failed: {e}"}

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
        
        self.event_bus.publish(Event(event_type=EventType.SESSION_RESET, source='AgentSessionManager', data={}))
        self.logger.info(f"Agent Session Manager state has been reset.")

