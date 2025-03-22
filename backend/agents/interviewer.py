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
        return (
            f"You are an AI interviewer for a {self.job_role} position. "
            f"Your interview style is {self.interview_style.value}. "
            "You ask relevant questions, listen carefully to answers, and provide constructive feedback. "
            "Be professional, respectful, and focused on evaluating the candidate's skills and experience.\n\n"
            "Follow this process for each interaction:\n"
            "1. THINK: Analyze the current interview state and candidate's previous responses\n"
            "2. REASON: Determine the most appropriate next action based on interview context\n"
            "3. ACT: Generate a question, provide feedback, or transition the interview as needed\n\n"
            "Format your responses according to the current interview phase to maintain a natural conversation flow."
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
        # Question generation chain with improved prompting for different question types
        question_template = """
        You are interviewing a candidate for a {job_role} position.
        The job description is: {job_description}
        
        The interview style is: {interview_style}
        Current difficulty level: {difficulty_level}
        
        Previous questions asked: {previous_questions}
        Candidate's conversation history: {conversation_history}
        
        TASK: Generate a relevant, {difficulty_level} difficulty interview question

        THINK:
        - Consider what skills and knowledge are most important for this position
        - Review previous questions to avoid redundancy
        - Identify areas not yet explored based on the job description
        - Consider the candidate's previous responses to adjust difficulty
        
        QUESTION TYPE GUIDANCE:
        - Technical: Focus on specific technical skills mentioned in the job description
        - Behavioral: Use the STAR format (Situation, Task, Action, Result)
        - Problem-solving: Present a realistic scenario related to the job role
        - Experience-based: Ask about relevant past experiences
        - Competency-based: Focus on specific skills like communication or leadership
        
        REASONING:
        Based on the interview context, create a {question_type} question that will effectively assess the candidate's suitability.
        
        OUTPUT:
        Generate a clear, concise, and relevant {question_type} question.
        """
        
        self.question_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(question_template),
            output_key="question"
        )
        
        # Answer evaluation chain with improved structure
        evaluation_template = """
        You are evaluating a candidate's answer for a {job_role} position.
        
        Question: {question}
        Candidate's Answer: {answer}
        
        THINK:
        - How relevant is the answer to the question asked?
        - What skills or competencies does the answer demonstrate?
        - How structured and clear is the response?
        - What specific examples or details were provided?
        - What is missing from the answer that would strengthen it?
        
        REASONING:
        Develop a balanced assessment that identifies both strengths and areas for improvement.
        Consider the context of the job role and the specific requirements.
        
        OUTPUT - Provide constructive feedback with this structure:
        1. Strengths: [List 2-3 positive aspects of the answer]
        2. Areas for Improvement: [List 1-2 specific suggestions]
        3. Overall Assessment: [Brief summary evaluation]
        
        Your feedback style should match: {interview_style}
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
        
        # Add new chain for answer quality assessment
        quality_assessment_template = """
        You are assessing the quality of a candidate's answer for a {job_role} position.
        
        Question: {question}
        Candidate's Answer: {answer}
        
        TASK: Evaluate the answer quality on a scale of 1-5 where:
        1: Poor - Irrelevant, incorrect, or severely lacking
        2: Basic - Partially relevant but superficial
        3: Adequate - Relevant and correct but lacking depth
        4: Good - Relevant, correct, and detailed with some examples
        5: Excellent - Comprehensive, insightful, with strong examples
        
        REASONING:
        Analyze the answer against these criteria:
        - Relevance to the question
        - Accuracy of information
        - Depth of understanding
        - Use of specific examples
        - Clarity and structure
        
        OUTPUT - JSON with three fields:
        {
            "score": [1-5 rating],
            "justification": [Brief explanation for the rating],
            "follow_up_needed": [true/false whether a follow-up question is needed]
        }
        """
        
        self.quality_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(quality_assessment_template),
            output_parser=StrOutputParser(),
            output_key="quality_assessment"
        )
        
        # Add new chain for follow-up question generation
        follow_up_template = """
        You are interviewing a candidate for a {job_role} position.
        
        Original Question: {original_question}
        Candidate's Answer: {answer}
        
        TASK: Generate a follow-up question to gain more insight
        
        THINK:
        - What aspects of the answer were unclear or incomplete?
        - What additional details would help better assess the candidate?
        - How can you probe deeper into their experience or knowledge?
        
        REASONING:
        Create a follow-up question that will encourage the candidate to expand on their answer,
        provide specific examples, or clarify their thinking.
        
        OUTPUT:
        A clear, concise follow-up question that naturally builds on the previous response.
        """
        
        self.follow_up_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(follow_up_template),
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
            response = self._handle_summary(context)
        else:
            response = "I'm sorry, there was an issue with the interview state. Let's restart."
            self.current_state = InterviewState.INITIALIZING
        
        # Add assistant message to context
        context.add_message("assistant", response)
        
        # Return response
        return response
    
    def _think_about_input(self, input_text: str, context: AgentContext) -> Dict[str, Any]:
        """
        Analyze the current input and context (Think step of ReAct).
        
        Args:
            input_text: The user input text
            context: The agent context
            
        Returns:
            Dictionary with analysis results
        """
        # Get conversation history
        history = context.get_history_as_text()
        
        # Get current interview state
        interview_state = self.current_state.value
        
        # Prepare prompt for analysis
        prompt = f"""
        You are an AI interviewer for a {self.job_role} position with a {self.interview_style.value} interview style.
        
        Current interview state: {interview_state}
        
        Recent conversation:
        {history}
        
        Candidate's latest response:
        {input_text}
        
        Analyze this response considering:
        - How relevant is it to the current interview state and previous questions?
        - What key topics or skills does it mention or demonstrate?
        - What is the sentiment and confidence level conveyed?
        - How complete or detailed is the response?
        
        Provide your analysis in JSON format with these fields:
        - input_analysis: Your overall analysis of the response
        - key_topics: List of important topics mentioned
        - sentiment: The candidate's apparent sentiment (positive, neutral, negative)
        - relevance: How relevant the response is (high, medium, low)
        - completeness: How complete the response is (high, medium, low)
        """
        
        try:
            # Call LLM to analyze input
            analysis_text = self._call_llm(prompt, context)
            
            # Parse analysis as JSON if possible
            try:
                analysis = json.loads(analysis_text)
            except:
                # If not valid JSON, create a simple dictionary
                analysis = {
                    "input_analysis": analysis_text,
                    "key_topics": [],
                    "sentiment": "neutral",
                    "relevance": "medium"
                }
            
            return analysis
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
        # Prepare prompt for reasoning
        prompt = f"""
        You are an AI interviewer for a {self.job_role} position with a {self.interview_style.value} interview style.
        
        Current interview state: {self.current_state.value}
        Current progress: {self.current_question_index}/{self.question_count} questions
        
        Analysis of candidate's response:
        {json.dumps(think_result, indent=2)}
        
        Based on this analysis, determine the most appropriate next action:
        - Should you continue with the current interview state?
        - Should you transition to a different state?
        - Is a follow-up question needed?
        - Is special guidance needed?
        
        Provide your reasoning in JSON format with these fields:
        - next_action: The action to take (continue, follow_up, provide_guidance, change_state)
        - justification: Why this action is appropriate
        - should_change_state: Boolean indicating if state should change
        - suggested_state: The state to change to if applicable
        """
        
        try:
            # Call LLM to reason about next action
            reasoning_text = self._call_llm(prompt, context)
            
            # Parse reasoning as JSON if possible
            try:
                reasoning = json.loads(reasoning_text)
            except:
                # If not valid JSON, create a simple dictionary
                reasoning = {
                    "next_action": "continue",
                    "justification": reasoning_text,
                    "should_change_state": False,
                    "suggested_state": self.current_state.value
                }
            
            # Check if state should be changed
            if reasoning.get("should_change_state", False):
                try:
                    new_state = InterviewState(reasoning.get("suggested_state", self.current_state.value))
                    self.current_state = new_state
                    self.logger.info(f"Changed interview state to {new_state}")
                except:
                    self.logger.error(f"Invalid interview state suggested: {reasoning.get('suggested_state')}")
            
            return reasoning
        except Exception as e:
            self.logger.error(f"Error in reason step: {e}")
            return {
                "next_action": "continue",
                "justification": "Error in reasoning process",
                "should_change_state": False,
                "suggested_state": self.current_state.value
            }
    
    def _run_planning_step(self, context: AgentContext) -> Dict[str, Any]:
        """
        Run a planning step to adjust the interview strategy based on context.
        
        Args:
            context: The current context
            
        Returns:
            The planning result
        """
        # Get conversation history
        history = context.get_history_as_text()
        
        # Prepare planning prompt
        planning_prompt = f"""
        You are an AI interviewer for a {self.job_role} position.
        Your current interview style is {self.interview_style.value}.
        You've asked {self.current_question_index} questions out of a planned {self.question_count}.
        
        Current interview state: {self.current_state.value}
        
        Recent conversation history:
        {history}
        
        Analyze the interview progress and decide if any adjustments are needed:
        1. Is the current interview style effective, or should it be adjusted?
        2. Are the questions at an appropriate difficulty level?
        3. Are there specific topics that should be explored further?
        4. Is the pace of the interview appropriate?
        
        Provide your strategic plan in JSON format with these fields:
        - continue_current_approach: Boolean indicating if current approach is working
        - suggested_style_adjustment: Any adjustment to interview style
        - suggested_difficulty_adjustment: Any adjustment to question difficulty
        - focus_areas: List of topics to focus on in upcoming questions
        - pace_adjustment: Any adjustment to interview pace
        - additional_notes: Any other strategic considerations
        """
        
        try:
            # Call LLM for planning
            planning_result_text = self._call_llm(planning_prompt, context)
            
            # Parse result as JSON
            try:
                planning_result = json.loads(planning_result_text)
            except:
                planning_result = {
                    "continue_current_approach": True,
                    "additional_notes": planning_result_text
                }
            
            # Apply any suggested adjustments
            if planning_result.get("suggested_difficulty_adjustment"):
                difficulty_adj = planning_result.get("suggested_difficulty_adjustment").lower()
                if "easier" in difficulty_adj:
                    self.difficulty_level = "easy"
                elif "harder" in difficulty_adj:
                    self.difficulty_level = "hard"
                else:
                    self.difficulty_level = "medium"
            
            # Update context with planning result
            context.metadata["last_planning"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "result": planning_result
            }
            
            return planning_result
        except Exception as e:
            self.logger.error(f"Error in planning step: {e}")
            return {
                "continue_current_approach": True,
                "error": str(e)
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
                guidance = self._evaluate_answer_tool(input_text, current_q_index)
                next_question = self._get_next_question()
                response = f"{guidance}\n\nLet's move on to the next question.\n\n{next_question}"
            else:
                # Get the next question
                response = self._get_next_question()
        else:
            # First question or error recovery
            response = self._get_next_question()
        
        # If we've reached the end of questions, transition to summary
        if self.current_question_index >= len(self.questions) or self.current_question_index >= self.question_count:
            self.current_state = InterviewState.SUMMARIZING
            return self._handle_summary(context)
        
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
        Handle the summary state of the interview.
        
        Args:
            context: The agent context
            
        Returns:
            The summary response
        """
        # Get question-answer history
        qa_history = ""
        for i, message in enumerate(context.conversation_history):
            if message["role"] == "assistant" and i > 0 and i < len(context.conversation_history) - 1:
                prev_message = context.conversation_history[i-1]
                if prev_message["role"] == "user":
                    qa_history += f"Question: {message['content']}\n"
                    qa_history += f"Answer: {prev_message['content']}\n\n"
        
        # Generate summary
        summary = self._summarize_interview_tool({"qa_history": qa_history})
        
        # Publish event
        self._publish_event("interview_summarized", {
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update state
        self.current_state = InterviewState.COMPLETED
        
        # Format summary based on style
        return self._format_response_by_style(summary, "summary")
    
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
    
    def _evaluate_answer(self, answer_text: str, question_index: int) -> str:
        """
        Evaluate an answer to a question.
        
        Args:
            answer_text: The answer text
            question_index: The index of the question
            
        Returns:
            Feedback on the answer
        """
        # Get the question
        question = self.questions[question_index] if question_index < len(self.questions) else "Unknown question"
        
        # Get feedback
        feedback = self._evaluate_answer_tool(answer_text, question_index)
        
        # Publish event
        self._publish_event("answer_evaluated", {
            "question_index": question_index,
            "question": question,
            "answer": answer_text,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Format feedback based on style
        return self._format_response_by_style(feedback, "feedback")
    
    def _create_introduction(self) -> str:
        """
        Create an introduction for the interview based on the interview style.
        
        Returns:
            Introduction message
        """
        job_role = self.job_role or "this position"
        
        # Base introduction components
        intro_components = {
            "greeting": f"Hello! I'll be conducting your interview for the {job_role} position today.",
            "purpose": "I'll ask you a series of questions to evaluate your skills and experience.",
            "expectation": "Please provide detailed, specific answers with examples from your experience when possible.",
            "format": f"I'll ask you about {self.question_count} questions, and provide feedback at the end.",
            "ready": "Let's begin. Are you ready for your first question?"
        }
        
        # Style-specific customizations
        style_customizations = {
            InterviewStyle.FORMAL: {
                "greeting": f"Good day. I am conducting your formal interview for the {job_role} position.",
                "tone": "professional and thorough",
                "formality": "This will be a structured interview following standard protocols.",
                "closing": "Please take a moment to prepare, and we will proceed with the first question."
            },
            InterviewStyle.CASUAL: {
                "greeting": f"Hi there! Thanks for joining me today for your {job_role} interview.",
                "tone": "conversational and relaxed",
                "formality": "We'll keep this pretty casual, like a conversation between colleagues.",
                "closing": "Feel free to ask questions anytime. Ready to get started?"
            },
            InterviewStyle.AGGRESSIVE: {
                "greeting": f"Let's get started with your interview for the {job_role} position.",
                "tone": "challenging and direct",
                "formality": "I'll be asking pointed questions to really test your capabilities.",
                "closing": "I expect precise, substantive answers. Let's see what you've got."
            },
            InterviewStyle.TECHNICAL: {
                "greeting": f"Welcome to your technical interview for the {job_role} position.",
                "tone": "technically focused and detailed",
                "formality": "This interview will focus on assessing your technical knowledge and problem-solving abilities.",
                "closing": "I'll be looking for specificity and technical accuracy in your responses."
            }
        }
        
        # Get style-specific components
        style_components = style_customizations.get(self.interview_style, style_customizations[InterviewStyle.FORMAL])
        
        # Create introduction based on style
        introduction = f"{style_components.get('greeting', intro_components['greeting'])}\n\n"
        
        introduction += f"This will be a {style_components.get('tone', 'professional')} interview. "
        introduction += f"{style_components.get('formality', intro_components['purpose'])}\n\n"
        
        introduction += f"{intro_components['expectation']}\n"
        introduction += f"{intro_components['format']}\n\n"
        
        introduction += f"{style_components.get('closing', intro_components['ready'])}"
        
        return introduction
    
    def _format_response_by_style(self, content: str, response_type: str = "question") -> str:
        """
        Format the response based on the interview style.
        
        Args:
            content: The content to format
            response_type: The type of response (question, feedback, summary)
            
        Returns:
            Formatted response
        """
        # Style-specific prefixes and suffixes
        style_formatting = {
            InterviewStyle.FORMAL: {
                "question_prefix": "The next question is: ",
                "question_suffix": "\n\nPlease provide a comprehensive response.",
                "feedback_prefix": "Evaluation: ",
                "feedback_suffix": "\n\nLet's continue with the next question.",
                "summary_prefix": "Interview Assessment:\n\n",
                "summary_suffix": "\n\nThank you for participating in this interview process."
            },
            InterviewStyle.CASUAL: {
                "question_prefix": "Let's talk about: ",
                "question_suffix": "\n\nWhat are your thoughts on this?",
                "feedback_prefix": "About your answer: ",
                "feedback_suffix": "\n\nLet's move on to something else.",
                "summary_prefix": "Here's how I think the interview went:\n\n",
                "summary_suffix": "\n\nThanks for the great conversation!"
            },
            InterviewStyle.AGGRESSIVE: {
                "question_prefix": "Next: ",
                "question_suffix": "\n\nBe specific and direct in your answer.",
                "feedback_prefix": "Feedback: ",
                "feedback_suffix": "\n\nMoving on immediately.",
                "summary_prefix": "Interview Performance Analysis:\n\n",
                "summary_suffix": "\n\nThat concludes this interview session."
            },
            InterviewStyle.TECHNICAL: {
                "question_prefix": "Technical Question: ",
                "question_suffix": "\n\nPlease provide specific technical details in your response.",
                "feedback_prefix": "Technical Assessment: ",
                "feedback_suffix": "\n\nLet's proceed to the next technical area.",
                "summary_prefix": "Technical Evaluation Summary:\n\n",
                "summary_suffix": "\n\nThank you for demonstrating your technical knowledge today."
            }
        }
        
        # Get formatting for current style
        formatting = style_formatting.get(self.interview_style, style_formatting[InterviewStyle.FORMAL])
        
        # Apply formatting based on response type
        if response_type == "question":
            return f"{formatting['question_prefix']}{content}{formatting['question_suffix']}"
        elif response_type == "feedback":
            return f"{formatting['feedback_prefix']}{content}{formatting['feedback_suffix']}"
        elif response_type == "summary":
            return f"{formatting['summary_prefix']}{content}{formatting['summary_suffix']}"
        else:
            return content
    
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