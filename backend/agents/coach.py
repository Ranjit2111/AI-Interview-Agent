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
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime
import json
import re
import random

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.output_parsers.json import JsonOutputParser
from langchain.output_parsers.structured import StructuredOutputParser
from langchain.output_parsers.format_instructions import FORMAT_INSTRUCTIONS

try:
    # Try standard import in production
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import Event, EventBus
    from backend.agents.templates.coach_templates import (
        ANALYSIS_TEMPLATE,
        TIPS_TEMPLATE,
        SUMMARY_TEMPLATE,
        TEMPLATE_PROMPT,
        STAR_EVALUATION_TEMPLATE,
        PERFORMANCE_ANALYSIS_TEMPLATE,
        COMMUNICATION_ASSESSMENT_TEMPLATE,
        COMPLETENESS_EVALUATION_TEMPLATE,
        PERSONALIZED_FEEDBACK_TEMPLATE,
        PERFORMANCE_METRICS_TEMPLATE,
        FEEDBACK_TEMPLATES,
        GENERAL_ADVICE_TEMPLATE,
        STAR_METHOD_ADVICE_TEMPLATE,
        SYSTEM_PROMPT,
        PRACTICE_QUESTION_PROMPT,
        PRACTICE_QUESTION_RESPONSE_TEMPLATE
    )
    from backend.agents.utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        extract_field_safely,
        format_conversation_history,
        calculate_average_scores
    )
except ImportError:
    # Use relative imports for development/testing
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import Event, EventBus
    from .templates.coach_templates import (
        ANALYSIS_TEMPLATE,
        TIPS_TEMPLATE,
        SUMMARY_TEMPLATE,
        TEMPLATE_PROMPT,
        STAR_EVALUATION_TEMPLATE,
        PERFORMANCE_ANALYSIS_TEMPLATE,
        COMMUNICATION_ASSESSMENT_TEMPLATE,
        COMPLETENESS_EVALUATION_TEMPLATE,
        PERSONALIZED_FEEDBACK_TEMPLATE,
        PERFORMANCE_METRICS_TEMPLATE,
        FEEDBACK_TEMPLATES,
        GENERAL_ADVICE_TEMPLATE,
        STAR_METHOD_ADVICE_TEMPLATE,
        SYSTEM_PROMPT,
        PRACTICE_QUESTION_PROMPT,
        PRACTICE_QUESTION_RESPONSE_TEMPLATE
    )
    from .utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        extract_field_safely,
        format_conversation_history,
        calculate_average_scores
    )


class CoachingFocus(str):
    """
    Predefined coaching focus areas.
    These represent different aspects of interview performance that can be coached.
    """
    COMMUNICATION = "communication"
    CONTENT = "content"
    CONFIDENCE = "confidence"
    TECHNICAL_DEPTH = "technical_depth"
    STORYTELLING = "storytelling"
    SPECIFICITY = "specificity"
    BODY_LANGUAGE = "body_language"
    CONCISENESS = "conciseness"


class CoachingMode(str):
    """Enum representing the coaching modes."""
    REAL_TIME = "real_time"
    SUMMARY = "summary"
    TARGETED = "targeted"
    PASSIVE = "passive"


class CoachAgent(BaseAgent):
    """
    Agent that provides coaching and feedback during interview preparation.
    
    The coach agent is responsible for:
    - Analyzing user's interview answers
    - Providing real-time feedback and improvement suggestions
    - Identifying strengths and weaknesses
    - Offering personalized coaching plans
    - Suggesting resources for skill development
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        planning_interval: int = 5,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        coaching_mode: CoachingMode = CoachingMode.REAL_TIME,
        coaching_focus: Optional[List[str]] = None,
        feedback_verbosity: str = "detailed"
    ):
        """
        Initialize the coach agent.
        
        Args:
            api_key: API key for the language model
            model_name: Name of the language model to use
            planning_interval: Number of interactions before planning
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            coaching_mode: Mode of coaching (real_time, summary, targeted, passive)
            coaching_focus: List of areas to focus coaching on (defaults to all areas)
            feedback_verbosity: Level of detail in feedback (brief, moderate, detailed)
        """
        super().__init__(api_key, model_name, planning_interval, event_bus, logger)
        
        self.coaching_mode = coaching_mode
        self.coaching_focus = coaching_focus or [
            CoachingFocus.COMMUNICATION,
            CoachingFocus.CONTENT,
            CoachingFocus.CONFIDENCE,
            CoachingFocus.SPECIFICITY
        ]
        self.feedback_verbosity = feedback_verbosity
        self.interview_session_id = None
        self.current_question = None
        self.current_answer = None
        self.interview_performance = {}
        self.improvement_areas = set()
        self.strength_areas = set()
        
        # Setup LLM chains
        self._setup_llm_chains()
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe("interviewer_response", self._handle_interviewer_message)
            self.event_bus.subscribe("user_response", self._handle_user_message)
            self.event_bus.subscribe("interview_summary", self._handle_interview_summary)
            self.event_bus.subscribe("coaching_request", self._handle_coaching_request)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the coach agent.
        
        Returns:
            System prompt string
        """
        return SYSTEM_PROMPT.format(
            coaching_mode=self.coaching_mode,
            coaching_focus=', '.join(self.coaching_focus)
        )
    
    def _initialize_tools(self) -> List[Tool]:
        """
        Initialize tools for the coach agent.
        
        Returns:
            List of LangChain tools
        """
        return [
            Tool(
                name="analyze_response",
                func=self._analyze_response_tool,
                description="Analyze a candidate's response to an interview question and provide feedback"
            ),
            Tool(
                name="generate_improvement_tips",
                func=self._generate_improvement_tips_tool,
                description="Generate specific tips for improving in particular areas of interview performance"
            ),
            Tool(
                name="create_coaching_summary",
                func=self._create_coaching_summary_tool,
                description="Create a comprehensive coaching summary based on the entire interview"
            ),
            Tool(
                name="generate_response_template",
                func=self._generate_response_template_tool,
                description="Generate a template for how to effectively answer a specific type of interview question"
            ),
            Tool(
                name="generate_practice_question",
                func=self._generate_practice_question_tool,
                description="Generate a practice interview question based on specified parameters"
            )
        ]
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Response analysis chain
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(ANALYSIS_TEMPLATE),
            output_key="analysis"
        )
        
        # Improvement tips chain
        self.tips_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(TIPS_TEMPLATE),
            output_key="tips"
        )
        
        # Coaching summary chain
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(SUMMARY_TEMPLATE),
            output_key="coaching_summary"
        )
        
        # Response template chain
        self.template_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(TEMPLATE_PROMPT),
            output_key="response_template"
        )
        
        # Create STAR method evaluation chain
        self.star_evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(STAR_EVALUATION_TEMPLATE),
            output_key="star_evaluation"
        )
        
        # Performance analysis chain
        self.performance_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(PERFORMANCE_ANALYSIS_TEMPLATE),
            output_key="performance_analysis"
        )
        
        # Create communication skills assessment chain
        self.communication_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(COMMUNICATION_ASSESSMENT_TEMPLATE),
            output_key="communication_assessment"
        )
        
        # Create completeness evaluation chain
        self.completeness_evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(COMPLETENESS_EVALUATION_TEMPLATE),
            output_key="completeness_evaluation"
        )
        
        # Create personalized feedback generator chain
        self.personalized_feedback_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(PERSONALIZED_FEEDBACK_TEMPLATE),
            output_key="personalized_feedback"
        )
        
        # Create performance tracker/metrics generator
        self.performance_metrics_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(PERFORMANCE_METRICS_TEMPLATE),
            output_key="performance_metrics"
        )
        
        # Create structured feedback templates
        self.feedback_templates = FEEDBACK_TEMPLATES
    
    def _analyze_response_tool(self, question: str, response: str) -> str:
        """
        Tool function to analyze a candidate's response to an interview question.
        
        Args:
            question: The interview question
            response: The candidate's response
            
        Returns:
            Analysis of the response
        """
        return self.analysis_chain.invoke({
            "question": question,
            "response": response,
            "focus_areas": ", ".join(self.coaching_focus)
        })["analysis"]
    
    def _generate_improvement_tips_tool(self, focus_area: str, context: str) -> str:
        """
        Tool function to generate improvement tips for a specific area.
        
        Args:
            focus_area: The area to focus on
            context: Context about the candidate's performance
            
        Returns:
            Improvement tips
        """
        return self.tips_chain.invoke({
            "focus_area": focus_area,
            "context": context
        })["tips"]
    
    def _create_coaching_summary_tool(self, interview_context: str, qa_pairs: List[Dict[str, str]]) -> str:
        """
        Tool function to create a comprehensive coaching summary.
        
        Args:
            interview_context: Context about the interview
            qa_pairs: List of question-answer pairs
            
        Returns:
            Coaching summary
        """
        qa_text = "\n\n".join([f"Q: {pair['question']}\nA: {pair['answer']}" for pair in qa_pairs])
        
        return self.summary_chain.invoke({
            "interview_context": interview_context,
            "qa_pairs": qa_text,
            "focus_areas": ", ".join(self.coaching_focus)
        })["coaching_summary"]
    
    def _generate_response_template_tool(self, question_type: str, example_question: str, job_role: str) -> str:
        """
        Tool function to generate a template for answering a specific type of question.
        
        Args:
            question_type: The type of question
            example_question: An example question of this type
            job_role: The candidate's job role
            
        Returns:
            Response template
        """
        return self.template_chain.invoke({
            "question_type": question_type,
            "example_question": example_question,
            "job_role": job_role
        })["response_template"]
    
    def process_input(self, message: str, context: AgentContext = None) -> Union[str, Dict]:
        """
        Process input message and generate coaching feedback.
        
        This is the main method called by the agent framework.
        
        Args:
            message: The input message from the user
            context: The agent context
            
        Returns:
            The response message or a structured response
        """
        if not context:
            context = self._create_context()
        
        # Get the current state and metadata from context
        current_state = context.get_state()
        metadata = context.get_metadata()
        
        # Extract interview data if available
        question = metadata.get("current_question", "")
        previous_answer = metadata.get("previous_answer", "")
        job_role = metadata.get("job_role", "the position")
        candidate_info = metadata.get("candidate_profile", {})
        
        # Parse the input to determine what the user is asking for
        user_intent = self._analyze_user_intent(message, current_state)
        
        # Handle different user intents
        if user_intent["intent"] == "request_feedback":
            # User is asking for feedback on their answer
            if not previous_answer:
                return "I don't have your previous answer to evaluate. Please provide an answer to receive feedback."
            
            # Store current feedback request for tracking
            if "evaluation_history" not in metadata:
                metadata["evaluation_history"] = []
            
            # Determine if we should use STAR method evaluation
            requires_star = self._requires_star_evaluation(question, previous_answer)
            
            # Determine feedback type based on message content
            feedback_type = self._determine_feedback_type(message, requires_star)
            
            # Generate evaluations based on feedback type
            evaluations = {}
            
            if feedback_type == "comprehensive" or feedback_type == "star_method":
                evaluations["star"] = self._evaluate_star_method(question, previous_answer)
            
            if feedback_type == "comprehensive" or feedback_type == "communication":
                evaluations["communication"] = self._evaluate_communication_skills(question, previous_answer)
            
            if feedback_type == "comprehensive" or feedback_type == "completeness":
                evaluations["completeness"] = self._evaluate_response_completeness(question, previous_answer, job_role)
            
            if feedback_type == "comprehensive" or feedback_type == "personalized":
                evaluations["personalized"] = self._generate_personalized_feedback(
                    job_role,
                    "mid-level",
                    ["technical knowledge", "communication"],
                    ["structuring answers", "providing examples"],
                    "visual and practical",
                    question,
                    previous_answer,
                    evaluations["star"],
                    evaluations["communication"],
                    evaluations["completeness"]
                )
            
            # Generate performance metrics if we have history
            if len(metadata.get("evaluation_history", [])) > 0:
                prev_evaluations = metadata.get("evaluation_history")
                evaluations["performance"] = self.track_performance(question, previous_answer, prev_evaluations)
            
            # Store evaluation data in history
            evaluation_record = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": previous_answer,
                "star_score": self._calculate_average_star_score(evaluations.get("star", {})),
                "communication_score": evaluations.get("communication", {}).get("overall_score", 5),
                "completeness_score": evaluations.get("completeness", {}).get("overall_score", 5)
            }
            metadata["evaluation_history"].append(evaluation_record)
            
            # Update context with feedback information
            context.update_metadata({
                "last_evaluations": evaluations,
                "feedback_type": feedback_type,
                "feedback_provided": True,
                "feedback_timestamp": datetime.now().isoformat(),
                "evaluation_history": metadata.get("evaluation_history", [])
            })
            
            # Format and return feedback using appropriate template
            return self._format_structured_feedback(evaluations, feedback_type)
        
        elif user_intent["intent"] == "ask_advice":
            # User is asking for general interview advice
            topic = user_intent.get("topic", "general")
            return self._provide_interview_advice(topic, job_role)
        
        elif user_intent["intent"] == "track_progress":
            # User wants to see their progress
            if not metadata.get("evaluation_history") or len(metadata.get("evaluation_history", [])) < 2:
                return "I don't have enough data to track your progress yet. Let's practice more interview questions first."
            
            # Generate progress report using performance metrics
            prev_evaluations = metadata.get("evaluation_history")
            performance_metrics = self.track_performance("", "", prev_evaluations)
            
            # Update context
            context.update_metadata({
                "last_progress_report": performance_metrics,
                "progress_report_timestamp": datetime.now().isoformat()
            })
            
            return self._format_progress_report(performance_metrics)
        
        elif user_intent["intent"] == "practice_question":
            # User wants to practice with a specific question type
            question_type = user_intent.get("question_type", "general")
            return self._generate_practice_question(question_type, job_role)
        
        else:
            # Default response for general conversation
            return "I'm your interview coach. I can help you practice interviews, provide feedback on your answers using the STAR method, evaluate your communication skills, track your progress, or provide general interview advice. What would you like to focus on today?"

    def _calculate_average_star_score(self, star_evaluation: Dict[str, Any]) -> float:
        """
        Calculate the average STAR method score from a STAR evaluation.
        
        Args:
            star_evaluation: STAR method evaluation dictionary
            
        Returns:
            Average score across STAR components
        """
        scores = []
        for component in ["situation", "task", "action", "result"]:
            if component in star_evaluation and "score" in star_evaluation[component]:
                scores.append(star_evaluation[component]["score"])
        
        return sum(scores) / len(scores) if scores else 5.0

    def _determine_feedback_type(self, message: str, requires_star: bool) -> str:
        """
        Determine what type of feedback to provide based on the user's message.
        
        Args:
            message: The user's message
            requires_star: Whether the answer requires STAR method evaluation
            
        Returns:
            Feedback type: "comprehensive", "star_method", "communication", "completeness", or "personalized"
        """
        message_lower = message.lower()
        
        if "comprehensive" in message_lower or "full" in message_lower or "detailed" in message_lower:
            return "comprehensive"
        elif "star" in message_lower or "situation task action result" in message_lower:
            return "star_method"
        elif "communicate" in message_lower or "clarity" in message_lower or "delivery" in message_lower:
            return "communication"
        elif "complete" in message_lower or "thorough" in message_lower or "missing" in message_lower:
            return "completeness"
        elif "personal" in message_lower or "for me" in message_lower or "my style" in message_lower:
            return "personalized"
        elif requires_star:
            return "star_method"
        else:
            return "comprehensive"

    def _requires_star_evaluation(self, question: str, answer: str) -> bool:
        """
        Determine if the question-answer pair requires STAR method evaluation.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            
        Returns:
            Boolean indicating if STAR method evaluation is appropriate
        """
        # Common behavioral question indicators
        behavioral_indicators = [
            "tell me about a time", "describe a situation", "give an example", 
            "how did you handle", "share an experience", "when have you",
            "what did you do when", "have you ever faced", "challenge you overcame"
        ]
        
        # Check if the question appears to be behavioral
        for indicator in behavioral_indicators:
            if indicator in question.lower():
                return True
        
        # If the answer is long enough, it might be a behavioral response
        if len(answer.split()) > 75:  # Assuming detailed answers are longer
            return True
        
        return False

    def _format_structured_feedback(self, evaluations: Dict[str, Any], feedback_type: str) -> Dict[str, Any]:
        """
        Format the feedback evaluations into a structured response.
        
        Args:
            evaluations: Dictionary of evaluation results
            feedback_type: Type of feedback requested
            
        Returns:
            Structured feedback dictionary
        """
        if feedback_type == "comprehensive":
            # For comprehensive feedback, include multiple sections
            response = {
                "feedback_type": "comprehensive",
                "title": "Comprehensive Interview Answer Evaluation",
                "introduction": "I've analyzed your answer from multiple perspectives. Here's my comprehensive feedback:",
                "sections": []
            }
            
            # Add STAR method section if available
            if "star" in evaluations:
                response["sections"].append(
                    self._format_feedback_section("star_method", evaluations["star"])
                )
            
            # Add communication section if available
            if "communication" in evaluations:
                response["sections"].append(
                    self._format_feedback_section("communication", evaluations["communication"])
                )
            
            # Add completeness section if available
            if "completeness" in evaluations:
                response["sections"].append(
                    self._format_feedback_section("completeness", evaluations["completeness"])
                )
            
            # Add personalized section if available
            if "personalized" in evaluations:
                personalized = evaluations["personalized"]
                response["sections"].append({
                    "title": "Your Personalized Coaching",
                    "content": personalized.get("personalized_coaching", ""),
                    "strengths": personalized.get("strengths_affirmation", []),
                    "improvements": [item.get("area", "") for item in personalized.get("growth_areas", [])],
                    "next_steps": [item.get("activity", "") for item in personalized.get("next_steps", [])]
                })
            
            # Add overall summary
            response["summary"] = self._generate_overall_summary(evaluations)
            
            return response
        else:
            # For specific feedback types, focus on just that evaluation
            template_key = feedback_type
            evaluation_key = {
                "star_method": "star",
                "communication": "communication",
                "completeness": "completeness",
                "personalized": "personalized"
            }.get(feedback_type)
            
            if evaluation_key and evaluation_key in evaluations:
                return self._format_feedback_section(template_key, evaluations[evaluation_key])
            else:
                # Fallback if the requested evaluation is not available
                return {
                    "feedback_type": "general",
                    "title": "Interview Answer Feedback",
                    "content": "I couldn't generate the specific feedback you requested. Would you like comprehensive feedback instead?"
                }

    def _format_feedback_section(self, template_key: str, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a specific feedback section based on template.
        
        Args:
            template_key: The template to use for formatting
            evaluation: The evaluation results to format
            
        Returns:
            Formatted feedback section
        """
        template = self.feedback_templates.get(template_key, {})
        if not template:
            return {
                "title": "Feedback",
                "content": "Unable to format feedback with the requested template."
            }
        
        section = {
            "title": template.get("title", "Feedback"),
            "introduction": template.get("intro", "Here's my feedback:"),
            "components": []
        }
        
        # Format each component in the template
        for component in template.get("sections", []):
            # Extract score and feedback using the keys defined in the template
            score_key = component.get("score_key", "")
            feedback_key = component.get("feedback_key", "")
            
            score = 5
            feedback = ""
            
            # Navigate nested dictionary using dot notation
            if score_key:
                keys = score_key.split('.')
                value = evaluation
                for key in keys:
                    if key in value:
                        value = value[key]
                    else:
                        value = 5
                        break
                if isinstance(value, (int, float)):
                    score = value
            
            if feedback_key:
                keys = feedback_key.split('.')
                value = evaluation
                for key in keys:
                    if key in value:
                        value = value[key]
                    else:
                        value = ""
                        break
                if isinstance(value, str):
                    feedback = value
            
            # Add to components if we have valid data
            if feedback:
                section["components"].append({
                    "name": component.get("name", "Component"),
                    "icon": component.get("icon", ""),
                    "description": component.get("description", ""),
                    "score": score,
                    "feedback": feedback
                })
        
        # Add summary and strengths/improvements sections if available
        summary_key = template.get("summary_key", "")
        strengths_key = template.get("strengths_key", "")
        improvements_key = template.get("improvements_key", "")
        
        if summary_key and summary_key in evaluation:
            section["summary"] = evaluation[summary_key]
        
        if strengths_key and strengths_key in evaluation:
            strengths = evaluation[strengths_key]
            if isinstance(strengths, list):
                section["strengths"] = strengths
            elif isinstance(strengths, str):
                section["strengths"] = [strengths]
        
        if improvements_key and improvements_key in evaluation:
            improvements = evaluation[improvements_key]
            if isinstance(improvements, list):
                section["improvements"] = improvements
            elif isinstance(improvements, str):
                section["improvements"] = [improvements]
        
        return section

    def _generate_overall_summary(self, evaluations: Dict[str, Any]) -> str:
        """
        Generate an overall summary from multiple evaluations.
        
        Args:
            evaluations: Dictionary of evaluation results
            
        Returns:
            Overall summary string
        """
        # Calculate overall scores
        scores = []
        
        if "star" in evaluations:
            star_score = self._calculate_average_star_score(evaluations["star"])
            scores.append(star_score)
        
        if "communication" in evaluations:
            comm_score = evaluations["communication"].get("overall_score", 5)
            scores.append(comm_score)
        
        if "completeness" in evaluations:
            comp_score = evaluations["completeness"].get("overall_score", 5)
            scores.append(comp_score)
        
        # Calculate average score
        avg_score = sum(scores) / len(scores) if scores else 5
        
        # Generate summary based on score
        if avg_score >= 8:
            return "Overall, your answer was excellent! You've demonstrated strong interview skills. The feedback provided can help you refine your already strong performance."
        elif avg_score >= 6:
            return "Overall, your answer was good. You've shown solid interview skills, with a few areas where you can improve further to make your responses even stronger."
        elif avg_score >= 4:
            return "Your answer was satisfactory. There are several areas where you can improve to make your responses more effective in interview situations."
        else:
            return "Your answer needs significant improvement. Focus on the feedback provided to strengthen your interview responses and make them more effective."

    def _format_progress_report(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format performance metrics into a structured progress report.
        
        Args:
            performance_metrics: Performance metrics data
            
        Returns:
            Structured progress report
        """
        return {
            "report_type": "progress",
            "title": "Your Interview Performance Progress",
            "introduction": "Here's how your interview performance has been trending:",
            "metrics_summary": performance_metrics.get("metrics_summary", {}),
            "improving_areas": performance_metrics.get("progress_tracking", {}).get("improving_areas", []),
            "focus_areas": performance_metrics.get("progress_tracking", {}).get("focus_areas", []),
            "trend_analysis": performance_metrics.get("trend_analysis", ""),
            "achievements": performance_metrics.get("achievement_badges", []),
            "recommendations": performance_metrics.get("focus_recommendations", [])
        }

    def _analyze_user_intent(self, message: str, current_state: str) -> Dict[str, Any]:
        """
        Analyze the user's message to determine their intent.
        
        Args:
            message: The user's message
            current_state: The current conversation state
            
        Returns:
            Dictionary with intent and related parameters
        """
        message_lower = message.lower()
        
        # Check for feedback request
        if any(phrase in message_lower for phrase in ["feedback", "how did i do", "evaluate", "assessment", "review my answer"]):
            return {
                "intent": "request_feedback",
                "confidence": 0.9
            }
        
        # Check for advice request
        elif any(phrase in message_lower for phrase in ["advice", "tips", "help with", "how should i", "what's the best way"]):
            # Determine specific advice topic
            topic = "general"
            if "star" in message_lower or "situation task action result" in message_lower:
                topic = "star_method"
            elif "technical" in message_lower:
                topic = "technical_interviews"
            elif "behavioral" in message_lower:
                topic = "behavioral_interviews"
            elif "question" in message_lower:
                topic = "answering_questions"
            
            return {
                "intent": "ask_advice",
                "topic": topic,
                "confidence": 0.8
            }
        
        # Check for progress tracking
        elif any(phrase in message_lower for phrase in ["progress", "improvement", "how am i doing", "track", "stats", "metrics"]):
            return {
                "intent": "track_progress",
                "confidence": 0.85
            }
        
        # Check for practice request
        elif any(phrase in message_lower for phrase in ["practice", "try", "example question", "mock interview", "give me a question"]):
            # Determine question type
            question_type = "general"
            if "technical" in message_lower:
                question_type = "technical"
            elif "behavioral" in message_lower:
                question_type = "behavioral"
            elif "case" in message_lower:
                question_type = "case_study"
            
            return {
                "intent": "practice_question",
                "question_type": question_type,
                "confidence": 0.75
            }
        
        # Default - general conversation
        return {
            "intent": "general_conversation",
            "confidence": 0.5
        }

    def _provide_interview_advice(self, topic: str, job_role: str) -> str:
        """
        Provide general interview advice on various topics.
        
        Args:
            topic: The advice topic
            job_role: The job role being applied for
            
        Returns:
            Formatted advice text
        """
        # Template store for different advice topics
        advice_templates = {
            "general": GENERAL_ADVICE_TEMPLATE.format(job_role=job_role),
            "star_method": STAR_METHOD_ADVICE_TEMPLATE
        }
        
        return advice_templates.get(topic, advice_templates["general"])

    def _generate_practice_question(self, question_type: str, job_role: str, difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generate a practice interview question based on specified parameters.
        
        Args:
            question_type: Type of interview question (e.g., "behavioral", "technical")
            job_role: The job role the question should be tailored for
            difficulty: Difficulty level of the question ("easy", "medium", "hard")
            
        Returns:
            Dictionary with the practice question information
        """
        try:
            # Format the prompt with parameters
            formatted_prompt = PRACTICE_QUESTION_PROMPT.format(
                job_role=job_role,
                difficulty=difficulty,
                question_type=question_type
            )
            
            # Call the LLM with error handling
            response = self.llm.invoke(formatted_prompt)
            
            # Parse the response
            return parse_json_with_fallback(
                json_string=response,
                default_value=self._create_default_practice_question(question_type, job_role, difficulty),
                logger=self.logger
            )
        except Exception as e:
            self.logger.error(f"Error generating practice question: {e}")
            return self._create_default_practice_question(question_type, job_role, difficulty)

    def _create_default_practice_question(self, question_type: str, job_role: str, difficulty: str) -> Dict[str, Any]:
        """
        Create a default practice question as a fallback.
        
        Args:
            question_type: Type of interview question
            job_role: The job role
            difficulty: Difficulty level
            
        Returns:
            Dictionary with default practice question
        """
        if question_type.lower() == "behavioral":
            question = "Tell me about a time when you had to overcome a significant challenge in your work."
            skills = ["problem-solving", "resilience", "adaptability"]
        elif question_type.lower() == "technical":
            question = f"What frameworks or tools do you prefer to use for {job_role} related tasks and why?"
            skills = ["technical knowledge", "critical thinking", "tool proficiency"]
        else:
            question = "Where do you see yourself professionally in five years?"
            skills = ["self-awareness", "goal-setting", "career planning"]
            
        return {
            "question": question,
            "question_type": question_type,
            "difficulty": difficulty,
            "target_skills": skills,
            "ideal_answer_points": [
                "Clear explanation of the situation",
                "Detailed description of actions taken",
                "Results or lessons learned"
            ],
            "follow_up_questions": [
                "Can you elaborate more on the impact?",
                "What would you do differently now?"
            ]
        }

    def _evaluate_star_method(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate how well a candidate applied the STAR method in their answer.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            
        Returns:
            Dictionary with STAR method evaluation results
        """
        return invoke_chain_with_error_handling(
            chain=self.star_evaluation_chain,
            inputs={"question": question, "answer": answer},
            output_key="star_evaluation",
            default_creator=self._create_default_star_evaluation,
            logger=self.logger
        )
    
    def _create_default_star_evaluation(self) -> Dict[str, Any]:
        """
        Create a default STAR method evaluation response for fallback.
        
        Returns:
            Dictionary with default STAR evaluation
        """
        return {
            "situation": {
                "score": 5,
                "feedback": "Unable to evaluate the situation component."
            },
            "task": {
                "score": 5,
                "feedback": "Unable to evaluate the task component."
            },
            "action": {
                "score": 5,
                "feedback": "Unable to evaluate the action component."
            },
            "result": {
                "score": 5,
                "feedback": "Unable to evaluate the result component."
            },
            "overall_feedback": "Unable to provide detailed feedback on STAR method application.",
            "areas_for_improvement": ["Consider structuring your answer using the STAR method."],
            "strengths": ["You provided an answer to the question."]
        }
    
    def _evaluate_communication_skills(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate a candidate's communication skills based on their answer.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            
        Returns:
            Dictionary with communication skills assessment
        """
        return invoke_chain_with_error_handling(
            chain=self.communication_assessment_chain,
            inputs={"question": question, "answer": answer},
            output_key="communication_assessment",
            default_creator=self._create_default_communication_assessment,
            logger=self.logger
        )
        
    def _evaluate_response_completeness(self, question: str, answer: str, job_role: str) -> Dict[str, Any]:
        """
        Evaluate how complete and comprehensive a candidate's answer is.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            job_role: The job role the candidate is applying for
            
        Returns:
            Dictionary with completeness evaluation results
        """
        return invoke_chain_with_error_handling(
            chain=self.completeness_evaluation_chain,
            inputs={"question": question, "answer": answer, "job_role": job_role},
            output_key="completeness_evaluation",
            default_creator=self._create_default_completeness_evaluation,
            logger=self.logger
        )
        
    def _generate_personalized_feedback(
        self, 
        job_role: str,
        experience_level: str,
        strengths: List[str],
        areas_for_improvement: List[str],
        learning_style: str,
        question: str,
        answer: str,
        star_evaluation: Dict[str, Any],
        communication_assessment: Dict[str, Any],
        response_completeness: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized feedback based on candidate profile and response evaluations.
        
        Args:
            job_role: The job role the candidate is applying for
            experience_level: The candidate's experience level
            strengths: List of candidate's strengths
            areas_for_improvement: List of candidate's areas for improvement
            learning_style: The candidate's learning style
            question: The interview question
            answer: The candidate's answer
            star_evaluation: STAR method evaluation results
            communication_assessment: Communication skills assessment
            response_completeness: Completeness evaluation results
            
        Returns:
            Dictionary with personalized feedback
        """
        return invoke_chain_with_error_handling(
            chain=self.personalized_feedback_chain,
            inputs={
                "job_role": job_role,
                "experience_level": experience_level,
                "strengths": ", ".join(strengths),
                "areas_for_improvement": ", ".join(areas_for_improvement),
                "learning_style": learning_style,
                "question": question,
                "answer": answer,
                "star_evaluation": json.dumps(star_evaluation),
                "communication_assessment": json.dumps(communication_assessment),
                "response_completeness": json.dumps(response_completeness)
            },
            output_key="personalized_feedback",
            default_creator=self._create_default_personalized_feedback,
            logger=self.logger
        )

    def _create_default_communication_assessment(self) -> Dict[str, Any]:
        """
        Create a default communication assessment for error cases.
        
        Returns:
            Default communication assessment dictionary
        """
        return {
            "clarity": {"score": 5, "feedback": "Your message was somewhat clear but could be improved."},
            "conciseness": {"score": 5, "feedback": "Your response had a reasonable length."},
            "structure": {"score": 5, "feedback": "Your response had some structure but could be more organized."},
            "engagement": {"score": 5, "feedback": "Your communication style was somewhat engaging."},
            "confidence": {"score": 5, "feedback": "You showed a moderate level of confidence."},
            "technical_terminology": {"score": 5, "feedback": "Your use of technical terms was appropriate."},
            "overall_score": 5,
            "key_strengths": ["Basic communication skills present"],
            "improvement_areas": ["Improving clarity", "Enhancing structure"],
            "practical_tips": ["Organize your thoughts before speaking", "Use transition phrases to connect ideas"]
        }

    def _create_default_completeness_evaluation(self) -> Dict[str, Any]:
        """
        Create a default completeness evaluation for error cases.
        
        Returns:
            Default completeness evaluation dictionary
        """
        return {
            "question_relevance": {"score": 5, "feedback": "Your answer was somewhat relevant to the question."},
            "key_points_coverage": {"score": 5, "feedback": "You covered some key points but missed others."},
            "examples": {"score": 5, "feedback": "You provided some examples but could include more specific ones."},
            "depth": {"score": 5, "feedback": "Your response had moderate depth."},
            "context_awareness": {"score": 5, "feedback": "Your answer showed some awareness of the role context."},
            "overall_score": 5,
            "missing_elements": ["More specific examples", "Deeper technical details"],
            "excessive_elements": ["Some tangential information"],
            "improvement_plan": "Focus more directly on answering the specific question asked, provide concrete examples, and tailor your response to the job requirements."
        }    

    def _create_default_personalized_feedback(self) -> Dict[str, Any]:
        """
        Create default personalized feedback for error cases.
        
        Returns:
            Default personalized feedback dictionary
        """
        return {
            "strengths_affirmation": [
                "You demonstrated good knowledge of the subject matter in your response.",
                "Your communication was generally clear and professional."
            ],
            "growth_areas": [
                {
                    "area": "Using the STAR method more effectively",
                    "rationale": "Structured responses help interviewers follow your experience more easily",
                    "example_from_answer": "Consider adding more specific details about the actions you took"
                },
                {
                    "area": "Providing more concrete examples",
                    "rationale": "Examples make your capabilities more tangible to interviewers",
                    "example_from_answer": "Try quantifying your results with specific metrics"
                }
            ],
            "personalized_coaching": "Focus on structuring your answers with a clear beginning, middle, and end. Start with the situation, describe the specific task you were handling, detail the actions you took, and finish with the results you achieved.",
            "improved_answer_examples": [
                {
                    "original": "I worked on a project with a team",
                    "improved": "I led a 5-person team on a critical client project where we needed to improve system performance by 30% within 3 months."
                }
            ],
            "next_steps": [
                {
                    "activity": "Practice recording yourself answering 3 common interview questions using the STAR method",
                    "benefit": "This will help you internalize the structure and identify areas for improvement"
                },
                {
                    "activity": "Create a document with 5-10 strong examples from your experience that showcase relevant skills",
                    "benefit": "This builds a library of experiences you can quickly reference during interviews"
                }
            ],
            "summary": "You're on the right track - with more structured responses and specific examples, you'll significantly strengthen your interview performance."
        }

    def track_performance(self, question: str, answer: str, 
                         previous_evaluations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Track performance over time and generate metrics.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            previous_evaluations: List of previous evaluation results
        
        Returns:
            Dictionary with performance metrics
        """
        # Default empty list if no previous evaluations
        prev_evals = previous_evaluations or []
        
        # Get current scores
        star_eval = self._evaluate_star_method(question, answer)
        comm_eval = self._evaluate_communication_skills(question, answer)
        comp_eval = self._evaluate_response_completeness(question, answer, "the position")
        
        star_score = sum([star_eval.get(k, {}).get("score", 5) for k in ["situation", "task", "action", "result"]]) / 4
        comm_score = comm_eval.get("overall_score", 5)
        comp_score = comp_eval.get("overall_score", 5)
        
        try:
            # Format previous evaluations for the chain
            prev_evals_formatted = []
            for i, eval_data in enumerate(prev_evals[-5:], 1):  # Only use last 5 evaluations
                prev_evals_formatted.append(
                    f"Evaluation {i}:\n"
                    f"- Question: {eval_data.get('question', 'Unknown')}\n"
                    f"- STAR Score: {eval_data.get('star_score', 5)}\n"
                    f"- Communication Score: {eval_data.get('communication_score', 5)}\n"
                    f"- Completeness Score: {eval_data.get('completeness_score', 5)}\n"
                )
            
            prev_evals_str = "\n".join(prev_evals_formatted) if prev_evals_formatted else "No previous evaluations available."
            
            # Generate performance metrics
            response = self.performance_metrics_chain.invoke({
                "previous_evaluations": prev_evals_str,
                "question": question,
                "answer": answer,
                "star_score": star_score,
                "communication_score": comm_score,
                "completeness_score": comp_score
            })
            
            # Parse the response
            if isinstance(response, dict) and "performance_metrics" in response:
                metrics = response["performance_metrics"]
                try:
                    if isinstance(metrics, str):
                        # Try to parse the string as JSON
                        metrics = json.loads(metrics)
                    return metrics
                except:
                    self.logger.error("Failed to parse performance metrics as JSON")
                    return self._create_default_performance_metrics()
            else:
                return self._create_default_performance_metrics()
        except Exception as e:
            self.logger.error(f"Error tracking performance: {e}")
            return self._create_default_performance_metrics()

    def _create_default_performance_metrics(self) -> Dict[str, Any]:
        """
        Create default performance metrics for error cases.
        
        Returns:
            Default performance metrics dictionary
        """
        return {
            "metrics_summary": {
                "star_score": {
                    "current": 5,
                    "previous_avg": 5,
                    "delta": 0
                },
                "communication_score": {
                    "current": 5,
                    "previous_avg": 5,
                    "delta": 0
                },
                "completeness_score": {
                    "current": 5,
                    "previous_avg": 5,
                    "delta": 0
                },
                "overall_score": {
                    "current": 5,
                    "previous_avg": 5,
                    "delta": 0
                }
            },
            "progress_tracking": {
                "improving_areas": [
                    {
                        "area": "Overall structure",
                        "evidence": "You're starting to use more elements of the STAR method"
                    }
                ],
                "focus_areas": [
                    {
                        "area": "Providing specific examples",
                        "rationale": "Your answers would benefit from more concrete details"
                    }
                ]
            },
            "trend_analysis": "Your performance is steady. Continue practicing structured responses and adding specific examples to see more improvement.",
            "achievement_badges": [
                {
                    "badge": "Consistent Performer",
                    "description": "Maintaining a steady level of interview performance"
                }
            ],
            "focus_recommendations": [
                "Practice the STAR method with 3-5 specific examples from your experience",
                "Record yourself answering questions to review your communication style"
            ]
        }    

    def _generate_practice_question_tool(self, question_type: str, job_role: str = None) -> str:
        """
        Generate a practice interview question as a tool function.
        
        Args:
            question_type: Type of interview question (behavioral, technical, etc.)
            job_role: Job role to tailor the question for (defaults to role in context)
            
        Returns:
            Formatted practice question with instructions
        """
        if job_role is None:
            job_role = self.context.job_role if hasattr(self.context, "job_role") else "professional"
            
        try:
            question_data = self._generate_practice_question(question_type, job_role)
            
            # Format the response as a string
            instructions = ""
            if question_type.lower() == "behavioral":
                instructions = "Use the STAR method (Situation, Task, Action, Result) to structure your answer."
            elif question_type.lower() == "technical":
                instructions = "Explain your thought process clearly and consider different approaches."
            elif question_type.lower() == "case_study":
                instructions = "Consider various perspectives including technical feasibility, business impact, and user experience."
            else:
                instructions = "Keep your answer concise, authentic, and relevant to the role you're applying for."
            
            # Format target skills as a comma-separated list
            target_skills = ", ".join(question_data.get("target_skills", []))
            
            # Format ideal answer points as a bullet list
            ideal_points = "\n".join([f"- {point}" for point in question_data.get("ideal_answer_points", [])])
            
            return PRACTICE_QUESTION_RESPONSE_TEMPLATE.format(
                question_type=question_data.get('question_type', '').title(),
                question=question_data.get('question', 'No question generated'),
                instructions=instructions,
                target_skills=target_skills,
                ideal_points=ideal_points
            )
        except Exception as e:
            self.logger.error(f"Error formatting practice question: {e}")
            return f"I'm having trouble generating a practice question. Please try again with a different question type or job role."    
    
    def _handle_interviewer_message(self, event: Event) -> None:
        """
        Handle messages from the interviewer agent.
        
        Args:
            event: The event containing the interviewer's message
        """
        if not event.data or "message" not in event.data:
            return
        
        # Extract the message and check if it's a question
        message = event.data.get("message", "")
        is_question = event.data.get("is_question", False)
        
        if is_question:
            # Store the current question for later use in feedback
            self.current_question = message
            
            # Reset current answer since we have a new question
            self.current_answer = None
            
            # If in real-time coaching mode, we could prepare initial guidance
            if self.coaching_mode == CoachingMode.REAL_TIME:
                # Analyze question to determine type and difficulty
                question_analysis = self._analyze_question_type(message)
                
                # Store metadata for later use
                if not hasattr(self, 'context'):
                    self.context = {}
                
                self.context["current_question_analysis"] = question_analysis
                
                # For targeted coaching mode, we might send preliminary advice
                if self.coaching_mode == CoachingMode.TARGETED:
                    # Check if the question type matches our focus areas
                    question_type = question_analysis.get("question_type", "")
                    
                    if any(focus in question_type.lower() for focus in self.coaching_focus):
                        # Send preliminary advice if available
                        self._send_preliminary_advice(message, question_analysis)
    
    def _handle_user_message(self, event: Event) -> None:
        """
        Handle messages from the user.
        
        Args:
            event: The event containing the user's message
        """
        if not event.data or "message" not in event.data:
            return
        
        # Extract the message
        message = event.data.get("message", "")
        
        # Store the current answer for later use in feedback
        self.current_answer = message
        
        # If in real-time coaching mode, provide immediate feedback
        if self.coaching_mode == CoachingMode.REAL_TIME and self.current_question:
            # Generate and send feedback
            feedback = self._analyze_response_tool(self.current_question, message)
                
                # Publish feedback event
            if self.event_bus:
                self.event_bus.publish(Event(
                    event_type="coach_feedback",
                    source="coach_agent",
                data={
                "feedback": feedback,
                "question": self.current_question,
                "answer": message,
                "timestamp": datetime.now().isoformat()
                }
                ))

    def _handle_interview_summary(self, event: Event) -> None:
        """
        Handle interview summary events.
        
        Args:
            event: The event containing the interview summary
        """
        if not event.data or "summary" not in event.data:
            return
        
        # Extract the summary
        summary = event.data.get("summary", "")
        qa_pairs = event.data.get("qa_pairs", [])
        
        # Generate coaching summary
        if qa_pairs:
            coaching_summary = self._create_coaching_summary_tool(summary, qa_pairs)
            
            # Publish coaching summary event
            if self.event_bus:
                self.event_bus.publish(Event(
                    event_type="coaching_summary",
                    source="coach_agent",
                    data={
                        "coaching_summary": coaching_summary,
                        "timestamp": datetime.now().isoformat()
                    }
                ))
    
    def _handle_coaching_request(self, event: Event) -> None:
        """
        Handle explicit requests for coaching.
        
        Args:
            event: The event containing the coaching request
        """
        if not event.data:
            return
        
        # Extract the request type and related data
        request_type = event.data.get("request_type", "")
        
        if request_type == "feedback":
            # Handle feedback request
            question = event.data.get("question", "")
            answer = event.data.get("answer", "")
            
            if question and answer:
                feedback = self._analyze_response_tool(question, answer)
                
                # Publish feedback event
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type="coach_feedback",
                        source="coach_agent",
                        data={
                            "feedback": feedback,
                            "question": question,
                            "answer": answer,
                            "timestamp": datetime.now().isoformat()
                        }
                    ))
        
        elif request_type == "template":
            # Handle template request
            question_type = event.data.get("question_type", "")
            example_question = event.data.get("example_question", "")
            job_role = event.data.get("job_role", "")
            
            if question_type and job_role:
                template = self._generate_response_template_tool(question_type, example_question, job_role)
                
                # Publish template event
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type="response_template",
                        source="coach_agent",
                        data={
                            "template": template,
                            "question_type": question_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    ))
        
        elif request_type == "practice_question":
            # Handle practice question request
            question_type = event.data.get("question_type", "")
            job_role = event.data.get("job_role", "")
            
            if question_type:
                practice_question = self._generate_practice_question_tool(question_type, job_role)
                
                # Publish practice question event
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type="practice_question",
                        source="coach_agent",
                        data={
                            "practice_question": practice_question,
                            "question_type": question_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    ))

    def _analyze_question_type(self, question: str) -> Dict[str, Any]:
        """
        Analyze a question to determine its type and characteristics.
        
        Args:
            question: The interview question to analyze
        
        Returns:
            Dictionary with question analysis
        """
        # Simple rule-based analysis for common question types
        question_lower = question.lower()
        
        # Default analysis
        analysis = {
            "question_type": "general",
            "difficulty": "medium",
            "requires_star": False,
            "focus_areas": []
        }
        
        # Check for behavioral questions
        behavioral_indicators = [
            "tell me about a time", "describe a situation", "give an example", 
            "how did you handle", "share an experience", "when have you"
        ]
        if any(indicator in question_lower for indicator in behavioral_indicators):
            analysis["question_type"] = "behavioral"
            analysis["requires_star"] = True
            analysis["focus_areas"].append("storytelling")
        
        # Check for technical questions
        technical_indicators = [
            "how would you implement", "explain how", "what is the difference between",
            "how does", "what are the principles of", "describe the process"
        ]
        if any(indicator in question_lower for indicator in technical_indicators):
            analysis["question_type"] = "technical"
            analysis["focus_areas"].append("technical_knowledge")
        
        # Check for hypothetical questions
        hypothetical_indicators = [
            "what would you do if", "how would you approach", "if you were faced with"
        ]
        if any(indicator in question_lower for indicator in hypothetical_indicators):
            analysis["question_type"] = "hypothetical"
            analysis["focus_areas"].append("problem_solving")
        
        # Check for strengths/weaknesses questions
        if "strength" in question_lower or "weakness" in question_lower or "improve" in question_lower:
            analysis["question_type"] = "self_assessment"
            analysis["focus_areas"].append("self_awareness")
        
        # Estimate difficulty
        complex_indicators = ["complex", "difficult", "challenging", "advanced", "detailed"]
        if any(indicator in question_lower for indicator in complex_indicators) or len(question.split()) > 25:
            analysis["difficulty"] = "hard"
        elif len(question.split()) < 10:
            analysis["difficulty"] = "easy"
        
        return analysis

    def _send_preliminary_advice(self, question: str, question_analysis: Dict[str, Any]) -> None:
        """
        Send preliminary advice for a question before the user answers.
        
        Args:
            question: The interview question
            question_analysis: Analysis of the question
        """
        if not self.event_bus:
            return
        
        question_type = question_analysis.get("question_type", "")
        requires_star = question_analysis.get("requires_star", False)
        
        advice = ""
        if requires_star:
            advice = "This appears to be a behavioral question. Consider using the STAR method in your response."
        elif question_type == "technical":
            advice = "This is a technical question. Be specific and showcase both your knowledge and practical experience."
        elif question_type == "hypothetical":
            advice = "For this hypothetical scenario, explain your thought process and the steps you would take."
        elif question_type == "self_assessment":
            advice = "When discussing strengths or weaknesses, be honest but strategic. For weaknesses, show how you're working to improve."
        
        if advice:
            self.event_bus.publish(Event(
                event_type="preliminary_advice",
                source="coach_agent",
                data={
                    "advice": advice,
                    "question": question,
                    "timestamp": datetime.now().isoformat()
                }
            ))    
