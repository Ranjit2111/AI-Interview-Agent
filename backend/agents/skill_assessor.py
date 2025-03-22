"""
Skill assessor agent that evaluates a user's technical competencies during the interview.
This agent identifies skills demonstrated, assesses proficiency levels, and suggests resources for improvement.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

try:
    # Try standard import in production
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import Event, EventBus
    from backend.models.interview import SkillAssessment, Resource
    from backend.agents.templates.skill_templates import (
        SKILL_SYSTEM_PROMPT,
        SKILL_EXTRACTION_TEMPLATE,
        PROFICIENCY_ASSESSMENT_TEMPLATE,
        RESOURCE_SUGGESTION_TEMPLATE,
        SKILL_PROFILE_TEMPLATE,
        ASSESSMENT_RESPONSE_TEMPLATE,
        RECENT_ANSWER_ASSESSMENT_TEMPLATE,
        SKILL_UPDATE_NOTIFICATION_TEMPLATE
    )
except ImportError:
    # Use relative imports for development/testing
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import Event, EventBus
    from ..models.interview import SkillAssessment, Resource
    from .templates.skill_templates import (
        SKILL_SYSTEM_PROMPT,
        SKILL_EXTRACTION_TEMPLATE,
        PROFICIENCY_ASSESSMENT_TEMPLATE,
        RESOURCE_SUGGESTION_TEMPLATE,
        SKILL_PROFILE_TEMPLATE,
        ASSESSMENT_RESPONSE_TEMPLATE,
        RECENT_ANSWER_ASSESSMENT_TEMPLATE,
        SKILL_UPDATE_NOTIFICATION_TEMPLATE
    )


class ProficiencyLevel(str, Enum):
    """Enum for skill proficiency levels."""
    NOVICE = "novice"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(str, Enum):
    """Categories for different types of skills."""
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"
    PROCESS = "process"
    LANGUAGE = "language"
    FRAMEWORK = "framework"


class SkillAssessorAgent(BaseAgent):
    """
    Agent that evaluates the user's skills during the interview.
    
    The skill assessor agent is responsible for:
    - Identifying skills mentioned or demonstrated in responses
    - Assessing proficiency levels for each skill
    - Tracking skill development across multiple sessions
    - Providing resources for skill improvement
    - Generating a comprehensive skill profile
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        planning_interval: int = 3,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        job_role: str = "",
        technical_focus: bool = True
    ):
        """
        Initialize the skill assessor agent.
        
        Args:
            api_key: API key for the language model
            model_name: Name of the language model to use
            planning_interval: Number of interactions before planning
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            job_role: Target job role for skill relevance
            technical_focus: Whether to focus on technical skills
        """
        super().__init__(api_key, model_name, planning_interval, event_bus, logger)
        
        self.job_role = job_role
        self.technical_focus = technical_focus
        self.interview_session_id = None
        self.current_question = None
        self.current_answer = None
        self.identified_skills = {}  # Dictionary mapping skill names to assessment data
        self.skill_mentions = {}     # Count of how many times each skill is mentioned
        self.last_assessment_time = None
        
        # Set up LLM chains
        self._setup_llm_chains()
        
        # Pre-defined skills for various roles
        self.role_skills = {
            "software engineer": {
                "technical": ["algorithms", "data structures", "system design", "coding", "debugging", 
                              "testing", "version control", "databases", "api design"],
                "languages": ["java", "python", "javascript", "c++", "typescript", "sql", "rust", "go"],
                "frameworks": ["react", "angular", "vue", "django", "flask", "spring", "node.js", "express"],
                "soft": ["problem solving", "teamwork", "communication", "time management"]
            },
            "data scientist": {
                "technical": ["machine learning", "data analysis", "statistics", "data visualization", 
                              "feature engineering", "data cleaning", "experiment design"],
                "languages": ["python", "r", "sql"],
                "tools": ["pandas", "scikit-learn", "tensorflow", "pytorch", "tableau", "power bi"],
                "soft": ["critical thinking", "research", "communication", "domain knowledge"]
            },
            "product manager": {
                "technical": ["product development", "market analysis", "user research", "roadmapping", 
                              "feature prioritization", "requirements gathering"],
                "tools": ["jira", "asana", "figma", "product analytics tools"],
                "soft": ["leadership", "communication", "negotiation", "strategic thinking", "empathy"]
            }
        }
        
        # Skill keywords to look for in responses
        self.skill_keywords = self._initialize_skill_keywords()
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe("interviewer_response", self._handle_interviewer_response)
            self.event_bus.subscribe("user_response", self._handle_user_response)
            self.event_bus.subscribe("interview_summary", self._handle_interview_summary)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the skill assessor agent.
        
        Returns:
            System prompt string
        """
        return SKILL_SYSTEM_PROMPT.format(job_role=self.job_role)
    
    def _initialize_tools(self) -> List[Tool]:
        """
        Initialize tools for the skill assessor agent.
        
        Returns:
            List of LangChain tools
        """
        return [
            Tool(
                name="extract_skills",
                func=self._extract_skills_tool,
                description="Extract skills mentioned in interview responses"
            ),
            Tool(
                name="assess_proficiency",
                func=self._assess_proficiency_tool,
                description="Assess the proficiency level for a mentioned skill"
            ),
            Tool(
                name="suggest_resources",
                func=self._suggest_resources_tool,
                description="Suggest resources for improving a specific skill"
            ),
            Tool(
                name="create_skill_profile",
                func=self._create_skill_profile_tool,
                description="Create a comprehensive skill profile based on interview responses"
            )
        ]
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Skill extraction chain
        self.skill_extraction_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(SKILL_EXTRACTION_TEMPLATE),
            output_parser=JsonOutputParser(),
            output_key="extracted_skills"
        )
        
        # Proficiency assessment chain
        self.proficiency_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(PROFICIENCY_ASSESSMENT_TEMPLATE),
            output_parser=StrOutputParser(),
            output_key="proficiency_level"
        )
        
        # Resource suggestion chain
        self.resource_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(RESOURCE_SUGGESTION_TEMPLATE),
            output_parser=JsonOutputParser(),
            output_key="resources"
        )
        
        # Skill profile chain
        self.profile_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(SKILL_PROFILE_TEMPLATE),
            output_key="skill_profile"
        )
    
    def _extract_skills_tool(self, response: str) -> List[Dict[str, Any]]:
        """
        Tool function to extract skills from a response.
        
        Args:
            response: The response to analyze
            
        Returns:
            List of extracted skills with metadata
        """
        try:
            result = self.skill_extraction_chain.invoke({
                "job_role": self.job_role,
                "response": response
            })
            return result["extracted_skills"]
        except Exception as e:
            self.logger.error(f"Error extracting skills: {e}")
            # Fallback to simpler extraction method
            return self._identify_skills_in_text(response)
    
    def _assess_proficiency_tool(self, skill: str, context: str) -> str:
        """
        Tool function to assess proficiency level for a skill.
        
        Args:
            skill: The skill to assess
            context: Context from the candidate's response
            
        Returns:
            Assessed proficiency level
        """
        try:
            result = self.proficiency_chain.invoke({
                "skill": skill,
                "job_role": self.job_role,
                "context": context
            })
            return result["proficiency_level"]
        except Exception as e:
            self.logger.error(f"Error assessing proficiency: {e}")
            # Fallback to simpler proficiency estimation
            return self._estimate_proficiency(skill, context)
    
    def _suggest_resources_tool(self, skill: str, proficiency_level: str) -> List[Dict[str, Any]]:
        """
        Tool function to suggest resources for improving a skill.
        
        Args:
            skill: The skill to improve
            proficiency_level: Current proficiency level
            
        Returns:
            List of suggested resources
        """
        try:
            result = self.resource_chain.invoke({
                "skill": skill,
                "proficiency_level": proficiency_level,
                "job_role": self.job_role
            })
            return result["resources"]
        except Exception as e:
            self.logger.error(f"Error suggesting resources: {e}")
            # Fallback to simpler resource suggestions
            resources = self._get_resources_for_skill(skill)
            return [{"type": "text", "content": resources}]
    
    def _create_skill_profile_tool(self, skills_json: str) -> str:
        """
        Tool function to create a comprehensive skill profile.
        
        Args:
            skills_json: JSON string of skills data
            
        Returns:
            Comprehensive skill profile
        """
        try:
            result = self.profile_chain.invoke({
                "job_role": self.job_role,
                "skills_json": skills_json
            })
            return result["skill_profile"]
        except Exception as e:
            self.logger.error(f"Error creating skill profile: {e}")
            # Fallback to simpler profile generation
            return self._generate_skill_profile(self.current_context)

    def process_input(self, input_text: str, context: AgentContext) -> str:
        """
        Process input from the user and generate a skill assessment response.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            The agent's skill assessment response
        """
        # Update context with user input
        context.add_message("user", input_text)
        self.current_context = context
        
        # Use LangChain agent if tools are set up
        if hasattr(self, 'agent_executor') and self.agent_executor:
            try:
                agent_response = self.process_with_langchain(input_text, context)
                response = agent_response.get("output", "")
            except Exception as e:
                self.logger.error(f"Error using LangChain agent: {e}")
                # Fall back to rule-based processing
                response = self._process_input_rule_based(input_text, context)
        else:
            # Use rule-based processing
            response = self._process_input_rule_based(input_text, context)
        
        # Add response to context
        context.add_message("assistant", response)
        
        # Publish event
        if self.event_bus and len(self.identified_skills) > 0:
            self.event_bus.publish(Event(
                event_type="skill_assessment_update",
                source="skill_assessor_agent",
                data={
                    "session_id": self.interview_session_id,
                    "identified_skills": list(self.identified_skills.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        
        return response
    
    def _process_input_rule_based(self, input_text: str, context: AgentContext) -> str:
        """
        Process input using rule-based methods.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            The agent's skill assessment response
        """
        # Determine if this is a request for specific skill information
        if "skills" in input_text.lower() and "profile" in input_text.lower():
            response = self._generate_skill_profile(context)
        elif "resources" in input_text.lower() or "improve" in input_text.lower():
            response = self._suggest_skill_resources(input_text, context)
        elif "assess" in input_text.lower() or "evaluate" in input_text.lower():
            response = self._assess_recent_answer(context)
        else:
            # Perform regular skill assessment on the input
            self._identify_skills_in_text(input_text)
            response = self._create_skill_update(context)
        
        return response
    
    def _initialize_skill_keywords(self) -> Dict[str, List[str]]:
        """
        Initialize skill keywords to detect in user responses.
        
        Returns:
            Dictionary mapping skill categories to lists of keywords
        """
        keywords = {}
        
        # Find the closest matching job role for our predefined skills
        matched_role = None
        for role in self.role_skills:
            if role in self.job_role.lower():
                matched_role = role
                break
        
        # Use the matched role or default to software engineer
        role_data = self.role_skills.get(matched_role, self.role_skills["software engineer"])
        
        # Flatten the nested skill lists
        for category, skills in role_data.items():
            keywords[category] = skills
        
        # Add general skills that apply to most roles
        keywords["general"] = [
            "problem solving", "critical thinking", "communication",
            "teamwork", "leadership", "time management", "organization"
        ]
        
        return keywords
    
    def _identify_skills_in_text(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Identify skills mentioned in the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of tuples of (skill_name, category, confidence)
        """
        # TODO: Replace with actual LLM-based skill extraction
        
        identified_skills = []
        text_lower = text.lower()
        
        # Look for skills based on keywords
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                # Check for exact matches or variations
                skill_variations = [skill, f"{skill}s", f"{skill}ing", f"{skill}ed"]
                for variation in skill_variations:
                    # Use word boundary to ensure we're matching whole words
                    pattern = r'\b' + re.escape(variation) + r'\b'
                    matches = re.findall(pattern, text_lower)
                    
                    if matches:
                        # Count occurrences
                        count = len(matches)
                        
                        # Increment skill mentions counter
                        if skill in self.skill_mentions:
                            self.skill_mentions[skill] += count
                        else:
                            self.skill_mentions[skill] = count
                        
                        # Add to identified skills if not already present
                        if skill not in self.identified_skills:
                            # Determine confidence based on context
                            confidence = 0.7  # Default moderate confidence
                            
                            # Adjust confidence based on context
                            if f"experience in {variation}" in text_lower or f"worked with {variation}" in text_lower:
                                confidence = 0.9
                            elif f"familiar with {variation}" in text_lower or f"know {variation}" in text_lower:
                                confidence = 0.8
                            elif f"learning {variation}" in text_lower or f"beginner in {variation}" in text_lower:
                                confidence = 0.6
                            
                            # Map the skill category from our internal format to the model's format
                            model_category = SkillCategory.TECHNICAL
                            if category == "languages":
                                model_category = SkillCategory.LANGUAGE
                            elif category == "frameworks":
                                model_category = SkillCategory.FRAMEWORK
                            elif category == "tools":
                                model_category = SkillCategory.TOOL
                            elif category == "soft" or category == "general":
                                model_category = SkillCategory.SOFT
                            
                            # Estimate proficiency based on context
                            proficiency = self._estimate_proficiency(skill, text_lower)
                            
                            # Store in identified skills
                            self.identified_skills[skill] = {
                                "category": model_category,
                                "confidence": confidence,
                                "proficiency": proficiency,
                                "mentions": self.skill_mentions[skill],
                                "last_mentioned": datetime.utcnow().isoformat()
                            }
                            
                            identified_skills.append((skill, model_category, confidence))
                        
                        # Break out of variations loop once we find a match
                        break
        
        return identified_skills
    
    def _estimate_proficiency(self, skill: str, text: str) -> ProficiencyLevel:
        """
        Estimate the proficiency level for a skill based on the text.
        
        Args:
            skill: The skill to estimate proficiency for
            text: The text to analyze
            
        Returns:
            Estimated proficiency level
        """
        # Look for indicators of proficiency
        novice_indicators = [f"beginning to learn {skill}", f"just started {skill}", 
                             f"novice {skill}", f"basic understanding of {skill}"]
        
        basic_indicators = [f"familiar with {skill}", f"worked with {skill} a bit",
                           f"some experience in {skill}", f"understand {skill}"]
        
        intermediate_indicators = [f"good knowledge of {skill}", f"worked with {skill}",
                                 f"{skill} experience", f"used {skill} in projects"]
        
        advanced_indicators = [f"extensive experience in {skill}", f"advanced {skill}",
                             f"very comfortable with {skill}", f"expert in {skill}",
                             f"mastery of {skill}", f"deep knowledge of {skill}"]
        
        # Check for proficiency indicators
        for indicator in advanced_indicators:
            if indicator in text:
                return ProficiencyLevel.ADVANCED
        
        for indicator in intermediate_indicators:
            if indicator in text:
                return ProficiencyLevel.INTERMEDIATE
        
        for indicator in basic_indicators:
            if indicator in text:
                return ProficiencyLevel.BASIC
        
        for indicator in novice_indicators:
            if indicator in text:
                return ProficiencyLevel.NOVICE
        
        # Default to intermediate if no clear indicators
        return ProficiencyLevel.INTERMEDIATE
    
    def _assess_recent_answer(self, context: AgentContext) -> str:
        """
        Assess the skills demonstrated in the most recent answer.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Skill assessment for the recent answer
        """
        # Find the most recent user message
        recent_response = None
        for idx in range(len(context.conversation_history) - 1, -1, -1):
            message = context.conversation_history[idx]
            if message["role"] == "user":
                recent_response = message["content"]
                break
        
        if not recent_response:
            return "I don't see any recent responses to assess. Could you provide an answer for me to evaluate?"
        
        # Identify skills in the response
        identified = self._identify_skills_in_text(recent_response)
        
        if not identified:
            return (
                "I didn't identify any specific skills in your most recent response. "
                "Could you elaborate more on your technical background or experience with specific technologies? "
                "This will help me provide a more accurate assessment of your skills."
            )
        
        # Create assessment using template
        skills_info = []
        for skill, category, _ in identified:
            proficiency = self.identified_skills[skill]["proficiency"]
            skills_info.append(f"{skill.title()} ({category}): {proficiency.capitalize()}")
        
        skills_list = "\n".join([f"- {info}" for info in skills_info])
        
        return RECENT_ANSWER_ASSESSMENT_TEMPLATE.format(
            skills_list=skills_list,
            job_role=self.job_role
        )
    
    def _create_skill_update(self, context: AgentContext) -> str:
        """
        Create an update about newly identified skills.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Update message about identified skills
        """
        # Check if we've just identified new skills
        if not self.identified_skills:
            return ""  # No skills identified, return empty string to avoid interrupting flow
        
        # Get skills identified in the last minute to avoid constant interruptions
        now = datetime.utcnow()
        recent_skills = []
        
        if self.last_assessment_time is None:
            # First assessment, include all skills
            recent_skills = list(self.identified_skills.keys())
        else:
            # Check which skills were recently identified
            for skill, data in self.identified_skills.items():
                last_mentioned = datetime.fromisoformat(data["last_mentioned"])
                if (now - last_mentioned).total_seconds() < 60:  # Skills mentioned in last minute
                    recent_skills.append(skill)
        
        # Update the last assessment time
        self.last_assessment_time = now
        
        # If no recent skills, return empty string
        if not recent_skills:
            return ""
        
        # Create feedback using template
        # Only interrupt if we have substantial new information
        if len(recent_skills) >= 2:
            skills_str = ", ".join([f"**{skill}**" for skill in recent_skills])
            return SKILL_UPDATE_NOTIFICATION_TEMPLATE.format(
                skills=skills_str
            )
        
        # Otherwise return empty string to avoid interrupting the flow
        return ""
    
    def _generate_skill_profile(self, context: AgentContext) -> str:
        """
        Generate a comprehensive skill profile based on the interview.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Comprehensive skill profile
        """
        if not self.identified_skills:
            return (
                "I haven't identified enough skills yet to generate a comprehensive profile. "
                "As you continue with the interview and provide more detailed answers about your experience, "
                "I'll be able to build a more complete skill assessment."
            )
        
        # Group skills by category and proficiency
        categorized_skills = {}
        for skill, data in self.identified_skills.items():
            category = data["category"]
            if category not in categorized_skills:
                categorized_skills[category] = {
                    ProficiencyLevel.NOVICE: [],
                    ProficiencyLevel.BASIC: [],
                    ProficiencyLevel.INTERMEDIATE: [],
                    ProficiencyLevel.ADVANCED: [],
                    ProficiencyLevel.EXPERT: []
                }
            
            proficiency = data["proficiency"]
            categorized_skills[category][proficiency].append(skill)
        
        # Format the skill profile
        profile_parts = ["# Your Skill Profile\n"]
        
        # Add job role context if available
        if self.job_role:
            profile_parts.append(f"Based on your interview for the **{self.job_role}** position, I've assessed the following skills:\n")
        else:
            profile_parts.append("Based on your interview responses, I've assessed the following skills:\n")
        
        # Add skills by category
        for category in sorted(categorized_skills.keys()):
            category_skills = categorized_skills[category]
            # Only include categories with skills
            if any(len(skills) > 0 for skills in category_skills.values()):
                profile_parts.append(f"## {category.capitalize()} Skills\n")
                
                # Add skills by proficiency level (highest first)
                for proficiency in reversed([ProficiencyLevel.EXPERT, ProficiencyLevel.ADVANCED, 
                                           ProficiencyLevel.INTERMEDIATE, ProficiencyLevel.BASIC,
                                           ProficiencyLevel.NOVICE]):
                    skills = category_skills[proficiency]
                    if skills:
                        profile_parts.append(f"### {proficiency.capitalize()} Level\n")
                        for skill in sorted(skills):
                            profile_parts.append(f"- **{skill.title()}**")
                        profile_parts.append("")  # Add empty line
        
        # Add recommendations
        profile_parts.append("## Recommendations\n")
        
        # Identify skills to highlight and improve
        advanced_skills = []
        skills_to_improve = []
        
        for skill, data in self.identified_skills.items():
            if data["proficiency"] in [ProficiencyLevel.ADVANCED, ProficiencyLevel.EXPERT]:
                advanced_skills.append(skill)
            elif data["proficiency"] in [ProficiencyLevel.NOVICE, ProficiencyLevel.BASIC]:
                skills_to_improve.append(skill)
        
        # Add highlights
        if advanced_skills:
            profile_parts.append("### Strengths to Highlight\n")
            for skill in sorted(advanced_skills)[:3]:  # Top 3 advanced skills
                profile_parts.append(f"- Emphasize your expertise in **{skill}** during interviews")
            profile_parts.append("")
        
        # Add improvement suggestions
        if skills_to_improve:
            profile_parts.append("### Areas for Growth\n")
            for skill in sorted(skills_to_improve)[:3]:  # Top 3 skills to improve
                profile_parts.append(f"- Consider developing your **{skill}** skills further")
            profile_parts.append("")
        
        profile_parts.append("Would you like specific resources to improve any of these skills?")
        
        return "\n".join(profile_parts)
    
    def _suggest_skill_resources(self, input_text: str, context: AgentContext) -> str:
        """
        Suggest resources for improving specific skills.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            Resource suggestions for skill improvement
        """
        # Check if a specific skill is mentioned
        mentioned_skill = None
        
        for skill in self.identified_skills:
            if skill.lower() in input_text.lower():
                mentioned_skill = skill
                break
        
        if mentioned_skill:
            return self._get_resources_for_skill(mentioned_skill)
        else:
            # No specific skill mentioned, suggest resources for skills that need improvement
            skills_to_improve = []
            
            for skill, data in self.identified_skills.items():
                if data["proficiency"] in [ProficiencyLevel.NOVICE, ProficiencyLevel.BASIC]:
                    skills_to_improve.append(skill)
            
            if not skills_to_improve:
                # If no skills to improve, suggest resources for the most mentioned skills
                sorted_skills = sorted(self.skill_mentions.items(), key=lambda x: x[1], reverse=True)
                skills_to_improve = [skill for skill, _ in sorted_skills[:3] if skill in self.identified_skills]
            
            if not skills_to_improve:
                return (
                    "I haven't identified specific skills to suggest resources for yet. "
                    "Could you mention a particular skill you'd like to improve?"
                )
            
            # Provide resources for the top skill to improve
            return self._get_resources_for_skill(skills_to_improve[0])
    
    def _get_resources_for_skill(self, skill: str) -> str:
        """
        Get resource recommendations for a specific skill.
        
        Args:
            skill: The skill to get resources for
            
        Returns:
            Resource recommendations
        """
        # TODO: Replace with more tailored resource recommendations
        
        # Common resources by skill type
        technical_resources = {
            "algorithms": [
                ("Book", "Introduction to Algorithms by CLRS", "Comprehensive reference for algorithms"),
                ("Online Course", "Algorithms Specialization on Coursera", "Stanford's popular algorithms course"),
                ("Practice", "LeetCode", "Platform for practicing algorithm challenges")
            ],
            "data structures": [
                ("Book", "Cracking the Coding Interview", "Explains data structures with interview problems"),
                ("Video", "CS Dojo YouTube Channel", "Visual explanations of common data structures"),
                ("Practice", "HackerRank Data Structures", "Hands-on challenges with data structures")
            ],
            "system design": [
                ("Book", "System Design Interview by Alex Xu", "Practical guide to system design interviews"),
                ("Course", "Grokking the System Design Interview", "Step-by-step approach to system design"),
                ("Blog", "High Scalability", "Real-world architecture examples and patterns")
            ],
            "machine learning": [
                ("Course", "Andrew Ng's Machine Learning on Coursera", "Foundational ML course"),
                ("Book", "Hands-On Machine Learning with Scikit-Learn & TensorFlow", "Practical approach to ML"),
                ("Practice", "Kaggle Competitions", "Apply ML to real-world problems")
            ],
            "python": [
                ("Book", "Python Crash Course", "Fast-paced introduction to Python"),
                ("Course", "Python for Everybody on Coursera", "Beginner-friendly Python specialization"),
                ("Tutorial", "Real Python", "In-depth articles and tutorials on Python concepts")
            ],
            "javascript": [
                ("Book", "Eloquent JavaScript", "Modern JavaScript introduction"),
                ("Course", "JavaScript30 by Wes Bos", "Building 30 things with vanilla JS"),
                ("Documentation", "MDN Web Docs", "Comprehensive JavaScript reference")
            ]
        }
        
        soft_skill_resources = {
            "communication": [
                ("Book", "Crucial Conversations", "Techniques for effective high-stakes communication"),
                ("Course", "Dynamic Public Speaking on Coursera", "Improve verbal communication"),
                ("Practice", "Toastmasters International", "Join local chapters to practice public speaking")
            ],
            "leadership": [
                ("Book", "Start with Why by Simon Sinek", "Understanding leadership purpose"),
                ("Course", "Leadership Development at Coursera", "Frameworks for effective leadership"),
                ("Podcast", "HBR IdeaCast", "Harvard Business Review's leadership insights")
            ],
            "problem solving": [
                ("Book", "How to Solve It by G. Polya", "Timeless approach to problem-solving"),
                ("Course", "Problem Solving Skills at LinkedIn Learning", "Systematic problem-solving techniques"),
                ("Practice", "Mind Tools", "Problem-solving frameworks and exercises")
            ]
        }
        
        # Determine whether it's a technical or soft skill
        skill_lower = skill.lower()
        
        if skill_lower in technical_resources:
            resources = technical_resources[skill_lower]
        elif skill_lower in soft_skill_resources:
            resources = soft_skill_resources[skill_lower]
        else:
            # Generic resources for other skills
            resources = [
                ("Search", "Coursera or Udemy", f"Search for '{skill}' courses"),
                ("Books", "Amazon or O'Reilly", f"Look for highly-rated '{skill}' books"),
                ("Community", "Reddit or Stack Exchange", f"Join communities focused on {skill}")
            ]
        
        # Format the recommendations
        response_parts = [f"## Resources to Improve Your {skill.title()} Skills\n"]
        
        for resource_type, resource_name, description in resources:
            response_parts.append(f"### {resource_type}: {resource_name}")
            response_parts.append(f"{description}\n")
        
        response_parts.append("Would you like resources for any other skills I've identified in your profile?")
        
        return "\n".join(response_parts)
    
    def _handle_interviewer_response(self, event: Event) -> None:
        """
        Handle interviewer response events.
        
        Args:
            event: The event containing the interviewer's response
        """
        data = event.data
        
        # Store the session ID if not already set
        if not self.interview_session_id and "session_id" in data:
            self.interview_session_id = data["session_id"]
        
        # Check if this is a question
        if "current_state" in data and data["current_state"] == "questioning":
            self.current_question = data.get("response", "")
    
    def _handle_user_response(self, event: Event) -> None:
        """
        Handle user response events.
        
        Args:
            event: The event containing the user's response
        """
        # Store the current answer if we have a current question
        if self.current_question:
            response = event.data.get("response", "")
            self.current_answer = response
            
            # Process the response to identify skills
            self._identify_skills_in_text(response)
            
            # Add to context if available
            if self.current_context:
                self.current_context.add_message("user", response)
    
    def _handle_interview_summary(self, event: Event) -> None:
        """
        Handle interview summary events.
        
        Args:
            event: The event containing the interview summary
        """
        # Publish a comprehensive skill assessment at the end of interview
        if self.event_bus and self.identified_skills:
            skill_data = []
            
            for skill_name, data in self.identified_skills.items():
                skill_data.append({
                    "skill_name": skill_name,
                    "category": data["category"],
                    "proficiency": data["proficiency"],
                    "mentions": data["mentions"]
                })
            
            self.event_bus.publish(Event(
                event_type="comprehensive_skill_assessment",
                source="skill_assessor_agent",
                data={
                    "session_id": self.interview_session_id,
                    "skills": skill_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        
        # Reset for a new session
        self.current_question = None
        self.current_answer = None 