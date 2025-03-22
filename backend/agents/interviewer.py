"""
Interviewer agent responsible for conducting interview sessions.
This agent asks questions, evaluates answers, and provides feedback.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import random
from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_core.output_parsers import StrOutputParser

from backend.agents.base import BaseAgent, AgentContext
from backend.utils.event_bus import Event, EventBus
from backend.models.interview import InterviewStyle, InterviewSession, Question, Answer


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
        return (
            f"You are an AI interviewer for a {self.job_role} position. "
            f"Your interview style is {self.interview_style.value}. "
            "You ask relevant questions, listen carefully to answers, and provide constructive feedback. "
            "Be professional, respectful, and focused on evaluating the candidate's skills and experience."
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
                func=self._evaluate_answer_tool,
                description="Evaluate the candidate's answer and provide feedback"
            ),
            Tool(
                name="summarize_interview",
                func=self._summarize_interview_tool,
                description="Generate a summary of the interview with feedback and recommendations"
            )
        ]
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Question generation chain
        question_template = """
        You are interviewing a candidate for a {job_role} position.
        The job description is: {job_description}
        
        The interview style is: {interview_style}
        
        Previous questions asked: {previous_questions}
        
        Generate a relevant, {difficulty_level} difficulty interview question that:
        1. Tests skills relevant to the job role
        2. Is not redundant with previous questions
        3. Follows the specified interview style
        4. Helps evaluate the candidate's suitability
        
        The question should be direct and clear. Avoid preambles or explanations.
        """
        
        self.question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(question_template),
            output_key="question"
        )
        
        # Answer evaluation chain
        evaluation_template = """
        You are evaluating a candidate's answer for a {job_role} position.
        
        Question: {question}
        Candidate's Answer: {answer}
        
        Provide constructive feedback on the answer considering:
        1. Relevance to the question
        2. Demonstration of required skills and experience
        3. Communication clarity and structure
        4. Specific examples or details provided
        
        Your feedback style should be: {interview_style}
        
        Provide balanced feedback with strengths and areas for improvement.
        """
        
        self.evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(evaluation_template),
            output_key="feedback"
        )
        
        # Interview summary chain
        summary_template = """
        You are summarizing an interview for a {job_role} position.
        
        Job Description: {job_description}
        
        Questions and Answers:
        {qa_history}
        
        Provide a comprehensive summary of the interview including:
        1. Overall impression of the candidate
        2. Key strengths demonstrated
        3. Areas for improvement
        4. Suitability for the position
        5. Specific recommendations for the candidate
        
        Be constructive, balanced, and specific in your assessment.
        """
        
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(summary_template),
            output_key="summary"
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
    
    def _evaluate_answer_tool(self, answer: str, question_index: int = None) -> str:
        """
        Tool function to evaluate a candidate's answer.
        
        Args:
            answer: The candidate's answer
            question_index: Optional index of the question (uses current if not provided)
            
        Returns:
            Feedback on the answer
        """
        if question_index is None:
            question_index = max(0, self.current_question_index - 1)
        
        question = self.questions[question_index] if question_index < len(self.questions) else "Unknown question"
        
        response = self.evaluation_chain.invoke({
            "job_role": self.job_role,
            "question": question,
            "answer": answer,
            "interview_style": self.interview_style.value
        })
        
        return response["feedback"]
    
    def _summarize_interview_tool(self, args: Optional[Dict[str, Any]] = None) -> str:
        """
        Tool function to summarize the interview.
        
        Args:
            args: Optional arguments for the tool
            
        Returns:
            Interview summary
        """
        if not self.current_context:
            return "No interview context available."
        
        # Construct QA history
        qa_pairs = []
        current_question = None
        
        for message in self.current_context.conversation_history:
            if message["role"] == "assistant" and message.get("metadata", {}).get("is_question", False):
                current_question = message["content"]
            elif message["role"] == "user" and current_question:
                qa_pairs.append(f"Q: {current_question}\nA: {message['content']}")
                current_question = None
        
        qa_history = "\n\n".join(qa_pairs)
        
        response = self.summary_chain.invoke({
            "job_role": self.job_role,
            "job_description": self.job_description,
            "qa_history": qa_history or "No question-answer pairs available."
        })
        
        return response["summary"]
    
    def process_input(self, input_text: str, context: AgentContext) -> str:
        """
        Process input from the user and generate a response.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            The agent's response
        """
        # Set current context if provided
        if context:
            self.current_context = context
        
        # Update context with user input
        self.current_context.add_message("user", input_text)
        
        response = ""
        
        # Process based on current state
        if self.current_state == InterviewState.INITIALIZING:
            response = self._handle_initialization(self.current_context)
        elif self.current_state == InterviewState.INTRODUCING:
            response = self._handle_introduction(self.current_context)
        elif self.current_state == InterviewState.QUESTIONING:
            response = self._handle_questioning(input_text, self.current_context)
        elif self.current_state == InterviewState.EVALUATING:
            response = self._handle_evaluation(input_text, self.current_context)
        elif self.current_state == InterviewState.TRANSITIONING:
            response = self._handle_transition(self.current_context)
        elif self.current_state == InterviewState.SUMMARIZING:
            response = self._handle_summary(self.current_context)
        elif self.current_state == InterviewState.COMPLETED:
            response = "The interview has concluded. Would you like to see your summary or start a new session?"
        
        # Add response to context
        self.current_context.add_message("assistant", response)
        
        # Publish event
        if self.event_bus:
            self.event_bus.publish(Event(
                event_type="interviewer_response",
                source="interviewer_agent",
                data={
                    "response": response,
                    "current_state": self.current_state.value,
                    "session_id": self.interview_session_id,
                    "current_question_index": self.current_question_index,
                    "total_questions": len(self.questions) if self.questions else self.question_count
                }
            ))
        
        return response
    
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
        Handle the questioning phase of the interview.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            Feedback and next question, or transition to summary
        """
        # Transition to evaluation state
        self.current_state = InterviewState.EVALUATING
        
        # Evaluate the answer using LangChain
        feedback = self._evaluate_answer(input_text, self.current_question_index - 1)
        
        # Check if we've asked all questions
        if self.current_question_index >= len(self.questions):
            self.current_state = InterviewState.SUMMARIZING
            return f"{feedback}\n\nThat concludes all our questions. Let me prepare a summary of your interview performance."
        else:
            self.current_state = InterviewState.TRANSITIONING
            return feedback
    
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
        feedback = self._evaluate_answer(input_text, self.current_question_index - 1)
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
    
    def _handle_summary(self, context: AgentContext) -> str:
        """
        Generate a summary of the interview.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Summary of the interview with feedback
        """
        # Transition to completed state
        self.current_state = InterviewState.COMPLETED
        
        # Generate the summary using LLM
        return self._summarize_interview_tool()
    
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
        Generate generic interview questions as a fallback.
        """
        # Sample questions for different job roles
        generic_questions = [
            "Tell me about yourself and your background.",
            "What are your key strengths and weaknesses?",
            "Why are you interested in this position?",
            "How do you handle pressure and stressful situations?",
            "Describe a challenging situation you faced and how you resolved it.",
            "Where do you see yourself in five years?",
            "What motivates you in your work?",
            "How do you approach learning new skills?",
            "Describe your ideal work environment.",
            "Do you have any questions for me about the role or company?"
        ]
        
        technical_questions = {
            "software engineer": [
                "Explain the difference between inheritance and composition.",
                "How would you optimize a slow database query?",
                "What testing strategies do you typically employ?",
                "Describe your experience with CI/CD pipelines.",
                "How do you approach debugging a complex issue?"
            ],
            "data scientist": [
                "Explain the difference between supervised and unsupervised learning.",
                "How do you handle missing data in a dataset?",
                "Explain overfitting and how to prevent it.",
                "How would you evaluate the performance of a classification model?",
                "Describe a data analysis project you've worked on."
            ],
            "product manager": [
                "How do you prioritize product features?",
                "Describe how you would launch a new product.",
                "How do you gather and incorporate user feedback?",
                "How do you resolve conflicts between stakeholders?",
                "Describe your approach to creating a product roadmap."
            ]
        }
        
        # Start with generic questions
        self.questions = generic_questions.copy()
        
        # Add role-specific questions if available
        role = self.job_role.lower()
        for key in technical_questions:
            if key in role:
                self.questions.extend(technical_questions[key])
                break
        
        # Shuffle questions (except the first "tell me about yourself")
        first_question = self.questions[0]
        remaining = self.questions[1:]
        random.shuffle(remaining)
        self.questions = [first_question] + remaining
        
        # Limit to desired question count
        self.questions = self.questions[:self.question_count]
    
    def _get_next_question(self) -> str:
        """
        Get the next question to ask.
        
        Returns:
            The next question text
        """
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.current_question_index += 1
            
            # Format based on interview style
            question_prefix = ""
            if self.interview_style == InterviewStyle.FORMAL:
                question_prefix = "Next question: "
            elif self.interview_style == InterviewStyle.CASUAL:
                question_prefix = "So, I'd like to know: "
            elif self.interview_style == InterviewStyle.AGGRESSIVE:
                question_prefix = "Tell me this, and be specific: "
            elif self.interview_style == InterviewStyle.TECHNICAL:
                question_prefix = "Let's assess your technical knowledge: "
            
            return f"{question_prefix}{question}"
        else:
            self.current_state = InterviewState.SUMMARIZING
            return "That concludes all our questions. Let me prepare a summary of your interview performance."
    
    def _evaluate_answer(self, answer_text: str, question_index: int) -> str:
        """
        Evaluate the user's answer and provide feedback.
        
        Args:
            answer_text: The user's answer
            question_index: Index of the question being answered
            
        Returns:
            Feedback on the answer
        """
        return self._evaluate_answer_tool(answer_text, question_index)
    
    def _create_introduction(self) -> str:
        """
        Create an introduction message based on interview style.
        
        Returns:
            Introduction message
        """
        base_intro = f"Welcome to your interview preparation session for the {self.job_role} position. "
        
        if self.interview_style == InterviewStyle.FORMAL:
            intro = (
                f"{base_intro}I'll be conducting a formal interview with you today. "
                f"We'll cover {len(self.questions)} questions related to the role. "
                "Please take your time to provide thoughtful answers, and I'll offer feedback after each response."
            )
        elif self.interview_style == InterviewStyle.CASUAL:
            intro = (
                f"{base_intro}Let's have a relaxed conversation about your fit for this role. "
                f"I have {len(self.questions)} questions for us to discuss, but feel free to ask questions along the way. "
                "This is meant to be more of a dialogue than a formal interview."
            )
        elif self.interview_style == InterviewStyle.AGGRESSIVE:
            intro = (
                f"{base_intro}I'll be conducting a challenging interview to really test your abilities. "
                f"I have {len(self.questions)} tough questions prepared. "
                "Remember, some interviewers use this style to see how you perform under pressure, "
                "so try to stay composed and focused with your answers."
            )
        elif self.interview_style == InterviewStyle.TECHNICAL:
            intro = (
                f"{base_intro}This will be a technical interview focusing on your skills and expertise. "
                f"I've prepared {len(self.questions)} questions to assess your technical knowledge and problem-solving abilities. "
                "Be specific in your answers and don't hesitate to demonstrate your depth of understanding."
            )
        else:
            intro = (
                f"{base_intro}I'll be asking you {len(self.questions)} questions related to the role. "
                "After each of your responses, I'll provide feedback to help you improve."
            )
        
        return intro
    
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