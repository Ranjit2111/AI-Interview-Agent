"""
Coach agent module for providing feedback and guidance to users during interview preparation.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

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
from backend.utils.common import safe_get_or_default
from backend.agents.constants import DEFAULT_VALUE_NOT_PROVIDED


class CoachAgent(BaseAgent):
    """
    Agent that provides detailed feedback on interview answers and final summaries.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        resume_content: Optional[str] = None,
        job_description: Optional[str] = None,
    ):
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.resume_content = resume_content or ""
        self.job_description = job_description or ""
        
        self._setup_llm_chains()
    
    def _setup_llm_chains(self) -> None:
        """Set up LangChain chains for the agent's tasks."""
        self.evaluate_answer_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(EVALUATE_ANSWER_TEMPLATE),
            output_key="evaluation_text" 
        )
        
        self.final_summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(FINAL_SUMMARY_TEMPLATE),
            output_key="summary_json"
        )

    def evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Evaluates a single question-answer pair in the context of the interview.
        
        Returns:
            A string containing conversational coaching feedback.
        """
        inputs = self._build_evaluation_inputs(question, answer, justification, conversation_history)
        
        response = invoke_chain_with_error_handling(
            self.evaluate_answer_chain,
            inputs,
            self.logger,
            "EvaluateAnswerChain",
            output_key="evaluation_text"
        )

        return self._extract_feedback_text(response)
    
    def _build_evaluation_inputs(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Build inputs for the evaluation chain."""
        history_str = format_conversation_history(conversation_history, max_messages=10, max_content_length=200)
        
        return {
            "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            "conversation_history": history_str,
            "question": question or "No question provided.",
            "answer": answer or "No answer provided.",
            "justification": justification or "No justification provided."
        }
    
    def _extract_feedback_text(self, response: Any) -> str:
        """Extract feedback text from LLM response with simplified error handling."""
        if isinstance(response, str) and response.strip():
            return response
        
        if isinstance(response, dict):
            # Try different possible keys
            for key in ['evaluation_text', 'text']:
                if key in response and isinstance(response[key], str):
                    return response[key]
        
        return "Could not generate coaching feedback for this answer."

    def generate_final_summary(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a final coaching summary at the end of the interview.
        
        Returns:
            A dictionary containing the final summary with patterns, strengths, 
            weaknesses, improvement areas, and recommended resources.
        """
        inputs = self._build_summary_inputs(conversation_history)
        
        response = invoke_chain_with_error_handling(
            self.final_summary_chain,
            inputs,
            self.logger,
            "FinalSummaryChain",
            output_key="summary_json"
        )
        
        return self._process_summary_response(response)
    
    def _build_summary_inputs(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build inputs for the summary chain."""
        history_str = format_conversation_history(conversation_history)
        
        return {
            "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            "conversation_history": history_str
        }
    
    def _process_summary_response(self, response: Any) -> Dict[str, Any]:
        """Process the summary response with simplified error handling."""
        default_summary = {
            "patterns_tendencies": "Could not generate patterns/tendencies feedback.",
            "strengths": "Could not generate strengths feedback.",
            "weaknesses": "Could not generate weaknesses feedback.",
            "improvement_focus_areas": "Could not generate improvement focus areas.",
            "resource_search_topics": [],
            "recommended_resources": []
        }
        
        if isinstance(response, dict):
            summary = response
        elif isinstance(response, str):
            summary = parse_json_with_fallback(response, default_summary, self.logger)
        else:
            return default_summary
        
        # Ensure it's a valid dict with required structure
        if not isinstance(summary, dict):
            return default_summary
            
        # Add recommended_resources if not present
        if "resource_search_topics" in summary and "recommended_resources" not in summary:
            summary["recommended_resources"] = []
            
        return summary

    def process(self, context: AgentContext) -> Any:
        """
        Main processing function for the CoachAgent.
        Primary logic is in specific methods called by Orchestrator.
        """
        return {"status": "CoachAgent processed context, primary logic is in specific methods."}
            
