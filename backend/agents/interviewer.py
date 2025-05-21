"""
Interviewer agent responsible for conducting interview sessions.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import random
import uuid 
from enum import Enum
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


try:
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import Event, EventBus, EventType
    from backend.services.llm_service import LLMService
    from backend.agents.config_models import InterviewStyle
    from backend.agents.templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES,
        RESPONSE_FORMAT_TEMPLATE
    )
    from backend.utils.llm_utils import (
        invoke_chain_with_error_handling,
        format_conversation_history,
        parse_json_with_fallback
    )
except ImportError:
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import Event, EventBus
    from ..agents.config_models import InterviewStyle
    from .templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES,
        RESPONSE_FORMAT_TEMPLATE
    )
    from ..utils.llm_utils import (
        invoke_chain_with_error_handling,
        format_conversation_history,
        parse_json_with_fallback
    )

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
        
        self._setup_llm_chains()
        

        self.subscribe(EventType.SESSION_START, self._handle_session_start)
        self.subscribe(EventType.SESSION_END, self._handle_session_end) 
        self.subscribe(EventType.SESSION_RESET, self._handle_session_reset)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the interviewer agent.
        
        Returns:
            System prompt string
        """
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
        self.job_specific_question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(JOB_SPECIFIC_TEMPLATE),
        )
        
        self.next_action_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(NEXT_ACTION_TEMPLATE),
        )
        
        self.response_formatter_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(RESPONSE_FORMAT_TEMPLATE),
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
        config = data.get("config", {})
        
        if isinstance(config, dict):
            self.job_role = config.get("job_role", self.job_role)
            self.job_description = config.get("job_description", self.job_description)
            self.resume_content = config.get("resume_content", self.resume_content)
            self.company_name = config.get("company_name", self.company_name)
            self.question_count = int(config.get("target_question_count", self.question_count))
            self.difficulty_level = config.get("difficulty", self.difficulty_level)
            
            try:
                style_value = config.get("style", self.interview_style.value)
                self.interview_style = InterviewStyle(style_value)
            except ValueError:
                 self.logger.warning(f"Invalid interview style '{style_value}' received. Defaulting to {self.interview_style.value}.")
        else:
            self.logger.warning(f"Received invalid config data: {config}")
        
        self.logger.info(f"Interview configuration updated via SESSION_START event.")
        
        # Generate initial questions
        self._generate_questions()
        self.logger.info(f"Generated {len(self.initial_questions)} initial questions during session start.")
    
    def _handle_session_end(self, event: Event) -> None:
        """
        Handle session end events (e.g., user manually stops).
        """
        self.logger.info(f"Handling session_end event.")
        self.current_state = InterviewState.COMPLETED
        # Optionally, clear sensitive data like resume content here if needed
        # self.resume_content = ""
    
    def _handle_session_reset(self, event: Event) -> None:
        """
        Handle session reset events.
        """
        self.logger.info(f"Handling session_reset event.")
        self.current_state = InterviewState.INITIALIZING
        self.asked_question_count = 0
        self.initial_questions = []
        self.current_question = None
        self.areas_covered = []


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
            "action_type": "ask_new_question",
            "next_question_text": "Can you tell me about your professional background and experience?",
            "justification": "Defaulting to a general question due to processing error.",
            "newly_covered_topics": []
        }
        
        response = invoke_chain_with_error_handling(
            self.next_action_chain,
            inputs,
            self.logger,
            "Next Action Chain",
            output_key="action_json" # Expecting JSON string output
        )
        
        # Handle case where the response is in the 'text' field instead of 'action_json'
        if response is None and isinstance(self.next_action_chain.invoke(inputs), dict):
            raw_response = self.next_action_chain.invoke(inputs)
            self.logger.debug(f"Raw response from next_action_chain: {raw_response}")
            
            # Check if there's a text field containing JSON
            if 'text' in raw_response and isinstance(raw_response['text'], str):
                parsed_json = parse_json_with_fallback(raw_response['text'], None, self.logger)
                if parsed_json is not None:
                    self.logger.info(f"Successfully parsed JSON from 'text' field")
                    response = parsed_json
        
        if isinstance(response, dict) and "action_type" in response:
            action_type = response.get("action_type")
            if not isinstance(action_type, str) or action_type not in ["ask_follow_up", "ask_new_question", "end_interview"]:
                self.logger.error(f"Invalid action_type received: {action_type}")
                return default_action
            if action_type == "end_interview" and self.asked_question_count < 3:
                self.logger.warning(f"Attempting to end interview after only {self.asked_question_count} questions. Overriding.")
                response["action_type"] = "ask_new_question"
                response["next_question_text"] = default_action["next_question_text"]
                response["justification"] = "Continuing interview to meet minimum question count."
            if not isinstance(response.get("newly_covered_topics"), list):
                 response["newly_covered_topics"] = []
            self.logger.info(f"Next action determined: {response.get('action_type')}, Justification: {response.get('justification')}")
            return response
        else:
            self.logger.error(f"Next action chain did not return a valid action dictionary. Got: {response}")
            return default_action

    def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Processes the current context to determine the next step in the interview.
        Uses the ReAct-style chain to decide the action and generate the response.
        
        Args:
            context: The current AgentContext.
            
        Returns:
            A dictionary representing the agent's response.
        """
        self.logger.info(f"Interviewer processing state: {self.current_state}")

        response_data = {
            "role": "assistant",
            "agent": "interviewer",
            "content": "",
            "response_type": "status",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {}
        }

        if self.current_state == InterviewState.INITIALIZING:
            self._handle_session_start(Event(
                event_type=EventType.SESSION_START,
                source=self.__class__.__name__,
                data={"config": context.session_config.dict()}
            ))
            # Transition state after handling start
            if self.initial_questions:
                self.current_state = InterviewState.INTRODUCING
            else:
                self.logger.error("Initialization failed, no questions generated.")
                response_data["content"] = "Sorry, I encountered an error setting up the interview questions."
                response_data["response_type"] = "error"
                self.current_state = InterviewState.COMPLETED
                return response_data

        if self.current_state == InterviewState.INTRODUCING:
            intro_text = self._create_introduction()
            response_data["content"] = intro_text
            response_data["response_type"] = "introduction"
            self.current_state = InterviewState.QUESTIONING
            self.logger.info("Interview introduction generated.")
            # Publish event? Maybe not needed here as it's just an intro.
            return response_data
        
        elif self.current_state == InterviewState.QUESTIONING:
            # Use the ReAct chain to determine the next action and question
            action_result = self._determine_and_generate_next_action(context)
            
            action_type = action_result.get("action_type")
            next_question = action_result.get("next_question_text")
            new_topics = action_result.get("newly_covered_topics", [])

            if new_topics:
                self.areas_covered.extend(topic for topic in new_topics if topic not in self.areas_covered)
            
            if action_type == "end_interview":
                self.current_state = InterviewState.COMPLETED
                response_data["content"] = "Thank you for your time. This concludes the interview."
                response_data["response_type"] = "closing"
                self.logger.info("Interview concluded based on ReAct decision.")
            elif next_question:
                self.current_question = next_question
                self.asked_question_count += 1
                response_data["content"] = self.current_question
                response_data["response_type"] = "question"
                response_data["metadata"] = {
                    "question_number": self.asked_question_count,
                    "justification": action_result.get("justification")
                }
                self.logger.info(f"Generated question #{self.asked_question_count} via ReAct: {self.current_question[:100]}...")
            else:
                # Handle error case where action requires a question but none was generated
                self.logger.error("ReAct chain decided to ask a question but did not provide text.")
                self.current_state = InterviewState.COMPLETED
                response_data["content"] = "It seems we've reached a natural stopping point. Thank you for your time."
                response_data["response_type"] = "closing"

        elif self.current_state == InterviewState.COMPLETED:
            response_data["content"] = "The interview has already concluded."
            response_data["response_type"] = "status"

        return response_data 