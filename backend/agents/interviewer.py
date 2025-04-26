"""
Interviewer agent responsible for conducting interview sessions.
This agent asks questions, evaluates answers, and provides feedback.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import random
import uuid # Keep
from enum import Enum
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate # Keep
from langchain.chains import LLMChain # Keep


try:
    from backend.agents.base import BaseAgent, AgentContext # Keep
    from backend.utils.event_bus import Event, EventBus, EventType # Keep & Add EventType
    from backend.services.llm_service import LLMService # Added
    from backend.models.interview import InterviewStyle # Keep InterviewStyle, remove others
    from backend.agents.templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES,
        RESPONSE_FORMAT_TEMPLATE
    )
    from backend.agents.utils.llm_utils import (
        invoke_chain_with_error_handling, # Keep
        parse_json_with_fallback, # Keep
        # extract_field_safely, # Not used directly
        format_conversation_history # Keep
    )
except ImportError:
    from .base import BaseAgent, AgentContext # Keep
    from ..utils.event_bus import Event, EventBus # Keep
    from ..models.interview import InterviewStyle # Keep InterviewStyle
    from .templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES,
        RESPONSE_FORMAT_TEMPLATE
    )
    from .utils.llm_utils import (
        invoke_chain_with_error_handling, # Keep
        parse_json_with_fallback, # Keep
        # extract_field_safely, # Not used directly
        format_conversation_history # Keep
    )

# Keep InterviewState Enum (simplified)
class InterviewState(Enum):
    """Enum representing the simplified states of an interview."""
    INITIALIZING = "initializing"
    INTRODUCING = "introducing"
    QUESTIONING = "questioning"
    COMPLETED = "completed"


class InterviewerAgent(BaseAgent):
    """
    Agent that conducts interview sessions.
    
    The interviewer agent is responsible for:
    - Generating and asking appropriate interview questions
    - Evaluating candidate answers
    - Providing feedback on responses
    - Maintaining interview flow and context
    - Adapting to the specified interview style
    
    Enhanced with:
    - ReAct-style reasoning for more deliberate decision making
    - Structured output format for consistent responses
    - Advanced context management for better conversation flow
    - Dynamic prompt engineering based on interview context
    """
    
    def __init__(
        self,
        llm_service: LLMService, # Changed from api_key, model_name
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        # Parameters below are typically set via session_config or events
        interview_style: InterviewStyle = InterviewStyle.FORMAL,
        job_role: str = "",
        job_description: str = "",
        resume_content: str = "",
        difficulty_level: str = "medium",
        question_count: int = 5, # Reduced default for quicker tests
        company_name: Optional[str] = None
    ):
        """
        Initialize the interviewer agent.
        
        Args:
            llm_service: Language model service for the agent
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            interview_style: Style of interview to conduct
            job_role: Target job role for the interview
            job_description: Description of the job
            resume_content: Content of the candidate's resume
            difficulty_level: Initial difficulty level for specific questions
            question_count: Target number of questions to ask
            company_name: Name of the company for the introduction
        """
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        # Initialize with defaults, _handle_session_start will update from config/event
        self.interview_style = interview_style
        self.job_role = job_role
        self.job_description = job_description
        self.resume_content = resume_content
        self.difficulty_level = difficulty_level
        self.question_count = question_count
        self.company_name = company_name
        
        self.current_state = InterviewState.INITIALIZING
        self.initial_questions: List[str] = []
        self.asked_question_count = 0
        self.current_question: Optional[str] = None
        self.areas_covered: List[str] = []
        self.interview_session_id = None # Set by event handler
        
        # Setup LLM chains using self.llm from llm_service
        self._setup_llm_chains()
        
        # Subscribe to relevant events using EventType
        # NOTE: Subscription moved here for clarity, ensure _setup_llm_chains is called first if needed
        # It's safe here as _setup_llm_chains only uses self.llm which is set in super().__init__
        self.subscribe(EventType.SESSION_START, self._handle_session_start) # Changed from interview_start
        self.subscribe(EventType.SESSION_END, self._handle_session_end) # Changed from interview_end
        self.subscribe(EventType.SESSION_RESET, self._handle_session_reset) # Added for state reset
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the interviewer agent.
        
        Returns:
            System prompt string
        """
        # Ensure required fields have fallbacks if somehow empty
        job_role = self.job_role or "[Job Role Not Specified]"
        interview_style = self.interview_style.value if self.interview_style else InterviewStyle.FORMAL.value
        resume_content = self.resume_content or "[Resume Not Provided]"
        job_description = self.job_description or "[Job Description Not Provided]"
        
        return INTERVIEWER_SYSTEM_PROMPT.format(
            job_role=job_role,
            interview_style=interview_style,
            resume_content=resume_content,
            job_description=job_description,
            target_question_count=self.question_count
        )
    
    def _setup_llm_chains(self) -> None:
        """Set up LangChain chains using self.llm."""
        # Chain for generating the initial list of job-specific questions
        self.job_specific_question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(JOB_SPECIFIC_TEMPLATE),
            # output_key="questions_json" # Handled by invoke_chain_with_error_handling
        )
        
        # Chain for deciding the next action and generating the question dynamically
        self.next_action_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(NEXT_ACTION_TEMPLATE),
            # output_key="action_json"
        )
        
        # Chain for formatting responses based on style
        self.response_formatter_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(RESPONSE_FORMAT_TEMPLATE),
            # output_key="formatted_text"
        )
    
    def _generate_questions(self) -> None:
        """Generate the initial list of interview questions."""
        self.logger.info("Generating initial interview questions...")
        self.initial_questions = []
        self.initial_questions.append("To start, could you please tell me a bit about yourself and your background?")
        num_specific_to_generate = self.question_count - len(self.initial_questions)
        if self.job_role and self.job_description and self.resume_content and num_specific_to_generate > 0:
            try:
                specific_questions = self._generate_job_specific_questions(num_specific_to_generate)
                for q in specific_questions:
                    if q not in self.initial_questions:
                        self.initial_questions.append(q)
            except Exception as e:
                self.logger.error(f"Error generating job-specific questions: {e}. Falling back to generic.")
        num_generic_needed = self.question_count - len(self.initial_questions)
        if num_generic_needed > 0:
            generic_questions = self._generate_generic_questions()
            for q in generic_questions:
                if len(self.initial_questions) >= self.question_count:
                    break
                if q not in self.initial_questions:
                    self.initial_questions.append(q)
        self.initial_questions = self.initial_questions[:self.question_count]
        self.logger.info(f"Generated {len(self.initial_questions)} initial questions.")
    
    def _generate_generic_questions(self) -> List[str]:
        """Generate generic questions (non-LLM based)."""
        generic_questions = []
        # Define question templates for different interview styles
        question_templates = {
            InterviewStyle.FORMAL: [
                "Can you describe your experience with {technology}?",
                "How would you approach a situation where {scenario}?",
                "What methodology would you use to solve {problem_type} problems?",
                "Describe a time when you had to {challenge}. How did you handle it?",
                "How do you ensure {quality_aspect} in your work?",
            ],
            InterviewStyle.CASUAL: [
                "Tell me about a time you worked with {technology}. How did it go?",
                "What would you do if {scenario}?",
                "How do you typically tackle {problem_type} problems?",
                "Have you ever had to {challenge}? What happened?",
                "How do you make sure your work is {quality_aspect}?",
            ],
            InterviewStyle.AGGRESSIVE: [
                "Prove to me you have experience with {technology}.",
                "What exactly would you do if {scenario}? Be specific.",
                "I need to know exactly how you would solve {problem_type} problems. Details.",
                "Give me a specific example of when you {challenge}. What exactly did you do?",
                "How specifically do you ensure {quality_aspect}? Don't give me generalities.",
            ],
            InterviewStyle.TECHNICAL: [
                "Explain the key concepts of {technology} and how you've implemented them.",
                "What is your approach to {scenario} from a technical perspective?",
                "Walk me through your process for solving {problem_type} problems, including any algorithms or data structures you would use.",
                "Describe a technical challenge where you had to {challenge}. What was your solution?",
                "What metrics and tools do you use to ensure {quality_aspect} in your technical work?",
            ]
        }
        # Define template variables based on job role (simplified example)
        template_vars = {
            "Software Engineer": {
                "technology": ["React", "Python", "cloud infrastructure", "REST APIs", "microservices"],
                "scenario": ["production system failure", "changing requirements", "performance optimization"],
                "problem_type": ["algorithmic", "debugging", "system design"],
                "challenge": ["lead a project", "mentor juniors", "meet tight deadlines"],
                "quality_aspect": ["code quality", "test coverage", "reliability"]
            },
            "Data Scientist": {
                "technology": ["Python for data analysis", "machine learning frameworks", "data visualization"],
                "scenario": ["incomplete data", "explaining results", "poor model performance"],
                "problem_type": ["prediction", "classification", "clustering"],
                "challenge": ["clean messy data", "deploy a model", "interpret complex results"],
                "quality_aspect": ["model accuracy", "reproducibility", "interpretability"]
            },
            # Add more roles as needed
        }
        role_vars = template_vars.get(self.job_role, template_vars["Software Engineer"]) # Default to SWE
        style_templates = question_templates.get(self.interview_style, question_templates[InterviewStyle.FORMAL])
        
        possible_questions = []
        for template in style_templates:
            temp_vars = role_vars.copy()
            q = template
            placeholders = [p.strip("{}") for p in template.split() if p.startswith("{" ) and p.endswith("}")]
            try:
                format_args = {p: random.choice(temp_vars[p]) for p in placeholders if p in temp_vars}
                q = template.format(**format_args)
                possible_questions.append(q)
            except KeyError as e:
                 self.logger.warning(f"Missing key {e} for template: {template}")
        
        # Add some general questions independent of role/style
        general_questions = [
            "What attracted you to this position?",
            "Where do you see yourself professionally in five years?",
            f"Why do you think you're a good fit for this {self.job_role or 'role'}?",
            "Describe your ideal work environment.",
            "How do you stay updated with the latest developments in your field?"
        ]
        possible_questions.extend(general_questions)
        random.shuffle(possible_questions)
        return possible_questions
    
    def _generate_job_specific_questions(self, num_questions: int) -> List[str]:
        """Generate job-specific questions using LLM."""
        self.logger.info(f"Generating {num_questions} job-specific questions...")
        inputs = {
            "job_role": self.job_role or "[Not Specified]",
            "job_description": self.job_description or "[Not Provided]",
            "resume_content": self.resume_content or "[Not Provided]",
            "num_questions": num_questions,
            "difficulty_level": self.difficulty_level,
            "interview_style": self.interview_style.value
        }

        response = invoke_chain_with_error_handling(
            self.job_specific_question_chain,
            inputs,
            self.logger,
            "Job Specific Question Chain",
            output_key="questions_json" # Expecting a JSON list string
        )
        
        # The utility now handles parsing
        if isinstance(response, list):
            self.logger.info(f"Successfully generated {len(response)} specific questions.")
            return [str(q) for q in response if isinstance(q, str) and q.strip()]
        else:
            self.logger.error(f"Job specific question chain did not return a list. Got: {type(response)}")
            return []
    
    def _create_introduction(self) -> str:
        """Create an introduction for the interview."""
        style_key = self.interview_style.value.lower()
        template = INTRODUCTION_TEMPLATES.get(style_key, INTRODUCTION_TEMPLATES["formal"])
        
        # Calculate approximate duration based on question count (e.g., 3 mins per question)
        approx_duration = f"around {self.question_count * 3} minutes"
        
        return template.format(
            job_role=self.job_role or "the position",
            interview_duration=approx_duration,
            company_name=self.company_name or "our company"
        )
    
    def _format_response_by_style(self, content: str, content_type: str) -> str:
        """Format a response based on style using LLM."""
        self.logger.debug(f"Formatting content (type: {content_type}) for style: {self.interview_style.value}")
        inputs = {
            "style": self.interview_style.value,
            "job_role": self.job_role or "[Not Specified]",
            "content": content,
            "content_type": content_type
        }
        response = invoke_chain_with_error_handling(
            self.response_formatter_chain,
            inputs,
            self.logger,
            "Response Formatter Chain",
            output_key="formatted_text" # Expecting formatted text string
        )
        return response if isinstance(response, str) else content
    
    def _handle_session_start(self, event: Event) -> None:
        """
        Handle session start events.
        Resets state and updates configuration.
        """
        self.logger.info(f"Handling session_start event: {event.data}")
        # Reset state
        self.current_state = InterviewState.INITIALIZING
        self.asked_question_count = 0
        self.initial_questions = []
        self.current_question = None
        self.areas_covered = []
        
        # Update interview parameters if provided
        data = event.data
        self.job_role = data.get("job_role", self.job_role)
        self.job_description = data.get("job_description", self.job_description)
        self.resume_content = data.get("resume_content", self.resume_content)
        self.company_name = data.get("company_name", self.company_name)
        self.question_count = int(data.get("question_count", self.question_count))
        self.difficulty_level = data.get("difficulty_level", self.difficulty_level)
        
        try:
            style_value = data.get("interview_style", self.interview_style.value)
            self.interview_style = InterviewStyle(style_value)
        except ValueError:
             self.logger.warning(f"Invalid interview style '{style_value}' received. Defaulting to {self.interview_style.value}.")
        
        # Store session ID if provided
        self.interview_session_id = data.get("session_id", str(uuid.uuid4())) # Generate one if missing
        self.logger.info(f"Interview configuration updated for session {self.interview_session_id}")
    
    def _handle_session_end(self, event: Event) -> None:
        """
        Handle session end events (e.g., user manually stops).
        """
        self.logger.info(f"Handling session_end event for session {self.interview_session_id}.")
        self.current_state = InterviewState.COMPLETED
        # Optionally, clear sensitive data like resume content here if needed
        # self.resume_content = ""
    
    def _handle_session_reset(self, event: Event) -> None:
        """
        Handle session reset events.
        """
        self.logger.info(f"Handling session_reset event for session {self.interview_session_id}.")
        self.current_state = InterviewState.INITIALIZING
        self.asked_question_count = 0
        self.initial_questions = []
        self.current_question = None
        self.areas_covered = []
    
    def _reset_state(self):
        # ... (Implementation updated in previous step) ...
        pass

    def _determine_and_generate_next_action(self, context: AgentContext) -> Dict[str, Any]:
        """Uses LLM to decide the next step and generate content."""
        self.logger.debug("Determining next action...")
        last_user_message = context.get_last_user_message() or "[No answer yet]"
        history_str = format_conversation_history(context.conversation_history[:-1])
        
        inputs = {
            "job_role": self.job_role or "[Not Specified]",
            "job_description": self.job_description or "[Not Provided]",
            "resume_content": self.resume_content or "[Not Provided]",
            "interview_style": self.interview_style.value,
            "target_question_count": self.question_count,
            "questions_asked_count": self.asked_question_count,
            "areas_covered_so_far": ", ".join(self.areas_covered) or "None",
            "conversation_history": history_str,
            "previous_question": self.current_question or "[No previous question]",
            "candidate_answer": last_user_message
        }
        
        default_action = {
            "action_type": "end_interview",
            "next_question_text": None,
            "justification": "Defaulting to end interview due to processing error.",
            "newly_covered_topics": []
        }
        
        response = invoke_chain_with_error_handling(
            self.next_action_chain,
            inputs,
            self.logger,
            "Next Action Chain",
            output_key="action_json" # Expecting JSON string output
        )
        
        if isinstance(response, dict) and "action_type" in response:
            action_type = response.get("action_type")
            if not isinstance(action_type, str) or action_type not in ["ask_follow_up", "ask_new_question", "end_interview"]:
                self.logger.error(f"Invalid action_type received: {action_type}")
                return default_action
            if not isinstance(response.get("newly_covered_topics"), list):
                 response["newly_covered_topics"] = []
            self.logger.info(f"Next action determined: {action_type}, Justification: {response.get('justification')}")
            return response
        else:
            self.logger.error(f"Next action chain did not return a valid action dictionary. Got: {response}")
            return default_action

    def _do_action(self, context: AgentContext) -> Dict[str, Any]:
        """Performs the next action based on the current state."""
        response_type = "error" # Default to error
        response_text = "An internal error occurred." # Default message
        metadata = {} # Optional metadata to return
        
        try:
            if self.current_state == InterviewState.INITIALIZING:
                self.logger.info("State: INITIALIZING -> Generating initial questions.")
                self._generate_questions() # Generate initial pool
                if not self.initial_questions:
                     self.logger.error("Failed to generate any initial questions! Ending interview prematurely.")
                     self.current_state = InterviewState.COMPLETED
                     response_text = "I seem to be having trouble formulating questions right now. We'll have to stop here. My apologies."
                     response_type = "closing"
                else:
                     self.current_state = InterviewState.INTRODUCING
                     self.logger.info("State transition: INITIALIZING -> INTRODUCING")
                     # Fall through to INTRODUCING state in the same turn
                # Re-evaluate state for fall-through
                if self.current_state != InterviewState.INTRODUCING:
                     # If already completed due to error above, return immediately
                     return {"response_type": response_type, "text": response_text, "metadata": metadata}
            
            # Note: Use 'if' instead of 'elif' for INTRODUCING to allow fall-through from INITIALIZING
            if self.current_state == InterviewState.INTRODUCING:
                self.logger.info("State: INTRODUCING -> Creating introduction and asking first question.")
                intro_text = self._create_introduction()
                formatted_intro = self._format_response_by_style(intro_text, "introduction")
                
                first_question = self.initial_questions.pop(0) # Get and remove first question
                formatted_question = self._format_response_by_style(first_question, "question")
                self.current_question = first_question # Set current question
                self.asked_question_count = 1
                
                response_text = f"{formatted_intro}\\n\\n{formatted_question}"
                self.current_state = InterviewState.QUESTIONING
                response_type = "question"
                metadata["question_number"] = self.asked_question_count
                self.logger.info(f"State transition: INTRODUCING -> QUESTIONING. Asked initial question 1.")
                # Publish the question asked
                self.publish_event(EventType.INTERVIEWER_QUESTION, {"question": self.current_question, "question_number": 1}) 
            
            elif self.current_state == InterviewState.QUESTIONING:
                # Check if target reached *before* determining next action
                if self.asked_question_count >= self.question_count:
                     self.logger.info(f"Target question count ({self.question_count}) reached. Ending interview.")
                     action_data = {"action_type": "end_interview"} # Force end
                else:
                     self.logger.info(f"State: QUESTIONING -> Determining next action (Question {self.asked_question_count + 1}).")
                     action_data = self._determine_and_generate_next_action(context)
                
                # Update covered topics from LLM analysis
                new_topics = action_data.get("newly_covered_topics", [])
                if new_topics:
                    updated = False
                    for topic in new_topics:
                        # Basic validation for topic
                        if isinstance(topic, str) and topic.strip() and topic not in self.areas_covered:
                            self.areas_covered.append(topic.strip())
                            updated = True
                    if updated:
                        self.logger.debug(f"Updated areas covered: {self.areas_covered}")
                
                action_type = action_data.get("action_type")
                
                if action_type in ["ask_follow_up", "ask_new_question"]:
                    next_question = action_data.get("next_question_text")
                    if next_question and isinstance(next_question, str) and next_question.strip():
                        formatted_question = self._format_response_by_style(next_question, "question")
                        self.current_question = next_question.strip() # Update current question
                        self.asked_question_count += 1
                        response_text = formatted_question
                        response_type = "question"
                        metadata["question_number"] = self.asked_question_count
                        self.logger.info(f"Asking question {self.asked_question_count}: {self.current_question[:100]}...")
                        # Publish the question asked
                        self.publish_event(EventType.INTERVIEWER_QUESTION, {"question": self.current_question, "question_number": self.asked_question_count})
                        # State remains QUESTIONING
                    else:
                        self.logger.error(f"Action type was {action_type} but no valid question text provided ('{next_question}'). Ending interview.")
                        action_type = "end_interview" # Force end if no question
                
                # Handle end_interview action (either decided by LLM or forced)
                # Use 'if' because action_type might have been changed above
                if action_type == "end_interview":
                    self.logger.info("State: QUESTIONING -> Ending interview.")
                    self.current_state = InterviewState.COMPLETED
                    # Use justification from LLM if available, else default
                    closing_remark = action_data.get("justification") or "Okay, that covers the main questions I had. Thank you for taking the time to speak with me today."
                    # Ensure closing remark is a non-empty string
                    if not isinstance(closing_remark, str) or not closing_remark.strip():
                         closing_remark = "Thank you for your time today."
                    response_text = self._format_response_by_style(closing_remark, "closing")
                    response_type = "closing"
                    self.logger.info(f"State transition: QUESTIONING -> COMPLETED")
            
            elif self.current_state == InterviewState.COMPLETED:
                 self.logger.info("State: COMPLETED - Interview already finished.")
                 response_text = "The interview has already concluded. Thank you." # Provide info
                 response_type = "info"
            
        except Exception as e:
            self.logger.exception(f"Unhandled exception in _do_action: {e}")
            self.current_state = InterviewState.COMPLETED # Prevent loops
            response_type = "error"
            response_text = "I apologize, but I encountered an unexpected error and need to end the interview. Thank you for your time."
        
        return {
            "response_type": response_type,
            "text": response_text,
            "metadata": metadata
        }

    def process(self, context: AgentContext) -> Dict[str, Any]: # Renamed from invoke, takes context
        """
        Main entry point for the Interviewer agent, called by SessionManager.
        Processes the current context and determines the next action/response.
        
        Args:
            context: The AgentContext provided by the SessionManager.
            
        Returns:
            Dictionary containing the agent's response content, type, and optional metadata.
        """
        # Basic check for context validity
        if not context:
            self.logger.error("Interviewer process called with invalid context. Cannot proceed.")
            return { "content": "Internal context error.", "response_type": "error", "metadata": {}}
            
        # Ensure session ID matches if it's already set (can be set by _handle_session_start)
        if self.interview_session_id and context.session_id != self.interview_session_id:
            self.logger.error(f"Context session ID mismatch! Agent expected {self.interview_session_id}, got {context.session_id}. Cannot proceed.")
            return { "content": "Internal context error.", "response_type": "error", "metadata": {}}
        elif not self.interview_session_id:
             # If agent session ID wasn't set by event yet, adopt it from context
             self.interview_session_id = context.session_id
             self.logger.info(f"Interviewer adopting session ID {self.interview_session_id} from context.")
            
        self.logger.info(f"Interviewer process called in state {self.current_state.value} for session {context.session_id}")
        
        # Execute state-based action using the provided context
        action_result = self._do_action(context)
        
        # Publish event if interview completed during this action
        # Use a flag to prevent publishing multiple times if process is called again in COMPLETED state
        completed_now = (self.current_state == InterviewState.COMPLETED and action_result.get("response_type") != "info")
        if completed_now and not getattr(self, '_completed_event_published', False):
             self.logger.info("Publishing interview_completed event.")
             self.publish_event(EventType.INTERVIEW_COMPLETED, { # Use enum
                 "session_id": context.session_id,
                 "timestamp": datetime.utcnow().isoformat(),
                 "total_questions_asked": self.asked_question_count,
                 "areas_covered": self.areas_covered
             })
             self._completed_event_published = True # Set flag
        elif self.current_state != InterviewState.COMPLETED:
             self._completed_event_published = False # Reset flag if not completed
        
        response_content = action_result.get("text", "")
        response_type = action_result.get("response_type", "error")
        response_metadata = action_result.get("metadata", {})
        
        self.logger.info(f"Interviewer process returning: Type={response_type}, Text='{response_content[:100]}...' Metadata={response_metadata}")
        
        # Return structure expected by SessionManager
        return {
            "content": response_content,
            "response_type": response_type,
            "metadata": response_metadata
            # TODO: Add token usage here if available from LLM response in _do_action
        } 