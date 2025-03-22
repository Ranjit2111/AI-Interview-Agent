"""
Coach agent module for providing feedback and guidance to users during interview preparation.
This agent analyzes interview performance and offers personalized advice for improvement.
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

from backend.agents.base import BaseAgent, AgentContext
from backend.utils.event_bus import Event, EventBus


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
        return (
            "You are an expert interview coach with years of experience helping candidates "
            "succeed in job interviews. Your goal is to provide constructive, actionable "
            "feedback to help the candidate improve their interview performance. "
            f"You're currently operating in {self.coaching_mode} mode. "
            f"Your focus areas are: {', '.join(self.coaching_focus)}. "
            "Be supportive but honest, highlighting both strengths and areas for improvement."
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
            )
        ]
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Response analysis chain
        analysis_template = """
        You are an expert interview coach analyzing a candidate's response to an interview question.
        
        Question: {question}
        Candidate's Response: {response}
        
        Analyze the response on the following dimensions:
        1. Content relevance (How well did they answer what was asked?)
        2. Structure (How well organized was the response?)
        3. Communication clarity (How clearly did they express their points?)
        4. Use of examples (Did they provide specific, relevant examples?)
        5. Brevity vs. detail (Was the response appropriately detailed?)
        6. Confidence indicators (What does their language suggest about confidence?)
        
        Focus especially on these areas: {focus_areas}
        
        Provide a balanced assessment highlighting strengths and areas for improvement.
        """
        
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(analysis_template),
            output_key="analysis"
        )
        
        # Improvement tips chain
        tips_template = """
        You are an expert interview coach helping a candidate improve their interview performance.
        
        Focus area: {focus_area}
        Context: {context}
        
        Provide 3-5 specific, actionable tips to help the candidate improve in this area.
        Each tip should include:
        1. A clear instruction
        2. The rationale behind it
        3. A brief example of how to implement it
        
        Make your advice practical and immediately applicable in their next response.
        """
        
        self.tips_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(tips_template),
            output_key="tips"
        )
        
        # Coaching summary chain
        summary_template = """
        You are an expert interview coach creating a comprehensive coaching summary for a candidate.
        
        Interview Context: {interview_context}
        Question-Answer Pairs: {qa_pairs}
        
        Create a comprehensive coaching summary that includes:
        1. Overall assessment of interview performance
        2. Key strengths demonstrated throughout the interview
        3. Primary areas for improvement
        4. 3-5 specific, actionable recommendations for future interviews
        5. A brief motivational conclusion
        
        Focus especially on these areas: {focus_areas}
        
        Be constructive and supportive while providing honest feedback.
        """
        
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(summary_template),
            output_key="coaching_summary"
        )
        
        # Response template chain
        template_prompt = """
        You are an expert interview coach creating a template for effectively answering a specific type of interview question.
        
        Question type: {question_type}
        Example question: {example_question}
        Candidate's job role: {job_role}
        
        Create a response template that includes:
        1. Recommended structure for this type of question
        2. Key components to include
        3. Common pitfalls to avoid
        4. A brief example of a strong response
        
        The template should be adaptable to various specific questions of this type.
        """
        
        self.template_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(template_prompt),
            output_key="response_template"
        )
        
        # Create STAR method evaluation chain
        star_evaluation_template = """
        You are an expert interview coach evaluating a candidate's use of the STAR method.
        
        Question: {question}
        Answer: {answer}
        
        Evaluate how well the candidate applied the STAR method using the following criteria:
        - Situation: Did they clearly describe the context/background?
        - Task: Did they explain their specific role or responsibility?
        - Action: Did they detail the steps they took?
        - Result: Did they quantify the outcome or explain the impact?
        
        For each component (Situation, Task, Action, Result), rate on a scale of 0-10 and explain why.
        
        Format your response as JSON:
        {
            "situation": {
                "score": score_from_0_to_10,
                "feedback": "specific feedback on situation description"
            },
            "task": {
                "score": score_from_0_to_10,
                "feedback": "specific feedback on task description"
            }, 
            "action": {
                "score": score_from_0_to_10,
                "feedback": "specific feedback on action description"
            },
            "result": {
                "score": score_from_0_to_10,
                "feedback": "specific feedback on result description"
            },
            "overall_feedback": "summary of overall STAR method application",
            "areas_for_improvement": ["specific suggestion 1", "specific suggestion 2"],
            "strengths": ["strength 1", "strength 2"]
        }
        """
        
        self.star_evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(star_evaluation_template),
            output_key="star_evaluation"
        )
        
        # Performance analysis chain
        performance_analysis_template = """
        You are an expert interview coach analyzing a candidate's interview performance over multiple questions.
        
        Review the following response analyses from the interview session:
        {analyses_json}
        
        TASK: Provide a comprehensive performance analysis with patterns, trends, and actionable insights.
        
        Your analysis should include:
        1. Overall Performance Summary: General assessment across all responses
        2. Pattern Recognition: Recurring strengths and weaknesses across responses
        3. Progression Analysis: Any improvement or decline in performance during the session
        4. Skill Assessment: Evaluation of key interview skills (STAR method, communication, specificity, etc.)
        5. Priority Improvement Areas: The 2-3 most critical areas to focus on improving
        6. Actionable Development Plan: Specific exercises and practices for improvement
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "overall_summary": "Comprehensive summary of performance",
            "patterns": {{
                "strengths": ["Pattern 1", "Pattern 2", ...],
                "weaknesses": ["Pattern 1", "Pattern 2", ...]
            }},
            "progression": "Analysis of improvement/decline during session",
            "skill_assessment": {{
                "star_method": {{
                    "score": <0-10>,
                    "assessment": "Evaluation of STAR method usage"
                }},
                "communication": {{
                    "score": <0-10>,
                    "assessment": "Evaluation of communication skills"
                }},
                "content_quality": {{
                    "score": <0-10>,
                    "assessment": "Evaluation of answer content"
                }},
                "specificity": {{
                    "score": <0-10>,
                    "assessment": "Evaluation of specific examples"
                }}
            }},
            "priority_improvement_areas": ["Area 1", "Area 2", "Area 3"],
            "development_plan": [
                {{
                    "focus_area": "Area 1",
                    "exercises": ["Exercise 1", "Exercise 2"],
                    "resources": ["Resource 1", "Resource 2"]
                }},
                ...
            ]
        }}
        """
        
        self.performance_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(performance_analysis_template),
            output_key="performance_analysis"
        )
        
        # Create communication skills assessment chain
        communication_assessment_template = """
        You are an expert interview coach evaluating a candidate's communication skills in their interview response.
        
        Question: {question}
        Candidate's Response: {answer}
        
        TASK: Evaluate the candidate's communication skills across multiple dimensions.
        
        Assess the following areas on a scale of 0-10 with specific feedback:
        - Clarity: How clear and understandable was their communication?
        - Conciseness: Did they communicate efficiently without unnecessary details?
        - Structure: How well-organized was their response?
        - Engagement: How engaging and compelling was their communication style?
        - Confidence: How confident did they appear through their word choice and phrasing?
        - Technical Terminology: How appropriate was their use of technical terms (if applicable)?
        
        Additionally, provide:
        - Overall Communication Score (0-10): A weighted assessment across all dimensions
        - Key Strengths: Communication aspects they handled well
        - Improvement Areas: Specific communication aspects they should work on
        - Practical Tips: 2-3 actionable suggestions to improve their communication
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "clarity": {{
                "score": <0-10>,
                "feedback": "<specific clarity feedback>"
            }},
            "conciseness": {{
                "score": <0-10>,
                "feedback": "<specific conciseness feedback>"
            }},
            "structure": {{
                "score": <0-10>,
                "feedback": "<specific structure feedback>"
            }},
            "engagement": {{
                "score": <0-10>,
                "feedback": "<specific engagement feedback>"
            }},
            "confidence": {{
                "score": <0-10>,
                "feedback": "<specific confidence feedback>"
            }},
            "technical_terminology": {{
                "score": <0-10>,
                "feedback": "<specific technical terminology feedback>"
            }},
            "overall_score": <0-10>,
            "key_strengths": ["<strength 1>", "<strength 2>", ...],
            "improvement_areas": ["<area 1>", "<area 2>", ...],
            "practical_tips": ["<tip 1>", "<tip 2>", ...]
        }}
        """
        
        self.communication_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(communication_assessment_template),
            output_key="communication_assessment"
        )
        
        # Create completeness evaluation chain
        completeness_evaluation_template = """
        You are an expert interview coach evaluating the completeness of a candidate's response.
        
        Question: {question}
        Candidate's Response: {answer}
        Job Role: {job_role}
        
        TASK: Evaluate how complete and comprehensive the candidate's answer is for this specific question and job role.
        
        Assess the following factors on a scale of 0-10 with specific feedback:
        - Question Relevance: How directly did they address the actual question asked?
        - Key Points Coverage: Did they cover all the important aspects related to the question?
        - Examples: Did they provide sufficient and relevant examples?
        - Depth: Did they go beyond surface-level explanations?
        - Context Awareness: Did they tailor their response to the role and company context?
        
        Additionally, provide:
        - Overall Completeness Score (0-10): A comprehensive assessment of response completeness
        - Missing Elements: Important points they should have included
        - Excessive Elements: Any unnecessary information that diluted their answer
        - Improvement Plan: How they could make the response more complete and relevant
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "question_relevance": {{
                "score": <0-10>,
                "feedback": "<specific relevance feedback>"
            }},
            "key_points_coverage": {{
                "score": <0-10>,
                "feedback": "<specific coverage feedback>"
            }},
            "examples": {{
                "score": <0-10>,
                "feedback": "<specific examples feedback>"
            }},
            "depth": {{
                "score": <0-10>,
                "feedback": "<specific depth feedback>"
            }},
            "context_awareness": {{
                "score": <0-10>,
                "feedback": "<specific context awareness feedback>"
            }},
            "overall_score": <0-10>,
            "missing_elements": ["<missing element 1>", "<missing element 2>", ...],
            "excessive_elements": ["<excessive element 1>", "<excessive element 2>", ...],
            "improvement_plan": "<specific plan for improving completeness>"
        }}
        """
        
        self.completeness_evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(completeness_evaluation_template),
            output_key="completeness_evaluation"
        )
        
        # Create personalized feedback generator chain
        personalized_feedback_template = """
        You are an expert interview coach creating personalized feedback for a candidate.
        
        CANDIDATE PROFILE:
        - Role they're applying for: {job_role}
        - Experience level: {experience_level}
        - Strengths: {strengths}
        - Areas for improvement: {areas_for_improvement}
        - Learning style: {learning_style}
        
        INTERVIEW EVALUATION:
        - Question: {question}
        - Candidate's Response: {answer}
        - STAR Method Evaluation: {star_evaluation}
        - Communication Assessment: {communication_assessment}
        - Response Completeness: {response_completeness}
        
        TASK: Create highly personalized feedback and coaching for this specific candidate.
        
        Your feedback must include:
        1. STRENGTHS AFFIRMATION (2-3 points): Highlight what they did well, tied to their specific strengths profile
        2. GROWTH AREAS (2-3 points): Identify key improvement areas, considering their experience level
        3. PERSONALIZED COACHING: Tailored advice matching their learning style and professional goals
        4. CONCRETE EXAMPLES: Rewrite 1-2 portions of their answer to demonstrate improvement
        5. ACTIONABLE NEXT STEPS: 2-3 specific practice exercises or resources
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "strengths_affirmation": [
                "<strength point 1 with specific example from their answer>",
                "<strength point 2 with specific example from their answer>"
            ],
            "growth_areas": [
                "{{
                    "area": "<improvement area 1>",
                    "rationale": "<why this matters for their target role>",
                    "example_from_answer": "<specific example from their response>"
                }}",
                "{{
                    "area": "<improvement area 2>",
                    "rationale": "<why this matters for their target role>",
                    "example_from_answer": "<specific example from their response>"
                }}"
            ],
            "personalized_coaching": "<300-400 character paragraph with tailored advice based on learning style>",
            "improved_answer_examples": [
                "{{
                    "original": "<direct quote from their answer>",
                    "improved": "<rewritten version showing the improvement>"
                }}"
            ],
            "next_steps": [
                "{{
                    "activity": "<specific practice exercise>",
                    "benefit": "<how this addresses their specific needs>"
                }}",
                "{{
                    "activity": "<resource or practice technique>",
                    "benefit": "<how this builds on their strengths>"
                }}"
            ],
            "summary": "<one sentence personalized encouragement>"
        }}
        """
        
        self.personalized_feedback_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(personalized_feedback_template),
            output_key="personalized_feedback"
        )
        
        # Create performance tracker/metrics generator
        performance_metrics_template = """
        You are an expert interview coach tracking a candidate's interview performance over time.
        
        PREVIOUS EVALUATIONS:
        {previous_evaluations}
        
        CURRENT EVALUATION:
        - Question: {question}
        - Candidate's Response: {answer}
        - STAR Method Score: {star_score}
        - Communication Score: {communication_score}
        - Completeness Score: {completeness_score}
        
        TASK: Generate performance metrics comparing current performance to historical data, and create a progress report.
        
        Include:
        1. METRICS SUMMARY: Key scores for this response compared to previous average
        2. PROGRESS TRACKING: Areas showing improvement and those still needing work
        3. TREND ANALYSIS: Overall direction of improvement
        4. ACHIEVEMENT BADGES: Any notable milestones reached
        5. FOCUS RECOMMENDATIONS: What to prioritize next based on progress
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "metrics_summary": {{
                "star_score": {{
                    "current": <current score>,
                    "previous_avg": <previous average>,
                    "delta": <change percentage>
                }},
                "communication_score": {{
                    "current": <current score>,
                    "previous_avg": <previous average>,
                    "delta": <change percentage>
                }},
                "completeness_score": {{
                    "current": <current score>,
                    "previous_avg": <previous average>,
                    "delta": <change percentage>
                }},
                "overall_score": {{
                    "current": <current overall>,
                    "previous_avg": <previous average>,
                    "delta": <change percentage>
                }}
            }},
            "progress_tracking": {{
                "improving_areas": [
                    "{{
                        "area": "<improving area 1>",
                        "evidence": "<specific evidence of improvement>"
                    }}",
                    "{{
                        "area": "<improving area 2>",
                        "evidence": "<specific evidence of improvement>"
                    }}"
                ],
                "focus_areas": [
                    "{{
                        "area": "<focus area 1>",
                        "rationale": "<why focus is still needed>"
                    }}",
                    "{{
                        "area": "<focus area 2>",
                        "rationale": "<why focus is still needed>"
                    }}"
                ]
            }},
            "trend_analysis": "<assessment of overall trajectory with 100-150 character explanation>",
            "achievement_badges": [
                "{{
                    "badge": "<achievement badge 1>",
                    "description": "<what they did to earn it>"
                }}"
            ],
            "focus_recommendations": [
                "<specific focus recommendation 1>",
                "<specific focus recommendation 2>"
            ]
        }}
        """
        
        self.performance_metrics_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(performance_metrics_template),
            output_key="performance_metrics"
        )
        
        # Create structured feedback templates
        self.feedback_templates = {
            "star_method": {
                "title": "STAR Method Evaluation",
                "intro": "I've analyzed your answer using the STAR method framework. Here's a breakdown:",
                "sections": [
                    {
                        "name": "Situation",
                        "icon": "📋",
                        "description": "Setting the context",
                        "score_key": "situation.score",
                        "feedback_key": "situation.feedback"
                    },
                    {
                        "name": "Task",
                        "icon": "🎯",
                        "description": "Your specific role",
                        "score_key": "task.score",
                        "feedback_key": "task.feedback"
                    },
                    {
                        "name": "Action",
                        "icon": "⚙️",
                        "description": "Steps you took",
                        "score_key": "action.score",
                        "feedback_key": "action.feedback"
                    },
                    {
                        "name": "Result",
                        "icon": "🏆",
                        "description": "Outcome achieved",
                        "score_key": "result.score",
                        "feedback_key": "result.feedback"
                    }
                ],
                "summary_key": "overall_feedback",
                "strengths_key": "strengths",
                "improvements_key": "areas_for_improvement"
            },
            "communication": {
                "title": "Communication Skills Assessment",
                "intro": "I've evaluated the communication aspects of your answer. Here's my assessment:",
                "sections": [
                    {
                        "name": "Clarity",
                        "icon": "💡",
                        "description": "How clear your message was",
                        "score_key": "clarity.score",
                        "feedback_key": "clarity.feedback"
                    },
                    {
                        "name": "Conciseness",
                        "icon": "✂️",
                        "description": "Efficiency of your communication",
                        "score_key": "conciseness.score",
                        "feedback_key": "conciseness.feedback"
                    },
                    {
                        "name": "Structure",
                        "icon": "🏗️",
                        "description": "Organization of your response",
                        "score_key": "structure.score",
                        "feedback_key": "structure.feedback"
                    },
                    {
                        "name": "Engagement",
                        "icon": "🎤",
                        "description": "How engaging your delivery was",
                        "score_key": "engagement.score",
                        "feedback_key": "engagement.feedback"
                    },
                    {
                        "name": "Confidence",
                        "icon": "👍",
                        "description": "Confidence in your delivery",
                        "score_key": "confidence.score",
                        "feedback_key": "confidence.feedback"
                    }
                ],
                "summary_key": "overall_score",
                "strengths_key": "key_strengths",
                "improvements_key": "improvement_areas"
            },
            "completeness": {
                "title": "Response Completeness Analysis",
                "intro": "I've analyzed how complete and comprehensive your answer was:",
                "sections": [
                    {
                        "name": "Question Relevance",
                        "icon": "🎯",
                        "description": "How directly you addressed the question",
                        "score_key": "question_relevance.score",
                        "feedback_key": "question_relevance.feedback"
                    },
                    {
                        "name": "Key Points Coverage",
                        "icon": "📋",
                        "description": "Coverage of important aspects",
                        "score_key": "key_points_coverage.score",
                        "feedback_key": "key_points_coverage.feedback"
                    },
                    {
                        "name": "Examples",
                        "icon": "🔍",
                        "description": "Relevance and sufficiency of examples",
                        "score_key": "examples.score",
                        "feedback_key": "examples.feedback"
                    },
                    {
                        "name": "Depth",
                        "icon": "🧠",
                        "description": "Depth of your explanations",
                        "score_key": "depth.score",
                        "feedback_key": "depth.feedback"
                    },
                    {
                        "name": "Context Awareness",
                        "icon": "🔎",
                        "description": "Tailoring to role/company context",
                        "score_key": "context_awareness.score",
                        "feedback_key": "context_awareness.feedback"
                    }
                ],
                "summary_key": "overall_score",
                "strengths_key": "",
                "improvements_key": "missing_elements"
            },
            "personalized": {
                "title": "Personalized Coaching Feedback",
                "intro": "Based on your profile and this response, here's my personalized coaching:",
                "sections": [],
                "summary_key": "personalized_coaching",
                "strengths_key": "strengths_affirmation",
                "improvements_key": "growth_areas"
            }
        }
    
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
                evaluations["completeness"] = self._evaluate_response_completeness(question, previous_answer)
            
            if feedback_type == "comprehensive" or feedback_type == "personalized":
                evaluations["personalized"] = self.generate_personalized_feedback(question, previous_answer, candidate_info)
            
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
            "general": f"""
# General Interview Tips for {job_role} Positions

## Before the Interview
1. **Research the Company**: Understand their mission, products, culture
2. **Review the Job Description**: Map your experience to their requirements
3. **Prepare Questions**: Thoughtful questions show your interest
4. **Practice Common Questions**: Especially using the STAR method
5. **Technical Preparation**: Review relevant skills and concepts

## During the Interview
1. **Listen Carefully**: Understand what's being asked
2. **Structured Responses**: Use the STAR method for behavioral questions
3. **Be Specific**: Use concrete examples rather than generalizations
4. **Show Your Thinking**: Explain your approach, especially for technical questions
5. **Authenticity**: Be genuine while maintaining professionalism

## After the Interview
1. **Send a Thank You Note**: Express appreciation for the opportunity
2. **Reflect on Your Performance**: Identify areas for improvement
3. **Follow Up Appropriately**: If you haven't heard back in the stated timeframe

## Interview Psychology
1. **Confidence vs. Arrogance**: Show self-assurance without overstepping
2. **Authenticity**: Be yourself while maintaining professionalism
3. **Growth Mindset**: Frame challenges as learning opportunities
4. **Positive Language**: Focus on what you can and have done

### Remember: The interview is a two-way evaluation. You're assessing the company as much as they're assessing you.
        """,
            "star_method": f"""
# STAR Method: Structuring Powerful Interview Responses

The STAR method helps you structure your responses to behavioral questions for maximum impact. Here's how to use it effectively:

## Situation
- Set the scene with a specific context
- Be concise but include relevant details
- Example: "While working as a {job_role} at Company X, we faced a critical deadline with limited resources..."

## Task
- Describe your specific responsibilities
- Explain the challenges clearly
- Example: "I was tasked with delivering a complex feature within two weeks while maintaining code quality..."

## Action
- Detail the steps YOU took (not the team)
- Use "I" statements to highlight your role
- Focus on your decision-making process
- Example: "I created a detailed work breakdown structure, prioritized features, and implemented a daily check-in process..."

## Result
- Quantify your results whenever possible
- Highlight what you learned
- Connect to the job you're applying for
- Example: "As a result, we delivered the project two days early, increased system performance by 30%, and received recognition from leadership..."

### Practice Exercise:
Choose 3-5 accomplishments from your experience and write them out using the STAR method. Refine until each example is clear, concise, and compelling.
        """,
        
        "technical_interviews": f"""
# Excelling in Technical Interviews for {job_role} Positions

## Preparation Strategies
1. **Review Fundamentals**: Ensure core concepts for {job_role} roles are solid
2. **Practice Problem-Solving**: Use platforms like LeetCode or HackerRank
3. **Study System Design**: Understand scalability, performance, and reliability principles
4. **Know Your Projects**: Be ready to discuss technical decisions and trade-offs

## During the Interview
1. **Clarify Requirements**: Ask questions before starting to solve
2. **Think Aloud**: Share your thought process as you work
3. **Consider Edge Cases**: Show thoroughness in your solutions
4. **Optimize Incrementally**: Start with a working solution, then improve it
5. **Test Your Solution**: Demonstrate quality assurance mindset

## Communication Tips
1. Use proper technical terminology
2. Explain complex concepts simply
3. Acknowledge limitations in your approach
4. Be receptive to hints and feedback
5. Connect solutions to real-world applications

## Common Pitfalls to Avoid
1. Jumping to code without planning
2. Focusing only on the happy path
3. Overcomplicating simple problems
4. Being defensive about feedback
5. Failing to ask clarifying questions

### Remember: Technical interviews assess not just what you know, but how you approach problems and communicate solutions.
        """,
        
        "behavioral_interviews": f"""
# Mastering Behavioral Interviews for {job_role} Roles

## Key Preparation Steps
1. **Research the Company**: Understand their culture, values, and challenges
2. **Analyze the Job Description**: Identify key traits and experiences they seek
3. **Prepare Stories**: Develop 8-10 flexible stories using the STAR method
4. **Practice Delivery**: Record yourself to refine clarity and conciseness

## Behavioral Competencies Often Assessed
1. **Teamwork**: Collaboration and conflict resolution
2. **Leadership**: Initiative and influence without authority
3. **Problem-solving**: Analytical thinking and creativity
4. **Adaptability**: Response to change and uncertainty
5. **Communication**: Clarity in different contexts

## Powerful Story Elements
1. Include specific challenges faced
2. Highlight your unique contribution
3. Show self-awareness and growth
4. Quantify results when possible
5. Align with the company's values

## Common Questions and Story Applications
- "Tell me about a time you faced a significant challenge..."
- "Describe a situation where you had to influence others..."
- "Give an example of how you handled a conflict with a colleague..."
- "Share an experience where you had to learn a new technology or skill quickly..."

### Pro Tip: For each story, prepare multiple angles to highlight different skills depending on the question asked.
        """,
        
        "answering_questions": f"""
# Effective Question-Answering Techniques for {job_role} Interviews

## Universal Principles
1. **Listen Completely**: Process the entire question before responding
2. **Pause When Needed**: Take a moment to organize your thoughts
3. **Structure Clearly**: Use frameworks like STAR for complex answers
4. **Be Concise**: Aim for 1-2 minute responses for most questions
5. **Close Strongly**: End with concrete results or lessons learned

## Handling Different Question Types

### Direct Questions
- Answer explicitly first, then provide supporting details
- Example Q: "Do you have experience with Python?"
- Example A: "Yes, I've used Python for 3 years, primarily for data analysis and automation. For instance..."

### Behavioral Questions
- Use the STAR method (Situation, Task, Action, Result)
- Focus on YOUR specific contributions
- Example Q: "Tell me about a time you solved a complex problem."

### Technical Questions
- Clarify your understanding first
- Explain your thought process step-by-step
- Consider multiple approaches
- Example Q: "How would you optimize this database query?"

### Hypothetical Scenarios
- State your assumptions
- Walk through your decision-making framework
- Balance ideal approaches with practical considerations
- Example Q: "What would you do if a critical system failed before a launch?"

## Addressing Challenging Questions
1. **Questions About Weaknesses**: Show self-awareness and improvement efforts
2. **Knowledge Gaps**: Be honest but emphasize your learning approach
3. **Negative Past Experiences**: Focus on lessons and growth
4. **Salary Expectations**: Research industry standards before the interview

### Remember: Every question is an opportunity to demonstrate value and fit for the role.
        """
    }
    
    return advice_templates.get(topic, advice_templates["general"])

    def _generate_practice_question(self, question_type: str, job_role: str) -> str:
        """
        Generate a practice interview question based on type and job role.
        
        Args:
            question_type: The type of question (technical, behavioral, etc.)
            job_role: The job role being applied for
            
        Returns:
            Practice question with instructions
        """
        # Sample questions by type
        questions = {
            "technical": [
                f"How would you design a scalable architecture for a high-traffic web application in your role as a {job_role}?",
                f"Explain the process you would follow to troubleshoot a performance issue in a production system as a {job_role}.",
                f"What testing strategies would you implement for a critical {job_role} project?",
                f"Describe how you would approach refactoring a legacy codebase as a {job_role}."
            ],
            "behavioral": [
                f"Tell me about a time when you had to deal with a significant challenge in your previous role that relates to being a {job_role}.",
                f"Describe a situation where you had to work with a difficult team member on a {job_role} project.",
                f"Give an example of when you had to make a difficult decision with limited information as a {job_role}.",
                f"Share an experience where you had to learn a new technology or skill quickly for a {job_role} position."
            ],
            "case_study": [
                f"Our company is experiencing scaling issues with our main product. As a {job_role}, how would you analyze the problem and propose solutions?",
                f"We're considering implementing a new feature that could impact 50% of our users. As a {job_role}, how would you approach this project?",
                f"Our team is falling behind on sprint commitments. As a {job_role}, what steps would you take to address this situation?",
                f"We need to reduce operational costs by 20% without affecting quality. As a {job_role}, what strategy would you recommend?"
            ],
            "general": [
                f"Why are you interested in this {job_role} position at our company?",
                f"Where do you see yourself in five years in the {job_role} field?",
                f"What unique qualities would you bring to our team as a {job_role}?",
                f"How do you stay updated with the latest trends and technologies relevant to the {job_role} position?"
            ]
        }
        
        # Select a random question from the appropriate category
        question = random.choice(questions.get(question_type, questions["general"]))
        
        # Provide instructions based on question type
        instructions = {
            "technical": "When answering this technical question, explain your thought process clearly, consider different approaches, and discuss any trade-offs involved.",
            "behavioral": "Use the STAR method (Situation, Task, Action, Result) to structure your answer to this behavioral question.",
            "case_study": "For this case study, consider various perspectives including technical feasibility, business impact, and user experience.",
            "general": "Keep your answer concise, authentic, and relevant to the role you're applying for."
        }
        
        return f"""
## Practice Interview Question ({question_type.title()} Type)

{question}

### Instructions
{instructions.get(question_type, instructions["general"])}

Provide your answer, and I'll give you detailed feedback using our assessment framework.
"""

    def _evaluate_star_method(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate how well a response follows the STAR method.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            
        Returns:
            Dictionary with STAR evaluation results
        """
        try:
            # Call LLM to analyze response
            response = self.star_evaluation_chain.invoke({
                "question": question,
                "answer": answer
            })
            
            # Parse the response
            if isinstance(response, dict) and "star_evaluation" in response:
                evaluation = response["star_evaluation"]
                try:
                    if isinstance(evaluation, str):
                        # Try to parse the string as JSON
                        evaluation = json.loads(evaluation)
                    return evaluation
                except:
                    self.logger.error("Failed to parse STAR evaluation as JSON")
                    return self._create_default_star_evaluation()
            else:
                return self._create_default_star_evaluation()
        except Exception as e:
            self.logger.error(f"Error in STAR method evaluation: {e}")
            return self._create_default_star_evaluation()

    def _create_default_star_evaluation(self) -> Dict[str, Any]:
        """
        Create a default STAR evaluation response for error cases.
        
        Returns:
            Default STAR evaluation dictionary
        """
        return {
            "situation": {"score": 5, "feedback": "Your description of the situation needs more context."},
            "task": {"score": 5, "feedback": "Clarify your specific role and responsibility in this scenario."},
            "action": {"score": 5, "feedback": "Provide more details about the steps you took."},
            "result": {"score": 5, "feedback": "Quantify or qualify your results more clearly."},
            "overall_score": 5,
            "improvements": ["Be more specific about the situation context", "Clearly state your objective", "Describe your actions in more detail", "Quantify your results when possible"],
            "strengths": ["Basic STAR structure is present"]
        }    

    def _evaluate_communication_skills(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate communication skills in a response.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            
        Returns:
            Dictionary with communication assessment results
        """
        try:
            # Call LLM to analyze communication
            response = self.communication_assessment_chain.invoke({
                "question": question,
                "answer": answer
            })
            
            # Parse the response
            if isinstance(response, dict) and "communication_assessment" in response:
                assessment = response["communication_assessment"]
                try:
                    if isinstance(assessment, str):
                        # Try to parse the string as JSON
                        assessment = json.loads(assessment)
                    return assessment
                except:
                    self.logger.error("Failed to parse communication assessment as JSON")
                    return self._create_default_communication_assessment()
            else:
                return self._create_default_communication_assessment()
        except Exception as e:
            self.logger.error(f"Error in communication skills assessment: {e}")
            return self._create_default_communication_assessment()

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

    def _evaluate_response_completeness(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate the completeness of a response.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            
        Returns:
            Dictionary with completeness evaluation results
        """
        try:
            job_role = "the position" if not hasattr(self, "job_role") else self.job_role
            
            # Call LLM to analyze completeness
            response = self.completeness_evaluation_chain.invoke({
                "question": question,
                "answer": answer,
                "job_role": job_role
            })
            
            # Parse the response
            if isinstance(response, dict) and "completeness_evaluation" in response:
                evaluation = response["completeness_evaluation"]
                try:
                    if isinstance(evaluation, str):
                        # Try to parse the string as JSON
                        evaluation = json.loads(evaluation)
                    return evaluation
                except:
                    self.logger.error("Failed to parse completeness evaluation as JSON")
                    return self._create_default_completeness_evaluation()
            else:
                return self._create_default_completeness_evaluation()
        except Exception as e:
            self.logger.error(f"Error in response completeness evaluation: {e}")
            return self._create_default_completeness_evaluation()

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

    def generate_personalized_feedback(self, question: str, answer: str, 
                                      candidate_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate personalized feedback based on response evaluation and candidate profile.
        
        Args:
            question: The interview question
            answer: The candidate's answer
            candidate_profile: Dictionary containing candidate information
            
        Returns:
            Dictionary with personalized feedback
        """
        # Default profile if none provided
        profile = {
            "job_role": "the position",
            "experience_level": "mid-level",
            "strengths": ["technical knowledge", "communication"],
            "areas_for_improvement": ["structuring answers", "providing examples"],
            "learning_style": "visual and practical"
        }
        
        # Update with provided profile if available
        if candidate_profile:
            profile.update(candidate_profile)
        
        # Evaluate using different methods
        star_eval = self._evaluate_star_method(question, answer)
        comm_eval = self._evaluate_communication_skills(question, answer)
        comp_eval = self._evaluate_response_completeness(question, answer)
        
        try:
            # Generate personalized feedback
            response = self.personalized_feedback_chain.invoke({
                "job_role": profile["job_role"],
                "experience_level": profile["experience_level"],
                "strengths": ", ".join(profile["strengths"]),
                "areas_for_improvement": ", ".join(profile["areas_for_improvement"]),
                "learning_style": profile["learning_style"],
                "question": question,
                "answer": answer,
                "star_evaluation": json.dumps(star_eval),
                "communication_assessment": json.dumps(comm_eval),
                "response_completeness": json.dumps(comp_eval)
            })
            
            # Parse the response
            if isinstance(response, dict) and "personalized_feedback" in response:
                feedback = response["personalized_feedback"]
                try:
                    if isinstance(feedback, str):
                        # Try to parse the string as JSON
                        feedback = json.loads(feedback)
                    return feedback
                except:
                    self.logger.error("Failed to parse personalized feedback as JSON")
                    return self._create_default_personalized_feedback()
            else:
                return self._create_default_personalized_feedback()
        except Exception as e:
            self.logger.error(f"Error generating personalized feedback: {e}")
            return self._create_default_personalized_feedback()

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
        comp_eval = self._evaluate_response_completeness(question, answer)
        
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
