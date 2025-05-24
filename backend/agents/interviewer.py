"""
Interviewer agent responsible for conducting interview sessions.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import random

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from backend.agents.base import BaseAgent, AgentContext
from backend.utils.event_bus import Event, EventBus, EventType
from backend.services.llm_service import LLMService
from backend.agents.config_models import InterviewStyle
from backend.agents.templates.interviewer_templates import (
    INTERVIEWER_SYSTEM_PROMPT,
    NEXT_ACTION_TEMPLATE,
    JOB_SPECIFIC_TEMPLATE,
INTRODUCTION_TEMPLATES
)
from backend.utils.llm_utils import (
    invoke_chain_with_error_handling,
    format_conversation_history,
)
from backend.utils.common import get_current_timestamp, safe_get_or_default
from backend.agents.constants import (
    DEFAULT_JOB_ROLE, DEFAULT_COMPANY_NAME, DEFAULT_VALUE_NOT_PROVIDED,
    DEFAULT_OPENING_QUESTION, DEFAULT_FALLBACK_QUESTION, MINIMUM_QUESTION_COUNT,
    ESTIMATED_TIME_PER_QUESTION, ERROR_INTERVIEW_SETUP, ERROR_INTERVIEW_CONCLUDED,
    ERROR_NO_QUESTION_TEXT, INTERVIEW_CONCLUSION
)
from backend.agents.interview_state import InterviewState, InterviewPhase
from backend.agents.question_templates import QUESTION_TEMPLATES, TEMPLATE_VARIABLES, GENERAL_QUESTIONS


class InterviewerAgent(BaseAgent):
    """
    Agent that conducts interview sessions with improved structure and minimal code.
    """
    
    def __init__(
        self,
        llm_service: LLMService, 
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        interview_style: InterviewStyle = InterviewStyle.FORMAL,
        job_role: str = "",
        job_description: str = "",
        resume_content: str = "",
        difficulty_level: str = "medium",
        question_count: int = 15,
        company_name: Optional[str] = None
    ):
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.interview_style = interview_style
        self.job_role = job_role
        self.job_description = job_description
        self.resume_content = resume_content
        self.difficulty_level = difficulty_level
        self.question_count = question_count
        self.company_name = company_name
        
        self.state = InterviewState()
        self._setup_llm_chains()
        
        # Subscribe to events
        self.subscribe(EventType.SESSION_START, self._handle_session_start)
        self.subscribe(EventType.SESSION_END, self._handle_session_end) 
        self.subscribe(EventType.SESSION_RESET, self._handle_session_reset)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the interviewer agent."""
        return INTERVIEWER_SYSTEM_PROMPT.format(
            job_role=safe_get_or_default(self.job_role, DEFAULT_JOB_ROLE),
            interview_style=self.interview_style.value,
            resume_content=safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            job_description=safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            target_question_count=self.question_count
        )
    
    def _setup_llm_chains(self) -> None:
        """Set up LangChain chains using self.llm."""
        self.job_specific_question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(JOB_SPECIFIC_TEMPLATE),
        )
        
        self.next_action_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(NEXT_ACTION_TEMPLATE),
        )
    
    def _generate_questions(self) -> None:
        """Generate the initial list of interview questions."""
        questions = [DEFAULT_OPENING_QUESTION]
        
        # Generate job-specific questions if possible
        num_specific_needed = self.question_count - len(questions)
        if self._can_generate_specific_questions() and num_specific_needed > 0:
            specific_questions = self._generate_job_specific_questions(num_specific_needed)
            questions.extend(q for q in specific_questions if q not in questions)
        
        # Fill remaining with generic questions
        num_generic_needed = self.question_count - len(questions)
        if num_generic_needed > 0:
            generic_questions = self._generate_generic_questions()
            for q in generic_questions:
                if len(questions) >= self.question_count:
                    break
                if q not in questions:
                    questions.append(q)
        
        self.state.set_questions(questions[:self.question_count])
    
    def _can_generate_specific_questions(self) -> bool:
        """Check if we have enough data to generate specific questions."""
        return bool(self.job_role and self.job_description and self.resume_content)
    
    def _generate_generic_questions(self) -> List[str]:
        """Generate generic questions using templates."""
        return self._create_questions_from_templates() + self._create_general_questions()
    
    def _create_questions_from_templates(self) -> List[str]:
        """Create questions from role-specific templates."""
        templates = QUESTION_TEMPLATES.get(self.interview_style, QUESTION_TEMPLATES[InterviewStyle.FORMAL])
        variables = TEMPLATE_VARIABLES.get(self.job_role, TEMPLATE_VARIABLES["Software Engineer"])
        
        questions = []
        for template in templates:
            try:
                placeholders = [p.strip("{}") for p in template.split() 
                              if p.startswith("{") and p.endswith("}")]
                format_args = {p: random.choice(variables[p]) for p in placeholders if p in variables}
                questions.append(template.format(**format_args))
            except (KeyError, ValueError):
                continue  # Skip templates that can't be formatted
        
        random.shuffle(questions)
        return questions
    
    def _create_general_questions(self) -> List[str]:
        """Create general interview questions."""
        questions = []
        for question in GENERAL_QUESTIONS:
            try:
                formatted_question = question.format(job_role=self.job_role or "role")
                questions.append(formatted_question)
            except (KeyError, ValueError):
                questions.append(question)  # Use unformatted if formatting fails
        
        return questions
    
    def _generate_job_specific_questions(self, num_questions: int) -> List[str]:
        """Generate job-specific questions using LLM."""
        inputs = {
            "job_role": safe_get_or_default(self.job_role, DEFAULT_VALUE_NOT_PROVIDED),
            "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            "num_questions": num_questions,
            "difficulty_level": self.difficulty_level,
            "interview_style": self.interview_style.value
        }

        response = invoke_chain_with_error_handling(
            self.job_specific_question_chain,
            inputs,
            self.logger,
            "Job Specific Question Chain",
            output_key="questions_json",
            default_creator=lambda: []
        )
        
        if isinstance(response, list):
            return [str(q) for q in response if isinstance(q, str) and q.strip()]
        
        return []
    
    def _create_introduction(self) -> str:
        """Create an introduction for the interview."""
        style_key = self.interview_style.value.lower()
        template = INTRODUCTION_TEMPLATES.get(style_key, INTRODUCTION_TEMPLATES["formal"])
        
        duration = f"around {self.question_count * ESTIMATED_TIME_PER_QUESTION} minutes"
        
        return template.format(
            job_role=safe_get_or_default(self.job_role, DEFAULT_JOB_ROLE),
            interview_duration=duration,
            company_name=safe_get_or_default(self.company_name, DEFAULT_COMPANY_NAME)
        )
    
    def _handle_session_start(self, event: Event) -> None:
        """Handle session start events."""
        self.state.reset()
        self._update_config_from_event(event)
        self._generate_questions()
    
    def _update_config_from_event(self, event: Event) -> None:
        """Update configuration from session start event."""
        config = event.data.get("config", {})
        
        if not isinstance(config, dict):
            return
    
    def _handle_session_end(self, event: Event) -> None:
        """Handle session end events."""
        self.state.phase = InterviewPhase.COMPLETED
    
    def _handle_session_reset(self, event: Event) -> None:
        """Handle session reset events."""
        self.state.reset()

    def _determine_next_action(self, context: AgentContext) -> Dict[str, Any]:
        """Use LLM to decide the next step and generate content."""
        inputs = self._build_action_inputs(context)
        
        response = invoke_chain_with_error_handling(
            self.next_action_chain,
            inputs,
            self.logger,
            "Next Action Chain",
            output_key="action_json",
            default_creator=lambda: {
                "action_type": "ask_new_question",
                "next_question_text": DEFAULT_FALLBACK_QUESTION,
                "justification": "Using fallback due to LLM chain error.",
                "newly_covered_topics": []
            }
        )
        
        return self._process_action_response(response)
    
    def _build_action_inputs(self, context: AgentContext) -> Dict[str, Any]:
        """Build inputs for the next action chain."""
        last_user_message = context.get_last_user_message() or "[No answer yet]"
        history_str = format_conversation_history(context.conversation_history[:-1])
        
        return {
            "job_role": safe_get_or_default(self.job_role, DEFAULT_VALUE_NOT_PROVIDED),
            "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            "interview_style": self.interview_style.value,
            "target_question_count": self.question_count,
            "questions_asked_count": self.state.asked_question_count,
            "areas_covered_so_far": self.state.get_covered_topics_str(),
            "conversation_history": history_str,
            "previous_question": self.state.current_question or "[No previous question]",
            "candidate_answer": last_user_message
        }
        
    def _process_action_response(self, response: Any) -> Dict[str, Any]:
        """Process and validate the action response from LLM."""
        default_action = {
            "action_type": "ask_new_question",
            "next_question_text": DEFAULT_FALLBACK_QUESTION,
            "justification": "Defaulting to a general question due to processing error.",
            "newly_covered_topics": []
        }
        
        # Try to parse response if it's not already a dict
        if not isinstance(response, dict):
            return default_action
        
        action_type = response.get("action_type")
        valid_actions = ["ask_follow_up", "ask_new_question", "end_interview"]
        
        if action_type not in valid_actions:
            return default_action
            
        # Override end_interview if not enough questions asked
        if action_type == "end_interview" and not self.state.can_end_interview(MINIMUM_QUESTION_COUNT):
            response["action_type"] = "ask_new_question"
            response["next_question_text"] = DEFAULT_FALLBACK_QUESTION
            response["justification"] = "Continuing interview to meet minimum question count."
        
        # Ensure newly_covered_topics is a list
        if not isinstance(response.get("newly_covered_topics"), list):
            response["newly_covered_topics"] = []
        
        return response

    def process(self, context: AgentContext) -> Dict[str, Any]:
        """Process the current context to determine the next step."""
        response_data = {
            "role": "assistant",
            "agent": "interviewer",
            "content": "",
            "response_type": "status",
            "timestamp": get_current_timestamp(),
            "metadata": {}
        }

        if self.state.phase == InterviewPhase.INITIALIZING:
            return self._handle_initialization(context, response_data)
        elif self.state.phase == InterviewPhase.INTRODUCING:
            return self._handle_introduction(response_data)
        elif self.state.phase == InterviewPhase.QUESTIONING:
            return self._handle_questioning(context, response_data)
        else:  # COMPLETED
            response_data["content"] = ERROR_INTERVIEW_CONCLUDED
            return response_data
    
    def _handle_initialization(self, context: AgentContext, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization phase."""
        self._handle_session_start(Event(
            event_type=EventType.SESSION_START,
            source=self.__class__.__name__,
            data={"config": context.session_config.dict()}
        ))
        
        if self.state.initial_questions:
            self.state.phase = InterviewPhase.INTRODUCING
            # Immediately proceed to introduction
            return self._handle_introduction(response_data)
        else:
            response_data["content"] = ERROR_INTERVIEW_SETUP
            response_data["response_type"] = "error"
            self.state.phase = InterviewPhase.COMPLETED
            
        return response_data

    def _handle_introduction(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle introduction phase."""
        response_data["content"] = self._create_introduction()
        response_data["response_type"] = "introduction"
        self.state.phase = InterviewPhase.QUESTIONING
        return response_data
    
    def _handle_questioning(self, context: AgentContext, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle questioning phase."""
        action_result = self._determine_next_action(context)
        
        action_type = action_result.get("action_type")
        next_question = action_result.get("next_question_text")
        new_topics = action_result.get("newly_covered_topics", [])

        if new_topics:
            self.state.add_covered_topics(new_topics)
        
        if action_type == "end_interview":
            self.state.phase = InterviewPhase.COMPLETED
            response_data["content"] = INTERVIEW_CONCLUSION
            response_data["response_type"] = "closing"
        elif next_question:
            self.state.ask_question(next_question)
            response_data["content"] = next_question
            response_data["response_type"] = "question"
            response_data["metadata"] = {
                "question_number": self.state.asked_question_count,
                "justification": action_result.get("justification")
            }
        else:
            self.state.phase = InterviewPhase.COMPLETED
            response_data["content"] = ERROR_NO_QUESTION_TEXT
            response_data["response_type"] = "closing"

        return response_data 