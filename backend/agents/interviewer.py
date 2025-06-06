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
    INTRODUCTION_TEMPLATES,
    TIME_AWARE_NEXT_ACTION_TEMPLATE,
    QUESTION_TEMPLATES, 
    TEMPLATE_VARIABLES, 
    GENERAL_QUESTIONS

)
from backend.utils.llm_utils import (
    invoke_chain_with_error_handling,
    format_conversation_history,
)
from backend.utils.common import get_current_timestamp, safe_get_or_default
from backend.utils.time_manager import InterviewTimeManager, TimeContext, TimePhase
from backend.agents.constants import (
    DEFAULT_JOB_ROLE, DEFAULT_COMPANY_NAME, DEFAULT_VALUE_NOT_PROVIDED,
    DEFAULT_OPENING_QUESTION, DEFAULT_FALLBACK_QUESTION, MINIMUM_QUESTION_COUNT,
    ESTIMATED_TIME_PER_QUESTION, ERROR_INTERVIEW_SETUP, ERROR_INTERVIEW_CONCLUDED,
    ERROR_NO_QUESTION_TEXT, INTERVIEW_CONCLUSION
)
from backend.agents.interview_state import InterviewState, InterviewPhase

class InterviewerAgent(BaseAgent):
    """
    Agent that conducts interview sessions with improved structure and time awareness.
    """
    
    def __init__(
        self,
        llm_service: LLMService, 
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        interview_style: InterviewStyle = InterviewStyle.CASUAL,
        job_role: str = "",
        job_description: str = "",
        resume_content: str = "",
        difficulty_level: str = "medium",
        question_count: Optional[int] = None,
        company_name: Optional[str] = None,
        interview_duration_minutes: Optional[int] = None,
        use_time_based_interview: bool = False
    ):
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.interview_style = interview_style
        self.job_role = job_role
        self.job_description = job_description
        self.resume_content = resume_content
        self.difficulty_level = difficulty_level
        self.question_count = question_count or 15  # Default fallback
        self.company_name = company_name
        
        # Time-based interview support
        self.interview_duration_minutes = interview_duration_minutes
        self.use_time_based_interview = use_time_based_interview
        self.time_manager: Optional[InterviewTimeManager] = None
        
        # Initialize time manager if using time-based interview
        if self.use_time_based_interview and self.interview_duration_minutes:
            self.time_manager = InterviewTimeManager(self.interview_duration_minutes)
            self._setup_time_callbacks()
        
        self.state = InterviewState()
        self._setup_llm_chains()
        
        # Subscribe to events
        self.subscribe(EventType.SESSION_START, self._handle_session_start)
        self.subscribe(EventType.SESSION_END, self._handle_session_end) 
        self.subscribe(EventType.SESSION_RESET, self._handle_session_reset)
    
    def _setup_time_callbacks(self) -> None:
        """Setup time manager callbacks for agentic notifications."""
        if not self.time_manager:
            return
            
        def on_phase_change(time_context: TimeContext):
            self.logger.info(f"Interview phase changed to: {time_context.current_phase.value}")
            
        def on_time_warning(time_context: TimeContext):
            self.logger.warning(f"Time warning: {time_context.remaining_minutes:.1f} minutes remaining")
            
        def on_halfway_point(time_context: TimeContext):
            self.logger.info("Interview halfway point reached")
            
        def on_final_warning(time_context: TimeContext):
            self.logger.warning("Final time warning: Interview should be concluding soon")
            
        self.time_manager.register_callback("phase_change", on_phase_change)
        self.time_manager.register_callback("time_warning", on_time_warning)
        self.time_manager.register_callback("halfway_point", on_halfway_point)
        self.time_manager.register_callback("final_warning", on_final_warning)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the interviewer agent."""
        time_context = ""
        if self.use_time_based_interview and self.time_manager:
            time_info = self.time_manager.get_time_based_prompt_context()
            time_context = f"""
TIME AWARENESS:
- Interview Duration: {self.interview_duration_minutes} minutes
- Current Phase: {time_info['current_time_phase']}
- Progress: {time_info['time_progress_percentage']}%
- Time Pressure: {time_info['time_pressure']}
"""
        
        base_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
            job_role=safe_get_or_default(self.job_role, DEFAULT_JOB_ROLE),
            interview_style=self.interview_style.value,
            resume_content=safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            job_description=safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            target_question_count=self.question_count
        )
        
        return base_prompt + time_context
    
    def _setup_llm_chains(self) -> None:
        """Set up LangChain chains using self.llm."""
        self.job_specific_question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(JOB_SPECIFIC_TEMPLATE),
        )
        
        # Use time-aware template if using time-based interview
        next_action_template = TIME_AWARE_NEXT_ACTION_TEMPLATE if self.use_time_based_interview else NEXT_ACTION_TEMPLATE
        
        self.next_action_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(next_action_template),
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
        
        # Create duration text based on interview type
        if self.use_time_based_interview and self.interview_duration_minutes:
            duration = f"around {self.interview_duration_minutes} minutes"
            # Start the timer when creating introduction
            if self.time_manager and not self.time_manager.is_active:
                self.time_manager.start_interview()
                self.logger.info("Started interview timer")
        else:
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
        
        # Update agent configuration from session config
        self.job_role = config.get("job_role", self.job_role)
        self.job_description = config.get("job_description", self.job_description)
        self.resume_content = config.get("resume_content", self.resume_content)
        self.difficulty_level = config.get("difficulty", self.difficulty_level)
        self.company_name = config.get("company_name", self.company_name)
        
        # Handle time-based interview settings
        self.use_time_based_interview = config.get("use_time_based_interview", self.use_time_based_interview)
        self.interview_duration_minutes = config.get("interview_duration_minutes", self.interview_duration_minutes)
        
        # Update question count (only if not using time-based)
        if not self.use_time_based_interview:
            self.question_count = config.get("target_question_count", self.question_count)
        
        # Initialize time manager if switching to time-based
        if self.use_time_based_interview and self.interview_duration_minutes and not self.time_manager:
            self.time_manager = InterviewTimeManager(self.interview_duration_minutes)
            self._setup_time_callbacks()
            self.logger.info(f"Initialized time manager for {self.interview_duration_minutes} minutes")
        
        # Update interview style if provided
        style_value = config.get("style")
        if style_value:
            if isinstance(style_value, str):
                try:
                    self.interview_style = InterviewStyle(style_value)
                except ValueError:
                    self.logger.warning(f"Invalid interview style: {style_value}")
            elif hasattr(style_value, 'value'):
                self.interview_style = style_value
        
        self.logger.info(f"Updated agent config: job_role={self.job_role}, style={self.interview_style.value}, company={self.company_name}, time_based={self.use_time_based_interview}")

    def _handle_session_end(self, event: Event) -> None:
        """Handle session end events."""
        self.state.phase = InterviewPhase.COMPLETED
        
        # Stop timer if active
        if self.time_manager and self.time_manager.is_active:
            final_context = self.time_manager.stop_interview()
            self.logger.info(f"Session ended. Final interview duration: {final_context.elapsed_minutes:.1f} minutes")
    
    def _handle_session_reset(self, event: Event) -> None:
        """Handle session reset events."""
        self.state.reset()
        # Also update config when session is reset
        self._update_config_from_event(event)

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
        
        base_inputs = {
            "job_role": safe_get_or_default(self.job_role, DEFAULT_VALUE_NOT_PROVIDED),
            "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
            "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
            "interview_style": self.interview_style.value,
            "difficulty_level": self.difficulty_level,
            "areas_covered_so_far": self.state.get_covered_topics_str(),
            "conversation_history": history_str,
            "previous_question": self.state.current_question or "[No previous question]",
            "candidate_answer": last_user_message
        }
        
        # Add time management context if using time-based interview
        if self.use_time_based_interview and self.time_manager:
            time_info = self.time_manager.get_time_based_prompt_context()
            base_inputs.update({
                "use_time_based": True,
                "interview_type": "Time-based",
                "current_time_phase": time_info["current_time_phase"],
                "time_progress_percentage": time_info["time_progress_percentage"],
                "remaining_minutes": time_info["remaining_minutes"],
                "time_pressure": time_info["time_pressure"],
                "time_based_suggestions": time_info["time_based_suggestions"]
            })
        else:
            # Question-based interview context
            base_inputs.update({
                "use_time_based": False,
                "interview_type": "Question-based",
                "target_question_count": self.question_count,
                "questions_asked_count": self.state.asked_question_count,
                "current_time_phase": "question_based",
                "time_progress_percentage": 0,
                "remaining_minutes": 999,
                "time_pressure": "low",
                "time_based_suggestions": ["Continue with question-based approach"]
            })
        
        return base_inputs
        
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
        
        # Time-based interview logic
        if self.use_time_based_interview and self.time_manager:
            time_context = self.time_manager.get_time_context()
            
            # Force end if time is up
            if time_context.remaining_minutes <= 0:
                response["action_type"] = "end_interview"
                response["justification"] = "Interview time has expired."
                self.logger.info("Forcing interview end due to time expiration")
            
            # Suggest ending if in closing phase and agent wants to end
            elif action_type == "end_interview" and time_context.current_phase == TimePhase.CLOSING:
                self.logger.info("Agent decided to end interview during closing phase")
            
            # Prevent ending too early unless specifically justified
            elif action_type == "end_interview" and time_context.progress_percentage < 70:
                self.logger.warning("Agent wants to end interview early, continuing instead")
                response["action_type"] = "ask_new_question"
                response["next_question_text"] = DEFAULT_FALLBACK_QUESTION
                response["justification"] = "Continuing interview as significant time remains."
                
        else:
            # Original question-based logic
            if action_type == "end_interview" and not self.state.can_end_interview(MINIMUM_QUESTION_COUNT):
                response["action_type"] = "ask_new_question"
                response["next_question_text"] = DEFAULT_FALLBACK_QUESTION
                response["justification"] = "Continuing interview to meet minimum question count."
        
        # Stop timer if ending interview
        if response.get("action_type") == "end_interview" and self.time_manager:
            final_context = self.time_manager.stop_interview()
            self.logger.info(f"Interview concluded after {final_context.elapsed_minutes:.1f} minutes")
        
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
        # Update configuration from context first
        if context.session_config:
            config_dict = context.session_config.model_dump() if hasattr(context.session_config, 'model_dump') else vars(context.session_config)
            
            # Manually convert enum values to strings for JSON serialization
            for key, value in config_dict.items():
                if hasattr(value, 'value'):  # This is an enum
                    config_dict[key] = value.value
            
            self._update_config_from_event(Event(
                event_type=EventType.SESSION_START,
                source=self.__class__.__name__,
                data={"config": config_dict}
            ))
        
        self._generate_questions()
        
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