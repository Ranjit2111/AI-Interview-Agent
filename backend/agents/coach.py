"""
Coach agent module for providing feedback and guidance to users during interview preparation.
This agent analyzes interview performance and offers personalized advice for improvement.

TODO: Further Refactoring Plan:
  - Extract more template strings to coach_templates.py
  - Move method groups (evaluation methods, feedback methods, etc.) to separate modules
  - Modularize event handling code
  - Standardize error handling across all methods
  - Consider further splitting the CoachAgent class into smaller focused classes
"""

import logging
from typing import Dict, Any, List, Optional

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

try:
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import EventBus
    from backend.services.llm_service import LLMService
    from backend.agents.templates.coach_templates import (
        EVALUATE_ANSWER_TEMPLATE,
        FINAL_SUMMARY_TEMPLATE
    )
    from backend.utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        format_conversation_history
    )
except ImportError:
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import EventBus
    from ..services.llm_service import LLMService
    from .templates.coach_templates import (
        EVALUATE_ANSWER_TEMPLATE,
        FINAL_SUMMARY_TEMPLATE
    )
    from ..utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        format_conversation_history
    )

class CoachAgent(BaseAgent):
    """
    Agent that provides detailed, contextual feedback on interview answers
    and a final summary at the end of the interview.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        resume_content: Optional[str] = None,
        job_description: Optional[str] = None,
    ):
        """
        Initialize the coach agent.
        
        Args:
            llm_service: Language model service instance.
            event_bus: Event bus for inter-agent communication.
            logger: Logger for recording agent activity.
            resume_content: The candidate's resume content.
            job_description: The job description for the target role.
        """
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.resume_content = resume_content or ""
        self.job_description = job_description or ""
        
        self._setup_llm_chains()
        
        # Basic subscriptions (can be expanded if needed)
        if self.event_bus:
            # self.event_bus.subscribe(EventType.USER_MESSAGE, self._handle_user_response_for_coaching)
            # self.event_bus.subscribe(EventType.INTERVIEW_COMPLETED, self._handle_interview_completed_for_summary)
            pass # Subscriptions will be driven by Orchestrator for now

    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        self.logger.info("CoachAgent: Initializing LLM chains...")
        
        self.evaluate_answer_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(EVALUATE_ANSWER_TEMPLATE),
            output_key="evaluation_json" # Expecting a JSON string
        )
        
        self.final_summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(FINAL_SUMMARY_TEMPLATE),
            output_key="summary_json" # Expecting a JSON string
        )
        self.logger.info("CoachAgent: LLM chains setup complete.")

    def evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Evaluates a single question-answer pair in the context of the interview.

        Args:
            question: The interview question asked.
            answer: The user's answer to the question.
            justification: The InterviewerAgent's rationale for the next question (or current state).
            conversation_history: The full conversation history for broader context.

        Returns:
            A dictionary containing feedback across multiple dimensions.
            Example: {"conciseness": "Feedback...", "completeness": "Feedback..."}
        """
        self.logger.info(f"CoachAgent evaluating answer for question: {question[:50]}...")
        
        question_str = question or "No question provided."
        answer_str = answer or "No answer provided."
        justification_str = justification or "No justification provided."
        # Limit history string length to avoid overly large prompts for single answer eval
        history_str = format_conversation_history(conversation_history, max_messages=10, max_content_length=200)

        inputs = {
            "resume_content": self.resume_content or "Not provided.",
            "job_description": self.job_description or "Not provided.",
            "conversation_history": history_str,
            "question": question_str,
            "answer": answer_str,
            "justification": justification_str
        }

        raw_evaluation = invoke_chain_with_error_handling(
            self.evaluate_answer_chain,
            inputs,
            self.logger,
            "EvaluateAnswerChain",
            output_key="evaluation_json"
        )

        parsed_evaluation = parse_json_with_fallback(
            raw_evaluation, 
            default_value={
                "conciseness": "Error: Could not generate conciseness feedback.",
                "completeness": "Error: Could not generate completeness feedback.",
                "technical_accuracy_depth": "Error: Could not generate technical feedback.",
                "contextual_alignment": "Error: Could not generate alignment feedback.",
                "fixes_improvements": "Error: Could not generate improvement suggestions.",
                "star_support": "Error: Could not generate STAR feedback."
            },
            logger=self.logger
        )
        
        if not isinstance(parsed_evaluation, dict): # Ensure it's a dict
             parsed_evaluation = {"error": "Evaluation output was not a valid dictionary."}

        self.logger.debug(f"CoachAgent - Evaluation generated: {parsed_evaluation}")
        return parsed_evaluation

    def generate_final_summary(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a final coaching summary at the end of the interview.

        Args:
            conversation_history: The full conversation history of the interview.

        Returns:
            A dictionary containing the final summary, including patterns,
            strengths, weaknesses, improvement areas, and recommended resources.
        """
        self.logger.info("CoachAgent generating final summary...")
        
        history_str = format_conversation_history(conversation_history) # Full history for summary

        inputs = {
            "resume_content": self.resume_content or "Not provided.",
            "job_description": self.job_description or "Not provided.",
            "conversation_history": history_str
        }

        raw_summary = invoke_chain_with_error_handling(
            self.final_summary_chain,
            inputs,
            self.logger,
            "FinalSummaryChain",
            output_key="summary_json"
        )

        parsed_summary = parse_json_with_fallback(
            raw_summary,
            default_value={
                "patterns_tendencies": "Error: Could not generate patterns/tendencies feedback.",
                "strengths": "Error: Could not generate strengths feedback.",
                "weaknesses": "Error: Could not generate weaknesses feedback.",
                "improvement_focus_areas": "Error: Could not generate improvement focus areas.",
                "resource_search_topics": []
            },
            logger=self.logger
        )
        if not isinstance(parsed_summary, dict): # Ensure it's a dict
            parsed_summary = {"error": "Final summary output was not a valid dictionary."}

        # The plan mentions the assistant (Gemini) uses the search tool.
        # CoachAgent will prepare the search topics from parsed_summary.get("resource_search_topics", [])
        # The actual search and adding results will be handled by the orchestrating assistant (Gemini).
        # For now, we just return the LLM-generated topics.
        
        # Ensure 'recommended_resources' is initialized if search topics are present,
        # so Orchestrator/Gemini knows where to inject search results.
        if "resource_search_topics" in parsed_summary and parsed_summary["resource_search_topics"]:
            parsed_summary["recommended_resources"] = [] # Placeholder for Gemini to fill

        self.logger.debug(f"CoachAgent - Final summary (pre-search) generated: {parsed_summary}")
        return parsed_summary

    # Optional: Add event handlers if CoachAgent needs to react to events directly
    # def _handle_user_response_for_coaching(self, event: Event):
    #     # This would be triggered if Orchestrator isn't explicitly calling evaluate_answer
    #     pass

    # def _handle_interview_completed_for_summary(self, event: Event):
    #     # This would be triggered if Orchestrator isn't explicitly calling generate_final_summary
    #     pass
        
    def process(self, context: AgentContext) -> Any:
        """
        Main processing function for the CoachAgent.
        For this refactor, CoachAgent primarily acts on direct calls from Orchestrator
        (evaluate_answer, generate_final_summary) rather than through a generic process() call.
        This method can be kept minimal or used for event-driven actions if any remain.
        """
        self.logger.info("CoachAgent process() called. Currently, actions are primarily driven by direct method calls from Orchestrator.")
        # Example: If there were specific coaching requests handled via events:
        # if context.last_event and context.last_event.event_type == EventType.COACHING_REQUEST:
        #    return self._handle_specific_coaching_request(context.last_event.data)
        return {"status": "CoachAgent processed context, but primary logic is in specific methods."}

