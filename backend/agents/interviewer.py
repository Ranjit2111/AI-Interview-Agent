"""
Interviewer agent responsible for conducting interview sessions.
This agent asks questions, evaluates answers, and provides feedback.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import random
from enum import Enum
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_core.output_parsers import StrOutputParser

try:
    # Try standard import in production
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import Event, EventBus
    from backend.models.interview import InterviewStyle, InterviewSession, Question, Answer
    from backend.agents.templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        QUESTION_TEMPLATE,
        EVALUATION_TEMPLATE, 
        SUMMARY_TEMPLATE,
        QUALITY_ASSESSMENT_TEMPLATE,
        FOLLOW_UP_TEMPLATE,
        THINK_TEMPLATE,
        REASON_TEMPLATE,
        PLANNING_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES,
        ANSWER_EVALUATION_TEMPLATE,
        RESPONSE_FORMAT_TEMPLATE
    )
    from backend.agents.utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        extract_field_safely,
        format_conversation_history
    )
except ImportError:
    # Use relative imports for development/testing
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import Event, EventBus
    from ..models.interview import InterviewStyle, InterviewSession, Question, Answer
    from .templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        QUESTION_TEMPLATE,
        EVALUATION_TEMPLATE,
        SUMMARY_TEMPLATE,
        QUALITY_ASSESSMENT_TEMPLATE,
        FOLLOW_UP_TEMPLATE,
        THINK_TEMPLATE,
        REASON_TEMPLATE,
        PLANNING_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES,
        ANSWER_EVALUATION_TEMPLATE,
        RESPONSE_FORMAT_TEMPLATE
    )
    from .utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        extract_field_safely,
        format_conversation_history
    )


class InterviewState(Enum):
    """Enum representing the possible states of an interview."""
    INITIALIZING = "initializing"
    INTRODUCING = "introducing"
    QUESTIONING = "questioning"
    EVALUATING = "evaluating"
    TRANSITIONING = "transitioning"
    SUMMARIZING = "summarizing"
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
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        planning_interval: int = 5,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        interview_style: InterviewStyle = InterviewStyle.FORMAL,
        job_role: str = "",
        job_description: str = "",
        difficulty_level: str = "medium",
        question_count: int = 10
    ):
        """
        Initialize the interviewer agent.
        
        Args:
            api_key: API key for the language model
            model_name: Name of the language model to use
            planning_interval: Number of interactions before planning
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            interview_style: Style of interview to conduct
            job_role: Target job role for the interview
            job_description: Description of the job
            difficulty_level: Difficulty level of questions (easy, medium, hard)
            question_count: Target number of questions to ask
        """
        super().__init__(api_key, model_name, planning_interval, event_bus, logger)
        
        self.interview_style = interview_style
        self.job_role = job_role
        self.job_description = job_description
        self.difficulty_level = difficulty_level
        self.question_count = question_count
        self.current_state = InterviewState.INITIALIZING
        self.questions = []
        self.current_question_index = 0
        self.interview_session_id = None
        
        # Setup LLM chains
        self._setup_llm_chains()
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe("user_response", self._handle_user_response)
            self.event_bus.subscribe("interview_start", self._handle_interview_start)
            self.event_bus.subscribe("interview_end", self._handle_interview_end)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the interviewer agent.
        
        Returns:
            System prompt string
        """
        return INTERVIEWER_SYSTEM_PROMPT.format(
            job_role=self.job_role,
            interview_style=self.interview_style.value
        )
    
    def _initialize_tools(self) -> List[Tool]:
        """
        Initialize tools for the interviewer agent.
        
        Returns:
            List of LangChain tools
        """
        return [
            Tool(
                name="generate_question",
                func=self._generate_next_question_tool,
                description="Generate the next interview question based on job role and previous answers"
            ),
            Tool(
                name="evaluate_answer",
                func=self._process_answer,
                description="Evaluate a candidate's answer to a question"
            ),
            Tool(
                name="summarize_interview",
                func=self._create_summary,
                description="Generate a summary of the interview with feedback and recommendations"
            )
        ]
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Question generation chain with improved prompting for different question types
        self.question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(QUESTION_TEMPLATE),
            output_key="question"
        )
        
        # Answer evaluation chain with improved structure
        self.evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(EVALUATION_TEMPLATE),
            output_key="feedback"
        )
        
        # Interview summary chain
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(SUMMARY_TEMPLATE),
            output_key="summary"
        )
        
        # Add new chain for answer quality assessment
        self.quality_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(QUALITY_ASSESSMENT_TEMPLATE),
            output_parser=StrOutputParser(),
            output_key="quality_assessment"
        )
        
        # Add new chain for follow-up question generation
        self.follow_up_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(FOLLOW_UP_TEMPLATE),
            output_key="follow_up_question"
        )
    
    def _generate_next_question_tool(self, args: Optional[Dict[str, Any]] = None) -> str:
        """
        Tool function to generate the next interview question.
        
        Args:
            args: Optional arguments for the tool
            
        Returns:
            The generated question
        """
        previous_questions = "\n".join([f"- {q}" for q in self.questions])
        
        response = self.question_chain.invoke({
            "job_role": self.job_role,
            "job_description": self.job_description,
            "interview_style": self.interview_style.value,
            "previous_questions": previous_questions or "No questions asked yet.",
            "difficulty_level": self.difficulty_level
        })
        
        return response["question"]
    
    def process_input(self, input_text: str, context: Optional[AgentContext] = None) -> str:
        """
        Process user input and generate a response.
        
        Args:
            input_text: The user input text
            context: Optional context (uses self.current_context if not provided)
            
        Returns:
            The agent's response
        """
        if not context:
            if not self.current_context:
                self.create_context()
            context = self.current_context
        
        # Add user message to context
        context.add_message("user", input_text)
        
        # Run planning step if needed
        if self._should_plan():
            planning_result = self._run_planning_step(context)
            self.logger.debug(f"Planning result: {planning_result}")
        
        # Apply ReAct process - Think, Reason, Act
        think_step = self._think_about_input(input_text, context)
        self.logger.debug(f"Think step: {think_step}")
        
        reason_step = self._reason_about_next_action(think_step, context)
        self.logger.debug(f"Reason step: {reason_step}")
        
        # Increment step count
        self.step_count += 1
        
        # Handle based on current state
        if self.current_state == InterviewState.INITIALIZING:
            response = self._handle_initialization(context)
        elif self.current_state == InterviewState.INTRODUCING:
            response = self._handle_introduction(context)
        elif self.current_state == InterviewState.QUESTIONING:
            response = self._handle_questioning(input_text, context)
        elif self.current_state == InterviewState.EVALUATING:
            response = self._handle_evaluation(input_text, context)
        elif self.current_state == InterviewState.TRANSITIONING:
            response = self._handle_transition(context)
        elif self.current_state == InterviewState.SUMMARIZING:
            response = self._handle_summarizing(input_text, context)
        else:
            response = "I'm sorry, there was an issue with the interview state. Let's restart."
            self.current_state = InterviewState.INITIALIZING
        
        # Add assistant message to context
        context.add_message("assistant", response)
        
        # Return response
        return response
    
    def _think_about_input(self, input_text: str, context: AgentContext) -> Dict[str, Any]:
        """
        Analyze the user input to understand its content (Think step of ReAct).
        
        Args:
            input_text: The user's input text
            context: The agent context
            
        Returns:
            Dictionary with analysis results
        """
        # Get conversation history
        history = format_conversation_history(context.conversation_history)
        
        # Current question (if any)
        current_question = self.questions[self.current_question_index].text if self.current_question_index < len(self.questions) else ""
        
        # Create inputs for the prompt
        inputs = {
            "job_role": self.job_role,
            "current_state": context.get_state(),
            "current_question": current_question,
            "history": history
        }
        
        try:
            # Call LLM to analyze input using the THINK_TEMPLATE
            analysis_text = self._call_llm(THINK_TEMPLATE.format(**inputs), context)
            
            # Parse analysis as JSON with fallback
            default_analysis = {
                "input_analysis": "Unable to analyze input",
                "key_topics": [],
                "sentiment": "neutral",
                "relevance": "medium"
            }
            
            return parse_json_with_fallback(analysis_text, default_analysis, self.logger)
            
        except Exception as e:
            self.logger.error(f"Error in think step: {e}")
            return {
                "input_analysis": "Error analyzing input",
                "key_topics": [],
                "sentiment": "unknown",
                "relevance": "unknown"
            }
    
    def _reason_about_next_action(self, think_result: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """
        Determine the next action based on analysis (Reason step of ReAct).
        
        Args:
            think_result: The result of the think step
            context: The agent context
            
        Returns:
            Dictionary with reasoning results
        """
        # Create inputs for the template
        inputs = {
            "job_role": self.job_role,
            "current_state": context.get_state(),
            "think_result": think_result,
            "json": json  # Pass json module to template for json.dumps
        }
        
        try:
            # Call LLM to reason about next action
            reasoning_text = self._call_llm(REASON_TEMPLATE.format(**inputs), context)
            
            # Parse reasoning as JSON with fallback
            default_reasoning = {
                "next_action": "ask_question",
                "justification": "Continuing with interview questions",
                "suggested_state": context.get_state(),
                "follow_up_needed": False,
                "suggested_question_type": "general"
            }
            
            reasoning = parse_json_with_fallback(reasoning_text, default_reasoning, self.logger)
            
            # Validate suggested state if present
            if "suggested_state" in reasoning:
                suggested_state = reasoning["suggested_state"]
                try:
                    # Try to convert to InterviewState enum
                    if not any(suggested_state == state.value for state in InterviewState):
                        reasoning["suggested_state"] = context.get_state()
                        self.logger.error(f"Invalid interview state suggested: {suggested_state}")
                except:
                    reasoning["suggested_state"] = context.get_state()
            
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Error in reason step: {e}")
            return {
                "next_action": "ask_question",
                "justification": "Error in reasoning process",
                "suggested_state": context.get_state(),
                "follow_up_needed": False
            }
    
    def _run_planning_step(self, context: AgentContext) -> Dict[str, Any]:
        """
        Run a planning step to adjust the interview strategy.
        
        Args:
            context: The agent context
            
        Returns:
            Dictionary with planning results
        """
        # Calculate progress percentage
        if self.question_count > 0:
            progress_percentage = min(int((self.current_question_index / self.question_count) * 100), 100)
        else:
            progress_percentage = 0
            
        # Get questions asked so far
        questions_asked = [q.text for q in self.questions[:self.current_question_index]]
        questions_summary = "\n".join([f"- {q}" for q in questions_asked]) if questions_asked else "None yet"
        
        # Create inputs for the template
        inputs = {
            "job_role": self.job_role,
            "current_state": context.get_state(),
            "progress": progress_percentage,
            "questions_asked": questions_summary,
            "difficulty_level": self.difficulty_level,
            "job_description": self.job_description
        }
        
        try:
            # Call LLM with the planning template
            planning_result_text = self._call_llm(PLANNING_TEMPLATE.format(**inputs), context)
            
            # Parse planning result as JSON with fallback
            default_planning = {
                "areas_to_cover": ["technical skills", "problem solving", "teamwork"],
                "suggested_difficulty": self.difficulty_level,
                "next_question_types": ["behavioral", "technical"],
                "should_transition": False,
                "transition_to": context.get_state(),
                "justification": "Continuing with current interview plan"
            }
            
            planning_result = parse_json_with_fallback(planning_result_text, default_planning, self.logger)
            
            # Update difficulty level if suggested
            if "suggested_difficulty" in planning_result:
                suggested_difficulty = planning_result["suggested_difficulty"]
                if suggested_difficulty in ["easy", "medium", "hard"]:
                    self.difficulty_level = suggested_difficulty
                    self.logger.info(f"Updated difficulty level to {suggested_difficulty}")
                    
            # Check if we should transition states
            if planning_result.get("should_transition", False):
                suggested_state = planning_result.get("transition_to", "")
                try:
                    # Try to convert to InterviewState enum
                    if any(suggested_state == state.value for state in InterviewState):
                        context.set_state(suggested_state)
                        self.logger.info(f"Transitioned to state: {suggested_state}")
                except:
                    self.logger.error(f"Invalid transition state suggested: {suggested_state}")
                    
            return planning_result
            
        except Exception as e:
            self.logger.error(f"Error in planning step: {e}")
            return {
                "areas_to_cover": ["technical skills", "soft skills"],
                "suggested_difficulty": self.difficulty_level,
                "next_question_types": ["behavioral", "technical"],
                "should_transition": False,
                "justification": "Error occurred during planning"
            }
    
    def _handle_initialization(self, context: AgentContext) -> str:
        """
        Initialize the interview session.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Welcome message for the user
        """
        # Create a new interview session if needed
        if not self.interview_session_id:
            self.interview_session_id = context.session_id
        
        # Generate interview questions based on job role and description
        self._generate_questions()
        
        # Transition to introduction state
        self.current_state = InterviewState.INTRODUCING
        
        return self._create_introduction()
    
    def _handle_introduction(self, context: AgentContext) -> str:
        """
        Handle the introduction phase of the interview.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Introduction and first question
        """
        # Transition to questioning state
        self.current_state = InterviewState.QUESTIONING
        
        # Return the first question
        question = self._get_next_question()
        
        # Add metadata to identify this as a question
        context.conversation_history[-1]["metadata"]["is_question"] = True
        
        return question
    
    def _handle_questioning(self, input_text: str, context: AgentContext) -> str:
        """
        Handle the questioning state of the interview.
        
        Args:
            input_text: The candidate's input
            context: The agent context
            
        Returns:
            The agent's response
        """
        # Record answer to current question
        current_q_index = self.current_question_index - 1
        if current_q_index >= 0 and current_q_index < len(self.questions):
            current_question = self.questions[current_q_index]
            
            # Assess answer quality
            quality_assessment = self._assess_answer_quality(current_question, input_text)
            
            # Store answer quality in context metadata
            if "answer_quality" not in context.metadata:
                context.metadata["answer_quality"] = []
            
            context.metadata["answer_quality"].append({
                "question_index": current_q_index,
                "assessment": quality_assessment
            })
            
            # Determine if follow-up needed
            if quality_assessment.get("follow_up_needed", False) and quality_assessment.get("score", 5) < 4:
                follow_up = self._generate_follow_up_question(current_question, input_text)
                
                # Add follow-up to context
                context.add_message("assistant", follow_up)
                
                # Publish answer evaluation event
                self._publish_event("answer_evaluated", {
                    "question_index": current_q_index,
                    "question": current_question,
                    "answer": input_text,
                    "follow_up_question": follow_up,
                    "quality_score": quality_assessment.get("score", 3)
                })
                
                return follow_up
            
            # If answer quality is very poor, provide some guidance
            if quality_assessment.get("score", 3) <= 2:
                guidance = self._process_answer(input_text, context)
                next_question = self._get_next_question()
                response = f"{guidance}\n\nLet's move on to the next question.\n\n{next_question}"
        else:
            # First question or error recovery
            response = self._get_next_question()
        
        # If we've reached the end of questions, transition to summary
        if self.current_question_index >= len(self.questions) or self.current_question_index >= self.question_count:
            self.current_state = InterviewState.SUMMARIZING
            return self._handle_summarizing(input_text, context)
        
        # Add response to context
        context.add_message("assistant", response)
        
        return response
    
    def _handle_evaluation(self, input_text: str, context: AgentContext) -> str:
        """
        Evaluate the user's answer and provide feedback.
        
        Args:
            input_text: The user's answer
            context: The current context of the conversation
            
        Returns:
            Feedback on the user's answer
        """
        # This should typically not be called directly as evaluation happens in _handle_questioning
        # But including for completeness
        feedback = self._process_answer(input_text, context)
        self.current_state = InterviewState.TRANSITIONING
        return feedback
    
    def _handle_transition(self, context: AgentContext) -> str:
        """
        Handle the transition between questions.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Next question or transition to summary
        """
        # Transition to questioning state
        self.current_state = InterviewState.QUESTIONING
        
        # Get the next question
        question = self._get_next_question()
        
        # Add metadata to identify this as a question
        if context.conversation_history and context.conversation_history[-1]["role"] == "assistant":
            context.conversation_history[-1]["metadata"]["is_question"] = True
        
        return question
    
    def _handle_summarizing(self, input_text: str, context: AgentContext) -> Dict[str, Any]:
        """
        Handle the SUMMARIZING state to generate the interview summary.
        
        Args:
            input_text: The input text from the user
            context: The agent context
            
        Returns:
            The interview summary data
        """
        # Generate summary
        summary = self._create_summary(context)
        
        # Publish summary event
        self._publish_event("interview_summarized", {
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Transition to COMPLETED state
        self.current_state = InterviewState.COMPLETED
        return summary
    
    def _generate_questions(self) -> None:
        """
        Generate a list of interview questions based on job role and description.
        """
        # Use LLM to generate relevant questions for the job role
        if self.job_role and self.job_description:
            # Reset questions
            self.questions = []
            
            # Generate first question - "Tell me about yourself"
            self.questions.append("Tell me about yourself and your background.")
            
            # Generate remaining questions
            for i in range(1, self.question_count):
                next_question = self._generate_next_question_tool()
                if next_question not in self.questions:  # Avoid duplicates
                    self.questions.append(next_question)
        else:
            # Fallback to generic questions if job details not provided
            self._generate_generic_questions()
    
    def _generate_generic_questions(self) -> None:
        """
        Generate a set of generic questions for the interview based on the job role.
        """
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
        
        # Define template variables based on job role
        template_vars = {
            # Software Engineer
            "Software Engineer": {
                "technology": ["React", "Python", "cloud infrastructure", "REST APIs", "microservices", "distributed systems"],
                "scenario": ["the system goes down in production", "requirements change mid-sprint", "you need to optimize performance", "you encounter legacy code"],
                "problem_type": ["algorithmic", "optimization", "debugging", "scaling", "design"],
                "challenge": ["lead a technical project", "mentor junior developers", "work under tight deadlines", "refactor a complex system"],
                "quality_aspect": ["code quality", "test coverage", "system reliability", "security", "documentation"]
            },
            # Data Scientist
            "Data Scientist": {
                "technology": ["Python for data analysis", "machine learning frameworks", "data visualization tools", "natural language processing", "statistical analysis"],
                "scenario": ["the data is incomplete", "results need to be explained to non-technical stakeholders", "model performance is inadequate", "features need to be engineered"],
                "problem_type": ["prediction", "classification", "clustering", "anomaly detection", "optimization"],
                "challenge": ["clean messy data", "deploy a model to production", "interpret complex results", "work with big data"],
                "quality_aspect": ["model accuracy", "reproducibility", "interpretability", "efficiency", "robustness"]
            },
            # Project Manager
            "Project Manager": {
                "technology": ["project management software", "agile methodologies", "resource planning tools", "collaboration platforms", "reporting dashboards"],
                "scenario": ["the project falls behind schedule", "team members conflict", "scope increases unexpectedly", "key resources become unavailable"],
                "problem_type": ["scheduling", "risk management", "resource allocation", "stakeholder", "scope"],
                "challenge": ["manage multiple competing priorities", "deliver a project with limited resources", "handle difficult stakeholders", "rescue a failing project"],
                "quality_aspect": ["on-time delivery", "team productivity", "stakeholder satisfaction", "budget adherence", "process improvement"]
            }
        }
        
        # Use default variables if job role not found
        role_vars = template_vars.get(self.job_role, template_vars["Software Engineer"])
        
        # Get question templates for the current interview style
        style_templates = question_templates.get(self.interview_style, question_templates[InterviewStyle.FORMAL])
        
        # Generate questions
        for template in style_templates:
            # Select a random variable for each placeholder
            for var_name, var_options in role_vars.items():
                if "{" + var_name + "}" in template:
                    template = template.replace("{" + var_name + "}", random.choice(var_options))
            
            generic_questions.append(template)
        
        # Add some general questions
        general_questions = [
            "What attracted you to this position?",
            "Where do you see yourself professionally in five years?",
            f"Why do you think you're a good fit for this {self.job_role} role?",
            "Describe your ideal work environment.",
            "How do you stay updated with the latest developments in your field?"
        ]
        
        self.questions = generic_questions + general_questions
        
        # If job description is present, generate specific questions using LLM
        if self.job_description and len(self.job_description) > 10:
            try:
                specific_questions = self._generate_job_specific_questions()
                self.questions.extend(specific_questions)
            except Exception as e:
                self.logger.error(f"Error generating job-specific questions: {e}")
        
        # Shuffle questions to create a natural interview flow
        random.shuffle(self.questions)
    
    def _generate_job_specific_questions(self) -> List[str]:
        """
        Generate job-specific questions based on the job description.
        
        Returns:
            List of job-specific questions
        """
        prompt = f"""
        You are an expert interviewer creating questions for a {self.job_role} position.
        
        Job Description:
        {self.job_description}
        
        Create 5 specific interview questions that:
        1. Directly relate to key skills or requirements in the job description
        2. Help assess the candidate's suitability for this specific role
        3. Are in a {self.interview_style.value} interview style
        4. Have {self.difficulty_level} difficulty level
        
        Format: Return only the questions as a list, one per line, with no preamble or explanation.
        """
        
        try:
            response = self._call_llm(prompt, None)
            
            # Process the response to extract questions
            questions = [q.strip() for q in response.split("\n") if q.strip() and "?" in q]
            
            # Take up to 5 questions
            return questions[:5]
        except Exception as e:
            self.logger.error(f"Error generating job-specific questions: {e}")
            return []
    
    def _get_next_question(self) -> str:
        """
        Get the next question in the interview.
        
        Returns:
            The next question text
        """
        if not self.questions:
            self._generate_questions()
        
        if self.current_question_index >= len(self.questions):
            return "I don't have any more questions prepared. Let's summarize the interview."
        
        question = self.questions[self.current_question_index]
        self.current_question_index += 1
            
        # Publish event
        self._publish_event("question_asked", {
            "question_index": self.current_question_index - 1,
            "question": question,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Format question based on style
        return self._format_response_by_style(question, "question")
    
    def _process_answer(self, answer_text: str, context: AgentContext) -> dict:
        """
        Process and evaluate the candidate's answer.
        
        Args:
            answer_text: The candidate's answer to evaluate
            context: The agent context
            
        Returns:
            Dictionary with evaluation results
        """
        if not self.current_question:
            return {
                "score": 0,
                "feedback": "No current question to evaluate",
                "areas_of_improvement": [],
                "strengths": []
            }
            
        # Create inputs for the template
        inputs = {
            "question": self.current_question.text,
            "answer": answer_text,
            "question_type": self.current_question.question_type,
            "job_role": self.job_role,
            "job_description": self.job_description
        }
        
        # Add rubric if available
        if hasattr(self.current_question, "rubric") and self.current_question.rubric:
            inputs["rubric"] = self.current_question.rubric
        else:
            inputs["rubric"] = "No specific rubric provided"
        
        try:
            # Call LLM with the evaluation template
            evaluation_text = self._call_llm(ANSWER_EVALUATION_TEMPLATE.format(**inputs), context)
            
            # Set up default evaluation
            default_evaluation = {
                "score": 5,
                "feedback": "The answer was acceptable.",
                "areas_of_improvement": ["Provide more specific examples"],
                "strengths": ["Good communication"],
                "questions_to_probe_further": []
            }
            
            # Parse evaluation
            evaluation = parse_json_with_fallback(evaluation_text, default_evaluation, self.logger)
            
            # Store the evaluation with the question
            if self.current_question and self.questions and self.current_question_index < len(self.questions):
                self.questions[self.current_question_index].evaluation = evaluation
                
            # Adjust overall candidate performance metrics
            self._update_candidate_metrics(evaluation)
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating answer: {e}")
            default_response = {
                "score": 3,
                "feedback": "I had difficulty evaluating your answer completely.",
                "areas_of_improvement": ["Consider providing more specific examples"],
                "strengths": ["You attempted to answer the question"]
            }
            return default_response
    
    def _create_introduction(self) -> str:
        """
        Create an introduction for the interview.
        
        Returns:
            Formatted introduction text
        """
        # Select the appropriate introduction template based on style
        style_key = self.interview_style.value.lower()
        template = INTRODUCTION_TEMPLATES.get(style_key, INTRODUCTION_TEMPLATES["formal"])
        
        # Format the template with job information
        return template.format(
            job_role=self.job_role,
            interview_duration=f"{self.question_count} questions",
            company_name=self.company_name or "our company"
        )
    
    def _format_response_by_style(self, content: str, content_type: str) -> str:
        """
        Format a response based on the interviewer's style.
        
        Args:
            content: The content to format
            content_type: The type of content (question, feedback, etc.)
            
        Returns:
            Formatted response
        """
        # Create inputs for the template
        inputs = {
            "style": self.interview_style.value,
            "content": content,
            "content_type": content_type,
            "job_role": self.job_role
        }
        
        try:
            # Call LLM with the response format template
            return self._call_llm(RESPONSE_FORMAT_TEMPLATE.format(**inputs), AgentContext())
        except Exception as e:
            self.logger.error(f"Error formatting response: {e}")
            return content  # Return the original content if formatting fails
    
    def _handle_user_response(self, event: Event) -> None:
        """
        Handle user response events.
        
        Args:
            event: The event containing the user's response
        """
        # Update the context with the user's response
        if self.current_context:
            self.current_context.add_message("user", event.data.get("response", ""))
    
    def _handle_interview_start(self, event: Event) -> None:
        """
        Handle interview start events.
        
        Args:
            event: The event containing interview configuration
        """
        # Reset interview state
        self.current_state = InterviewState.INITIALIZING
        self.current_question_index = 0
        
        # Update interview parameters if provided
        data = event.data
        if "job_role" in data:
            self.job_role = data["job_role"]
        if "job_description" in data:
            self.job_description = data["job_description"]
        if "interview_style" in data:
            self.interview_style = InterviewStyle(data["interview_style"])
        if "difficulty_level" in data:
            self.difficulty_level = data["difficulty_level"]
        if "question_count" in data:
            self.question_count = data["question_count"]
        
        # Store session ID
        self.interview_session_id = data.get("session_id", None)
    
    def _handle_interview_end(self, event: Event) -> None:
        """
        Handle interview end events.
        
        Args:
            event: The event indicating the interview has ended
        """
        # Reset interview state
        self.current_state = InterviewState.COMPLETED
        self.interview_session_id = None 
    
    def _assess_answer_quality(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Assess the quality of a candidate's answer.
        
        Args:
            question: The question that was asked
            answer: The candidate's answer
            
        Returns:
            Dictionary with quality assessment results
        """
        try:
            response = self.quality_assessment_chain.invoke({
                "job_role": self.job_role,
                "question": question,
                "answer": answer
            })
            
            # Parse the JSON response
            assessment = json.loads(response)
            return assessment
        except Exception as e:
            self.logger.error(f"Error assessing answer quality: {e}")
            return {"score": 3, "justification": "Unable to assess answer", "follow_up_needed": False}
    
    def _generate_follow_up_question(self, original_question: str, answer: str) -> str:
        """
        Generate a follow-up question based on the candidate's answer.
        
        Args:
            original_question: The original question asked
            answer: The candidate's answer
            
        Returns:
            A follow-up question
        """
        response = self.follow_up_chain.invoke({
            "job_role": self.job_role,
            "original_question": original_question,
            "answer": answer
        })
        
        return response["follow_up_question"]
    
    def _create_summary(self, context: AgentContext) -> Dict[str, Any]:
        """
        Create a summary of the interview.
        
        Args:
            context: The agent context
            
        Returns:
            Dictionary with summary results
        """
        # Gather all questions and evaluations
        qa_pairs = []
        for i, question in enumerate(self.questions):
            if hasattr(question, "evaluation") and question.evaluation:
                qa_pairs.append({
                    "question": question.text,
                    "question_type": question.question_type,
                    "answer": question.candidate_answer if hasattr(question, "candidate_answer") else "No answer provided",
                    "evaluation": question.evaluation
                })
        
        # Calculate average score
        scores = [qa["evaluation"].get("score", 0) for qa in qa_pairs if "evaluation" in qa and isinstance(qa["evaluation"], dict)]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Create inputs for the template
        inputs = {
            "job_role": self.job_role,
            "job_description": self.job_description,
            "qa_pairs": json.dumps(qa_pairs, indent=2),
            "average_score": round(average_score, 1),
            "candidate_strengths": json.dumps(self.candidate_metrics.get("strengths", []), indent=2),
            "candidate_weaknesses": json.dumps(self.candidate_metrics.get("areas_of_improvement", []), indent=2)
        }
        
        try:
            # Call LLM with the summary template
            summary_text = self._call_llm(SUMMARY_TEMPLATE.format(**inputs), context)
            
            # Set up default summary
            default_summary = {
                "overall_assessment": "The candidate demonstrated average performance during the interview.",
                "technical_skills": "Demonstrated basic understanding of required technical skills.",
                "communication": "Communication was adequate during the interview.",
                "culture_fit": "The candidate may be a good cultural fit for the organization.",
                "recommendation": "Consider for follow-up interview to further assess skills.",
                "areas_of_strength": self.candidate_metrics.get("strengths", ["Communication skills"]),
                "areas_for_improvement": self.candidate_metrics.get("areas_of_improvement", ["Technical depth"]),
                "overall_score": average_score
            }
            
            # Parse summary result as JSON with fallback
            summary = parse_json_with_fallback(summary_text, default_summary, self.logger)
            
            # Format the summary for display
            formatted_summary = self._format_response_by_style(json.dumps(summary, indent=2), "summary")
            
            # Add formatted text to summary
            summary["formatted_text"] = formatted_summary
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating summary: {e}")
            error_summary = {
                "overall_assessment": "Unable to generate a complete assessment due to an error.",
                "technical_skills": "Assessment not available.",
                "communication": "Assessment not available.",
                "recommendation": "Review interview transcript manually.",
                "areas_of_strength": self.candidate_metrics.get("strengths", []),
                "areas_for_improvement": self.candidate_metrics.get("areas_of_improvement", []),
                "overall_score": average_score,
                "error": str(e)
            }
            
            return error_summary 
    
    def _update_candidate_metrics(self, evaluation: Dict[str, Any]) -> None:
        """
        Update candidate performance metrics based on the latest answer evaluation.
        
        Args:
            evaluation: The evaluation dictionary from _process_answer
        """
        if not evaluation:
            return
            
        # Initialize metrics if needed
        if not hasattr(self, "candidate_metrics"):
            self.candidate_metrics = {
                "strengths": [],
                "areas_of_improvement": [],
                "scores_by_question_type": {},
                "total_questions_by_type": {},
                "follow_up_questions": []
            }
            
        # Update strengths (avoid duplicates but keep track of frequency)
        if "strengths" in evaluation and isinstance(evaluation["strengths"], list):
            for strength in evaluation["strengths"]:
                # Clean and normalize the strength
                clean_strength = strength.strip().lower()
                # Check if similar strength already exists
                exists = False
                for existing in self.candidate_metrics["strengths"]:
                    if clean_strength in existing.lower() or existing.lower() in clean_strength:
                        exists = True
                        break
                
                if not exists:
                    self.candidate_metrics["strengths"].append(strength)
                    
        # Update areas of improvement (avoid duplicates)
        if "areas_of_improvement" in evaluation and isinstance(evaluation["areas_of_improvement"], list):
            for area in evaluation["areas_of_improvement"]:
                # Clean and normalize the area
                clean_area = area.strip().lower()
                # Check if similar area already exists
                exists = False
                for existing in self.candidate_metrics["areas_of_improvement"]:
                    if clean_area in existing.lower() or existing.lower() in clean_area:
                        exists = True
                        break
                
                if not exists:
                    self.candidate_metrics["areas_of_improvement"].append(area)
                    
        # Update scores by question type
        if "score" in evaluation and self.current_question:
            question_type = self.current_question.question_type
            
            # Initialize if needed
            if question_type not in self.candidate_metrics["scores_by_question_type"]:
                self.candidate_metrics["scores_by_question_type"][question_type] = 0
                self.candidate_metrics["total_questions_by_type"][question_type] = 0
                
            # Update scores
            self.candidate_metrics["scores_by_question_type"][question_type] += evaluation["score"]
            self.candidate_metrics["total_questions_by_type"][question_type] += 1
            
        # Track follow-up questions
        if "questions_to_probe_further" in evaluation and isinstance(evaluation["questions_to_probe_further"], list):
            self.candidate_metrics["follow_up_questions"].extend(evaluation["questions_to_probe_further"])

    def _do_action(self, context: AgentContext) -> Dict[str, Any]:
        """
        Perform the next action based on the current state.
        
        Args:
            context: The agent context
            
        Returns:
            Result of the action
        """
        # Get input text
        input_text = context.get_last_user_message() or ""
        
        # Create response based on current state
        if self.current_state == InterviewState.INTRODUCTION:
            # Create and format introduction
            intro_text = self._create_introduction()
            formatted_intro = self._format_response_by_style(intro_text, "introduction")
            
            # Transition to preparation state
            self.current_state = InterviewState.PREPARATION
            
            return {
                "response_type": "introduction",
                "text": formatted_intro
            }
            
        elif self.current_state == InterviewState.PREPARATION:
            # Run planning step
            planning_result = self._run_planning_step(context)
            
            # Generate questions based on planning
            self._generate_questions()
            
            # Transition to questioning state
            self.current_state = InterviewState.QUESTIONING
            
            # Get first question
            question = self._get_next_question()
            formatted_question = self._format_response_by_style(question, "question")
            
            return {
                "response_type": "question",
                "text": formatted_question,
                "planning_result": planning_result
            }
            
        elif self.current_state == InterviewState.QUESTIONING:
            # Process candidate's answer to previous question
            evaluation = self._process_answer(input_text, context)
            
            # Check if we should ask a follow-up question
            if (
                "questions_to_probe_further" in evaluation and
                isinstance(evaluation["questions_to_probe_further"], list) and
                len(evaluation["questions_to_probe_further"]) > 0
            ):
                # Ask a follow-up question
                followup = evaluation["questions_to_probe_further"][0]
                formatted_followup = self._format_response_by_style(followup, "followup_question")
                
                return {
                    "response_type": "followup_question",
                    "text": formatted_followup,
                    "evaluation": evaluation
                }
            else:
                # Get next question or transition to summarizing
                if self.current_question_index >= self.question_count:
                    # Transition to summarizing
                    self.current_state = InterviewState.SUMMARIZING
                    
                    # Generate summary
                    summary = self._create_summary(context)
                    formatted_summary = summary.get("formatted_text", "Interview summary")
                    
                    return {
                        "response_type": "summary",
                        "text": formatted_summary,
                        "summary_data": summary
                    }
                else:
                    # Get next question
                    question = self._get_next_question()
                    formatted_question = self._format_response_by_style(question, "question")
                    
                    return {
                        "response_type": "question",
                        "text": formatted_question,
                        "evaluation": evaluation
                    }
                    
        elif self.current_state == InterviewState.SUMMARIZING:
            # Generate summary
            summary = self._create_summary(context)
            formatted_summary = summary.get("formatted_text", "Interview summary")
            
            # Transition to completed
            self.current_state = InterviewState.COMPLETED
            
            return {
                "response_type": "summary",
                "text": formatted_summary,
                "summary_data": summary
            }
            
        elif self.current_state == InterviewState.COMPLETED:
            return {
                "response_type": "completed",
                "text": "The interview has been completed. Thank you for your participation."
            }
            
        else:
            return {
                "response_type": "error",
                "text": "I'm sorry, there was an issue with the interview state. Please restart the interview."
            } 

    def invoke(self, input_text: str, context: Optional[AgentContext] = None) -> Dict[str, Any]:
        """
        Invoke the agent with the given input.
        
        Args:
            input_text: The input from the user
            context: The agent context
            
        Returns:
            Response containing next action
        """
        # Initialize context if not provided
        if not context:
            context = AgentContext()
            
        # Add user message to context
        context.add_user_message(input_text)
        
        # Execute next action based on current state
        response = self._do_action(context)
        
        # Add agent response to context
        context.add_agent_message(response.get("text", ""))
        
        # Check for completed state
        if response.get("response_type") == "summary":
            self._publish_event("interview_completed", {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": response.get("summary_data", {})
            })
            
        return response 