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
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain

try:
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import Event, EventBus
    from backend.services.llm_service import LLMService
    from backend.agents.templates.coach_templates import (
        TIPS_TEMPLATE,
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
    from backend.utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback
    )
except ImportError:
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import Event, EventBus
    from ..services.llm_service import LLMService
    from .templates.coach_templates import (
        TIPS_TEMPLATE,
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
    from ..utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback
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
    
    DEFAULT_COACHING_FOCUS = [
        CoachingFocus.COMMUNICATION,
        CoachingFocus.CONTENT,
        CoachingFocus.CONFIDENCE,
        CoachingFocus.SPECIFICITY,
        CoachingFocus.STORYTELLING
    ]
    
    def __init__(
        self,
        llm_service: LLMService,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        coaching_focus: Optional[List[str]] = None,
        feedback_verbosity: str = "detailed"
    ):
        """
        Initialize the coach agent for post-interview feedback.
        
        Args:
            llm_service: Language model service instance.
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            coaching_focus: List of areas to focus coaching on (defaults defined in DEFAULT_COACHING_FOCUS)
            feedback_verbosity: Level of detail in feedback (brief, moderate, detailed)
        """
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.coaching_focus = coaching_focus or self.DEFAULT_COACHING_FOCUS
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
        # System prompt is now static as mode/focus are less dynamic
        return SYSTEM_PROMPT
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Improvement tips chain
        self.tips_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(TIPS_TEMPLATE),
            output_key="tips"
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
        
        # Performance analysis chain (For overall structured analysis)
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
        
        # Store structured feedback templates dictionary
        self.feedback_templates = FEEDBACK_TEMPLATES
    
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
        Stores the current question asked by the interviewer.
        
        Args:
            event: The event containing the interviewer's message
        """
        if not event.data or "question" not in event.data: # Assuming interviewer event sends 'question' key
            self.logger.warning("Received interviewer event without 'question' data.")
            return
        
        # Store the current question for later analysis context
        self.current_question = event.data.get('response', {}).get("content", "")
        self.logger.debug(f"Stored current question: {self.current_question[:100]}...")
            
            # Reset current answer since we have a new question
        self.current_answer = None
            
    
    def _handle_user_message(self, event: Event) -> None:
        """
        Stores the user's latest answer for later analysis.        
        Args:
            event: The event containing the user's message
        """
        if not event.data or "message" not in event.data: # Assuming user event sends 'message'
            self.logger.warning("Received user event without 'message' data.")
            return
        
        # Store the current answer for later analysis context
        self.current_answer = event.data.get('message', {}).get("content", "")
        self.logger.debug(f"Stored current answer: {self.current_answer[:100]}...")
    
    def _handle_interview_summary(self, event: Event) -> None:
        """
        Handles the signal that the interview has concluded.
        Triggers the generation and publishing of a comprehensive performance analysis.
        
        Args:
            event: The event containing interview summary data (e.g., Q&A pairs)
        """
        self.logger.info("Received interview_summary event. Generating final coaching analysis.")
        if not event.data:
            self.logger.error("Interview summary event received with no data.")
            return
        
        # Extract necessary data - requires clarity on what interviewer_summary event provides.
        # Assuming it provides a list of qa_pairs like [{'question': q_text, 'answer': a_text}, ...]
        # and potentially overall context/metrics from the InterviewerAgent (like job_role, style etc.)
        # For now, let's assume we have access to stored Q&A or need to accumulate them.
        # TODO: Refine based on actual event data structure.

        # Placeholder: Accumulate Q&A pairs if not provided directly in the event
        # This assumes handle_interviewer_message and handle_user_message are called consistently.
        # A better approach might be to have the InterviewerAgent pass the full transcript.
        if not hasattr(self, 'qa_pairs_history'):
             self.qa_pairs_history = [] # Initialize if doesn't exist
        if self.current_question and self.current_answer:
             self.qa_pairs_history.append({"question": self.current_question, "answer": self.current_answer})
             self.logger.debug(f"Added Q/A pair to history. Total pairs: {len(self.qa_pairs_history)}")

        # Use accumulated history for analysis
        qa_pairs_for_analysis = getattr(self, 'qa_pairs_history', [])

        if not qa_pairs_for_analysis:
             self.logger.warning("No Q&A pairs available to generate coaching summary.")
             # Optionally publish an event indicating coaching couldn't be generated
             return

        try:
            # Option 1: Generate comprehensive performance analysis using PERFORMANCE_ANALYSIS_TEMPLATE
            # This requires preparing the input 'analyses_json' which means running individual evaluations first.
            # This might be too complex/slow for a single event handler.

            # Option 2: Generate personalized feedback based on the last Q&A (Simpler, but less comprehensive)
            # last_qa = qa_pairs_for_analysis[-1]
            # feedback = self._generate_personalized_feedback(...) # Needs profile info

            # Option 3: Generate metrics tracking progress (requires previous sessions)
            # performance_metrics = self.track_performance(...) # Needs history

            # Let's choose a simpler approach for now: Perform STAR/Comm/Complete on the LAST answer
            # and provide that structured feedback as the initial post-interview summary.
            # A more advanced implementation could run evaluations iteratively or use PERFORMANCE_ANALYSIS.

            last_q = qa_pairs_for_analysis[-1]["question"]
            last_a = qa_pairs_for_analysis[-1]["answer"]

            evaluations = {}
            job_role = "[Not Provided]" # TODO: Get job role from context or event data
            requires_star = self._requires_star_evaluation(last_q, last_a)

            if requires_star:
                evaluations["star"] = self._evaluate_star_method(last_q, last_a)
            evaluations["communication"] = self._evaluate_communication_skills(last_q, last_a)
            evaluations["completeness"] = self._evaluate_response_completeness(last_q, last_a, job_role)

            # Format the feedback (using comprehensive to show all available evals for the last Q)
            formatted_feedback = self._format_structured_feedback(evaluations, "comprehensive")
            # Add a note that this is based on the last answer primarily
            formatted_feedback["note"] = "This initial summary focuses on your last response. Further analysis can be requested."
            
            # Publish coaching summary event
            if self.event_bus:
                self.event_bus.publish(Event(
                    event_type="coaching_summary_generated",
                    source="coach_agent",
                    data={
                        "coaching_results": formatted_feedback, # Send structured data
                        "timestamp": datetime.now().isoformat()
                    }
                ))
            self.logger.info("Published initial post-interview coaching summary based on last answer.")

            # Reset history for next potential interview
            self.qa_pairs_history = []

        except Exception as e:
            self.logger.exception(f"Error generating post-interview coaching summary: {e}")
            # Publish error event?
    
    def _handle_coaching_request(self, event: Event) -> None:
        """
        Handle explicit requests for coaching actions (post-interview).
        Focuses on providing specific evaluation types or resources.
        
        Args:
            event: The event containing the coaching request
        """
        if not event.data:
            self.logger.warning("Received coaching request event with no data.")
            return
        
        request_type = event.data.get("request_type", "").lower()
        self.logger.info(f"Handling coaching request of type: {request_type}")

        response_data = None
        response_event_type = "coaching_response" # Default event type

        try:
            # Get common data potentially needed
            question = event.data.get("question", self.current_question) # Use context if available
            answer = event.data.get("answer", self.current_answer)
            job_role = event.data.get("job_role", "[Not Provided]")
            # Candidate profile would ideally come from context/event
            candidate_profile = event.data.get("candidate_profile", {
                "experience_level": "mid-level", 
                "strengths": list(getattr(self, 'strength_areas', [])),
                "areas_for_improvement": list(getattr(self, 'improvement_areas', [])),
                "learning_style": "visual"
            })

            # --- Specific Feedback Requests --- 
            if request_type in ["star", "star_method", "star_feedback"]:
                if question and answer:
                    response_data = self._evaluate_star_method(question, answer)
                    response_event_type = "coach_feedback_response"
                else:
                    response_data = {"message": "Missing question or answer for STAR feedback request."}
            
            elif request_type in ["communication", "comm_feedback"]:
                if question and answer:
                    response_data = self._evaluate_communication_skills(question, answer)
                    response_event_type = "coach_feedback_response"
                else:
                    response_data = {"message": "Missing question or answer for Communication feedback request."}

            elif request_type in ["completeness", "complete_feedback"]:
                if question and answer:
                    response_data = self._evaluate_response_completeness(question, answer, job_role)
                    response_event_type = "coach_feedback_response"
                else:
                    response_data = {"message": "Missing question or answer for Completeness feedback request."}

            elif request_type in ["personalized", "personal_feedback"]:
                if question and answer:
                     # Need to run dependent evals first
                     star_eval = self._evaluate_star_method(question, answer) if self._requires_star_evaluation(question, answer) else {}
                     comm_eval = self._evaluate_communication_skills(question, answer)
                     comp_eval = self._evaluate_response_completeness(question, answer, job_role)
                     response_data = self._generate_personalized_feedback(\
                         job_role, candidate_profile["experience_level"], candidate_profile["strengths"], \
                         candidate_profile["areas_for_improvement"], candidate_profile["learning_style"], \
                         question, answer, star_eval, comm_eval, comp_eval\
                     )
                     response_event_type = "coach_feedback_response"
                else:
                     response_data = {"message": "Missing question or answer for Personalized feedback request."}

            # --- Other Coaching Actions --- 
            elif request_type == "tips":
                focus_area = event.data.get("focus_area", random.choice(self.DEFAULT_COACHING_FOCUS))
                context_summary = event.data.get("context", "Based on recent interview practice") # Need context
                tips_text = self._generate_improvement_tips_tool(focus_area, context_summary)
                response_data = {"tips": tips_text, "focus_area": focus_area}
                response_event_type = "coaching_tips_response"

            elif request_type == "template":
                question_type = event.data.get("question_type", "behavioral")
                example_question = event.data.get("example_question", "Tell me about a time you dealt with conflict.")
                template_text = self._generate_response_template_tool(question_type, example_question, job_role)
                response_data = {"template": template_text, "question_type": question_type}
                response_event_type = "response_template_response"
        
            elif request_type == "practice_question":
                question_type = event.data.get("question_type", "behavioral")
                difficulty = event.data.get("difficulty", "medium")
                practice_question_data = self._generate_practice_question(question_type, job_role, difficulty)
                practice_question_formatted = self._format_practice_question_response(practice_question_data)
                response_data = {"practice_question": practice_question_formatted, "question_data": practice_question_data}
                response_event_type = "practice_question_response"

            elif request_type == "advice":
                topic = event.data.get("topic", "general")
                advice_text = self._provide_interview_advice(topic, job_role)
                response_data = {"advice": advice_text, "topic": topic}
                response_event_type = "coaching_advice_response"
            
            elif request_type == "progress":
                # Assuming history is stored somewhere accessible 
                prev_evals = getattr(self, 'evaluation_history', []) 
                if len(prev_evals) > 0:
                    # Note: track_performance needs Q/A - this might need redesign or fetch last Q/A
                    metrics_data = self.track_performance("", "", prev_evals) 
                    response_data = self._format_progress_report(metrics_data)
                    response_event_type = "progress_report_response"
                else:
                    response_data = {"message": "Not enough history to generate a progress report."}

            else:
                self.logger.warning(f"Received unknown coaching request type: {request_type}")
                response_data = {"message": f"Unknown coaching request type: {request_type}. Try: feedback, tips, template, practice_question, advice, progress.", "available_requests": ["feedback", "tips", "template", "practice_question", "advice", "progress"]}

        except Exception as e:
             self.logger.exception(f"Error handling coaching request '{request_type}': {e}")
             response_data = {"error": f"Failed to handle request '{request_type}'.", "details": str(e)}

        # Publish response event
        if self.event_bus and response_data:
            self.event_bus.publish(Event(\
                event_type=response_event_type,\
                source="coach_agent",\
                data={\
                    "response": response_data,\
                    "original_request": event.data, # Echo request for context\
                    "timestamp": datetime.now().isoformat()\
                }\
            ))
            self.logger.info(f"Published response for coaching request type: {request_type}")

    # Helper to format practice question response (internal use)
    def _format_practice_question_response(self, question_data: Dict[str, Any]) -> str:
        """ Formats the practice question JSON into a user-readable string. """
        instructions = ""
        question_type = question_data.get('question_type', 'general')
        if question_type.lower() == "behavioral":
            instructions = "Use the STAR method (Situation, Task, Action, Result) to structure your answer."
        elif question_type.lower() == "technical":
            instructions = "Explain your thought process clearly and consider different approaches."
        else:
            instructions = "Keep your answer concise, authentic, and relevant."

        target_skills = ", ".join(question_data.get("target_skills", []))
        ideal_points = "\n".join([f"- {point}" for point in question_data.get("ideal_answer_points", [])])
        
        return PRACTICE_QUESTION_RESPONSE_TEMPLATE.format(
            question_type=question_data.get('question_type', '').title(),
            question=question_data.get('question', 'No question generated'),
            instructions=instructions,
            target_skills=target_skills,
            ideal_points=ideal_points
        )

    def _analyze_question_type(self, question: str) -> Dict[str, Any]:
        """ # Keep this helper as it might be useful for deciding which evaluation to run
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

    def generate_coaching_summary(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generates a comprehensive coaching summary based on the entire interview context.
        This is typically called at the end of an interview session.

        Args:
            context: The AgentContext containing the full conversation history and config.

        Returns:
            A dictionary containing the structured coaching summary.
        """
        self.logger.info("Generating final coaching summary for the interview session.")
        
        full_history = context.conversation_history
        qa_pairs = []
        current_q = None
        for msg in full_history:
            role = msg.get("role")
            content = msg.get("content")
            # Heuristic: Assume assistant messages from 'interviewer' are questions
            if role == "assistant" and msg.get("agent") == "interviewer":
                current_q = content
            elif role == "user" and current_q is not None:
                qa_pairs.append({"question": current_q, "answer": content})
                current_q = None # Reset question after getting an answer
        
        if not qa_pairs:
             self.logger.warning("No complete Q&A pairs found in history to generate coaching summary.")
             return {"error": "Could not generate summary due to missing Q&A pairs."}

        # --- Perform analysis on all Q&A pairs (This can be computationally expensive) ---
        # For simplicity here, we'll analyze the LAST pair as a representative sample.
        # A full implementation might iterate, use specific chains, or use the PERFORMANCE_ANALYSIS_TEMPLATE.
        # TODO: Enhance this to analyze more than just the last pair for a true summary.
        
        try:
            last_q = qa_pairs[-1]["question"]
            last_a = qa_pairs[-1]["answer"]

            evaluations = {}
            job_role = context.session_config.job_role or "[Not Provided]"
            requires_star = self._requires_star_evaluation(last_q, last_a)

            if requires_star:
                evaluations["star"] = self._evaluate_star_method(last_q, last_a)
            evaluations["communication"] = self._evaluate_communication_skills(last_q, last_a)
            evaluations["completeness"] = self._evaluate_response_completeness(last_q, last_a, job_role)

            # Format the feedback
            formatted_feedback = self._format_structured_feedback(evaluations, "comprehensive")
            formatted_feedback["note"] = "This summary is based on an analysis of the final interaction. A more comprehensive analysis could be performed."
            
            # Publish an event (optional, could be done by caller)
            # self.publish_event(EventType.COACH_ANALYSIS, {"coaching_summary": formatted_feedback})
            
            self.logger.info("Generated coaching summary successfully (based on last Q&A).")
            return formatted_feedback
            
        except Exception as e:
            self.logger.exception(f"Error generating coaching summary: {e}")
            return {"error": f"Failed to generate coaching summary: {e}"}

    def _handle_session_start(self, event: Event) -> None:
        """
        Handles the session start event, potentially resetting state or loading config.
        """
        # Reset internal state related to a specific interview
        self.logger.info(f"CoachAgent handling {event.event_type} event.")
        self.interview_session_id = event.data.get("session_id", "unknown") # Example: If session ID is in event
        self.current_question = None
        self.current_answer = None
        self.interview_performance = {}
        self.improvement_areas = set()
        self.strength_areas = set()
        self.qa_pairs_history = [] # Reset Q&A history if used

        # Update config from event if provided
        if event.data and 'config' in event.data:
            config_data = event.data['config']
            self.logger.info(f"CoachAgent updating config from SESSION_START event: {config_data}")
            # Assuming config_data is a dict-like representation of SessionConfig
            self.coaching_focus = config_data.get('coaching_focus', self.DEFAULT_COACHING_FOCUS) # Example update
            # Update other relevant config attributes if needed by the coach
            # self.feedback_verbosity = config_data.get('feedback_verbosity', "detailed") 
            # Note: job_role isn't directly stored but used in methods, fetched from context when needed.

        self.logger.debug("CoachAgent state reset for new session.")
            
    def process(self, context: AgentContext) -> Any:
        """
        Process the current context and generate coaching feedback.
        This is the main entry point required by BaseAgent.
        
        Args:
            context: The current AgentContext containing history, config, etc.
            
        Returns:
            Dictionary with coaching results
        """
        self.logger.info("CoachAgent process method called with context")
        
        # Extract the most recent question-answer pair if available
        last_question = None
        last_answer = None
        
        for i in range(len(context.conversation_history) - 1, 0, -1):
            msg = context.conversation_history[i]
            if msg.get("role") == "user" and last_answer is None:
                last_answer = msg.get("content")
            elif msg.get("role") == "assistant" and last_answer is not None and last_question is None:
                last_question = msg.get("content")
                break
        
        if last_question and last_answer:
            self.current_question = last_question
            self.current_answer = last_answer
            
            # Determine what type of feedback to provide
            requires_star = self._requires_star_evaluation(last_question, last_answer)
            feedback_type = self._determine_feedback_type(last_answer, requires_star)
            
            # Generate appropriate evaluations
            evaluations = {}
            if feedback_type in ["comprehensive", "star_method"] or requires_star:
                evaluations["star"] = self._evaluate_star_method(last_question, last_answer)
            
            if feedback_type in ["comprehensive", "communication"]:
                evaluations["communication"] = self._evaluate_communication_skills(last_question, last_answer)
            
            if feedback_type in ["comprehensive", "completeness"]:
                job_role = context.session_config.job_role if hasattr(context.session_config, "job_role") else "professional"
                evaluations["completeness"] = self._evaluate_response_completeness(last_question, last_answer, job_role)
            
            # Format the results into a structured response
            return self._format_structured_feedback(evaluations, feedback_type)
        
        # No question-answer pair found - return a placeholder response
        return {
            "feedback_type": "status",
            "message": "No interview data available to analyze. Please complete at least one question-answer exchange."
        }
            
