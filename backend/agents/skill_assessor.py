"""
Skill assessor agent that evaluates a user's technical competencies during the interview.
This agent identifies skills demonstrated, assesses proficiency levels, and suggests resources for improvement.
"""

import logging
import re
import json
import random
import asyncio
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
    from backend.utils.event_bus import Event, EventBus, EventType
    from backend.models.interview import SkillAssessment, Resource, ProficiencyLevel as DBProficiencyLevel, SkillCategory as DBSkillCategory
    from backend.services import get_search_service
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
    from ..utils.event_bus import Event, EventBus, EventType
    from ..models.interview import SkillAssessment, Resource, ProficiencyLevel as DBProficiencyLevel, SkillCategory as DBSkillCategory
    from ..services import get_search_service
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
    BEGINNER = "beginner"
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
        self.resource_cache = {}  # Cache for skill resources
        
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
            self.event_bus.subscribe(EventType.INTERVIEWER_RESPONSE, self._handle_interviewer_response)
            self.event_bus.subscribe(EventType.USER_RESPONSE, self._handle_user_response)
            self.event_bus.subscribe(EventType.INTERVIEW_SUMMARY, self._handle_interview_summary)
    
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
            output_parser=JsonOutputParser(),
            output_key="proficiency_assessment"
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
            output_parser=JsonOutputParser(),
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
            
            # Emit event with extracted skills
            if self.event_bus:
                self.event_bus.emit(Event(
                    event_type=EventType.SKILL_EXTRACTED,
                    data={"skills": result["extracted_skills"]},
                    source="skill_assessor"
                ))
                
            return result["extracted_skills"]
        except Exception as e:
            self.logger.error(f"Error extracting skills: {e}")
            # Fallback to simpler extraction method
            skills = self._identify_skills_in_text(response)
            
            # Format skills for consistency
            formatted_skills = [
                {
                    "skill_name": skill[0], 
                    "category": skill[1], 
                    "confidence": 0.7
                } 
                for skill in skills
            ]
            
            return formatted_skills
    
    def _assess_proficiency_tool(self, skill: str, context: str) -> Dict[str, Any]:
        """
        Tool function to assess proficiency level for a skill.
        
        Args:
            skill: The skill to assess
            context: The context to use for assessment
            
        Returns:
            Dictionary with proficiency assessment
        """
        try:
            result = self.proficiency_chain.invoke({
                "skill": skill,
                "job_role": self.job_role,
                "context": context
            })
            
            # Emit event with proficiency assessment
            if self.event_bus:
                self.event_bus.emit(Event(
                    event_type=EventType.SKILL_ASSESSED,
                    data={
                        "skill": skill,
                        "proficiency": result["proficiency_level"],
                        "feedback": result.get("feedback", "")
                    },
                    source="skill_assessor"
                ))
                
            return result
        except Exception as e:
            self.logger.error(f"Error assessing proficiency: {e}")
            return {
                "proficiency_level": "intermediate",
                "feedback": "Unable to assess proficiency accurately.",
                "confidence": 0.5
            }
    
    def _suggest_resources_tool(self, skill: str, proficiency_level: str) -> Dict[str, Any]:
        """
        Tool function to suggest resources for improving a skill.
        
        Args:
            skill: The skill to suggest resources for
            proficiency_level: Current proficiency level
            
        Returns:
            Dictionary with suggested resources
        """
        try:
            # Check if resources are already cached
            if skill in self.resource_cache:
                return {"resources": self.resource_cache[skill]}
            
            # Try to get resources using the search service first
            search_resources = self._get_resources_using_search(skill, proficiency_level)
            
            # If search service returns resources, use them
            if search_resources and len(search_resources) > 0:
                # Cache the resources
                self.resource_cache[skill] = search_resources
                
                # Emit event with resource suggestions
                if self.event_bus:
                    self.event_bus.emit(Event(
                        event_type=EventType.RESOURCES_SUGGESTED,
                        data={
                            "skill": skill,
                            "resources": search_resources
                        },
                        source="skill_assessor"
                    ))
                    
                return {"resources": search_resources}
            
            # Fallback to LLM-based resource generation
            result = self.resource_chain.invoke({
                "skill": skill,
                "proficiency_level": proficiency_level,
                "job_role": self.job_role
            })
            
            # Cache the resources
            self.resource_cache[skill] = result["resources"]
            
            # Emit event with resource suggestions
            if self.event_bus:
                self.event_bus.emit(Event(
                    event_type=EventType.RESOURCES_SUGGESTED,
                    data={
                        "skill": skill,
                        "resources": result["resources"]
                    },
                    source="skill_assessor"
                ))
                
            return result
        except Exception as e:
            self.logger.error(f"Error suggesting resources: {e}")
            # Fallback to simpler resource generation
            resources_json = self._get_resources_for_skill(skill, proficiency_level)
            resources = json.loads(resources_json)
            return resources
    
    def _create_skill_profile_tool(self, skills_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Tool function to create a comprehensive skill profile.
        
        Args:
            skills_data: List of skills with assessment data
            
        Returns:
            Dictionary with skill profile
        """
        try:
            skills_json = json.dumps(skills_data)
            result = self.profile_chain.invoke({
                "skills": skills_json,
                "job_role": self.job_role
            })
            
            # Emit event with skill profile
            if self.event_bus:
                self.event_bus.emit(Event(
                    event_type=EventType.SKILL_PROFILE_GENERATED,
                    data={"profile": result},
                    source="skill_assessor"
                ))
                
            return result
        except Exception as e:
            self.logger.error(f"Error creating skill profile: {e}")
            # Return a simple profile
            return {
                "overall_assessment": "Profile generation encountered an error.",
                "strengths": [],
                "areas_for_improvement": [],
                "recommended_learning_path": "Retry profile generation."
            }
    
    def _initialize_skill_keywords(self) -> Dict[str, List[str]]:
        """
        Initialize keywords for skill extraction.
        
        Returns:
            Dictionary of skill categories to keywords
        """
        # Get skills for the job role, or use default if not found
        if self.job_role.lower() in self.role_skills:
            role_skills = self.role_skills[self.job_role.lower()]
        else:
            # Use software engineer as default
            role_skills = self.role_skills["software engineer"]
        
        # Combine all skills into a single dictionary
        all_skills = {}
        for category, skills in role_skills.items():
            all_skills[category] = skills
        
        return all_skills
    
    def _identify_skills_in_text(self, text: str) -> List[Tuple[str, str]]:
        """
        Identify skills mentioned in text using keyword matching.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of (skill, category) tuples
        """
        text = text.lower()
        found_skills = []
        
        # Check each category of skills
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                # Check if skill is mentioned as a whole word
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text):
                    found_skills.append((skill, category))
        
        return found_skills
    
    def _handle_interviewer_response(self, event: Event) -> None:
        """
        Handle interviewer response event.
        
        Args:
            event: The event with interviewer response
        """
        if event.data and "question" in event.data:
            self.current_question = event.data["question"]
    
    def _handle_user_response(self, event: Event) -> None:
        """
        Handle user response event.
        
        Args:
            event: The event with user response
        """
        if event.data and "answer" in event.data:
            self.current_answer = event.data["answer"]
            self._analyze_response(self.current_answer)
    
    def _handle_interview_summary(self, event: Event) -> None:
        """
        Handle interview summary event.
        
        Args:
            event: The event with interview summary
        """
        if event.data and "summary" in event.data:
            # Analyze the full interview summary for skills
            self._analyze_response(event.data["summary"])
            
            # Generate and emit a comprehensive skill profile
            if self.identified_skills:
                skills_data = []
                for skill_name, data in self.identified_skills.items():
                    skills_data.append({
                        "skill_name": skill_name,
                        "category": data.get("category", "unknown"),
                        "proficiency_level": data.get("proficiency_level", "intermediate"),
                        "feedback": data.get("feedback", ""),
                        "mentions": self.skill_mentions.get(skill_name, 1)
                    })
                
                self._create_skill_profile_tool(skills_data)
    
    def _analyze_response(self, response: str) -> None:
        """
        Analyze a response for skills.
        
        Args:
            response: The response to analyze
        """
        # Extract skills from the response
        extracted_skills = self._extract_skills_tool(response)
        
        # Update skill mention counts
        for skill_data in extracted_skills:
            skill_name = skill_data["skill_name"].lower()
            self.skill_mentions[skill_name] = self.skill_mentions.get(skill_name, 0) + 1
            
            # If this is a new skill or has high confidence, assess proficiency
            if (skill_name not in self.identified_skills or 
                skill_data.get("confidence", 0) > self.identified_skills[skill_name].get("confidence", 0)):
                
                # Assess proficiency for the skill
                assessment = self._assess_proficiency_tool(skill_name, response)
                
                # Store the assessment data
                self.identified_skills[skill_name] = {
                    "skill_name": skill_name,
                    "category": skill_data.get("category", "unknown"),
                    "proficiency_level": assessment.get("proficiency_level", "intermediate"),
                    "feedback": assessment.get("feedback", ""),
                    "confidence": skill_data.get("confidence", 0.7),
                    "last_updated": datetime.now()
                }
                
                # Get resources for skill improvement
                resources = self._suggest_resources_tool(
                    skill_name, 
                    assessment.get("proficiency_level", "intermediate")
                )
                
                # Store resources
                self.identified_skills[skill_name]["resources"] = resources.get("resources", [])
        
        self.last_assessment_time = datetime.now()
    
    def _get_resources_for_skill(self, skill: str, proficiency_level: str = "intermediate") -> str:
        """
        Get learning resources for a specific skill.
        
        Args:
            skill: The skill to get resources for
            proficiency_level: Proficiency level for appropriate resources
            
        Returns:
            JSON string with resources
        """
        # Check cache first
        if skill in self.resource_cache:
            return json.dumps({"resources": self.resource_cache[skill]})
            
        # Try to get resources using the search service first
        search_resources = self._get_resources_using_search(skill, proficiency_level)
        
        # If search service returns resources, use them
        if search_resources and len(search_resources) > 0:
            # Cache the resources
            self.resource_cache[skill] = search_resources
            return json.dumps({"resources": search_resources})
            
        # Fallback to generating mock resources
        # Construct resource types
        resource_types = ["online_course", "book", "article", "tutorial"]
        
        # Generate resources based on skill
        resources = []
        
        for _ in range(4):  # Generate 4 resources
            resource_type = random.choice(resource_types)
            
            # Create resource based on type
            if resource_type == "online_course":
                platforms = ["Coursera", "Udemy", "edX", "Pluralsight", "LinkedIn Learning"]
                title = f"{random.choice(['Complete', 'Advanced', 'Comprehensive', 'Practical'])} {skill.title()} {random.choice(['Course', 'Masterclass', 'Bootcamp'])}"
                url = f"https://www.{random.choice(platforms).lower().replace(' ', '')}.com/{skill.lower().replace(' ', '-')}"
                description = f"Learn {skill} from experts with hands-on projects and exercises."
                
            elif resource_type == "book":
                publishers = ["O'Reilly", "Packt", "Manning", "Apress", "Wiley"]
                title = f"{random.choice(['Mastering', 'Learning', 'Professional', 'Practical'])} {skill.title()}"
                url = f"https://www.amazon.com/books/{skill.lower().replace(' ', '-')}"
                description = f"Comprehensive guide to {skill} with practical examples and best practices."
                
            elif resource_type == "article":
                platforms = ["Medium", "Dev.to", "Towards Data Science", "HackerNoon"]
                title = f"{random.choice(['Understanding', 'Mastering', 'Deep Dive into', 'Practical Guide to'])} {skill.title()}"
                url = f"https://www.{random.choice(platforms).lower().replace(' ', '').replace('.', '')}.com/articles/{skill.lower().replace(' ', '-')}"
                description = f"In-depth article explaining key concepts of {skill} with practical examples."
                
            else:  # tutorial
                platforms = ["YouTube", "freeCodeCamp", "W3Schools", "TutorialsPoint"]
                title = f"{skill.title()} {random.choice(['Tutorial', 'Guide', 'Walkthrough', 'Masterclass'])}"
                url = f"https://www.{random.choice(platforms).lower().replace(' ', '')}.com/tutorials/{skill.lower().replace(' ', '-')}"
                description = f"Step-by-step tutorial for learning {skill} from scratch."
            
            resources.append({
                "type": resource_type,
                "title": title,
                "url": url,
                "description": description,
                "relevance_score": round(random.uniform(0.7, 0.95), 2)
            })
        
        # Cache the resources
        self.resource_cache[skill] = resources
        
        return json.dumps({"resources": resources})
    
    def _get_resources_using_search(self, skill: str, proficiency_level: str) -> List[Dict[str, Any]]:
        """
        Get resources for a skill using the search service.
        
        Args:
            skill: The skill to get resources for
            proficiency_level: Current proficiency level
            
        Returns:
            List of resource dictionaries
        """
        try:
            # Get the search service instance
            search_service = get_search_service()
            
            # Use asyncio to run the async search method
            loop = asyncio.get_event_loop()
            resources = loop.run_until_complete(
                search_service.search_resources(
                    skill=skill,
                    proficiency_level=proficiency_level,
                    job_role=self.job_role,
                    num_results=5
                )
            )
            
            # Convert Resource objects to dictionaries
            resource_dicts = []
            for resource in resources:
                # Map resource_type to type expected by the system
                resource_type_mapping = {
                    "article": "article",
                    "course": "online_course",
                    "video": "video",
                    "tutorial": "tutorial",
                    "documentation": "documentation",
                    "book": "book",
                    "tool": "tool",
                    "community": "community",
                    "unknown": "article"
                }
                
                resource_dict = {
                    "type": resource_type_mapping.get(resource.resource_type, "article"),
                    "title": resource.title,
                    "url": resource.url,
                    "description": resource.description,
                    "relevance_score": resource.relevance_score
                }
                resource_dicts.append(resource_dict)
            
            self.logger.info(f"Found {len(resource_dicts)} resources for {skill} using search service")
            return resource_dicts
            
        except Exception as e:
            self.logger.error(f"Error getting resources from search service: {e}")
            return []
    
    def process_input(self, user_input: str, context: AgentContext) -> str:
        """
        Process user input and provide a response.
        
        Args:
            user_input: The user's input message
            context: The agent context
            
        Returns:
            Response string
        """
        # Store context
        self.interview_session_id = context.session_id
        
        # Process the input using the base class method or rule-based
        try:
            response = self._process_input_rule_based(user_input, context)
            if response:
                return response
                
            # Fallback to LLM-based processing
            return super().process_input(user_input, context)
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            return "I'm analyzing your skills based on our conversation. Could you tell me more about your experience with specific technologies or methodologies?"
    
    def _process_input_rule_based(self, user_input: str, context: AgentContext) -> Optional[str]:
        """
        Process user input using rule-based approaches.
        
        Args:
            user_input: The user's input message
            context: The agent context
            
        Returns:
            Response string or None
        """
        input_lower = user_input.lower()
        
        # Analyze the response for skills
        self._analyze_response(user_input)
        
        # Check if the user is asking about their skills
        if "what skills" in input_lower or "which skills" in input_lower or "my skills" in input_lower:
            if not self.identified_skills:
                return "I haven't identified any specific skills yet. Could you tell me more about your experience and the technologies you've worked with?"
                
            skills_list = ", ".join(self.identified_skills.keys())
            return f"Based on our conversation, I've identified these skills: {skills_list}. Would you like me to provide a detailed assessment of any specific skill?"
        
        # Check if the user is asking about a specific skill
        if "how is my" in input_lower and "skill" in input_lower:
            # Extract the skill from the query
            skill_match = re.search(r'how is my (\w+)', input_lower)
            if skill_match:
                skill = skill_match.group(1)
                if skill in self.identified_skills:
                    assessment = self.identified_skills[skill]
                    return f"For {skill}, I assess your proficiency as {assessment['proficiency_level']}. {assessment.get('feedback', '')}"
                else:
                    return f"I haven't been able to assess your {skill} skill yet. Could you tell me more about your experience with it?"
        
        # Check if the user wants resources for a skill
        if "resources" in input_lower or "improve" in input_lower:
            # Try to extract a skill from the query
            for skill in self.identified_skills:
                if skill in input_lower:
                    resources = self.identified_skills[skill].get("resources", [])
                    if resources:
                        response = f"Here are some resources to improve your {skill} skills:\n"
                        for i, resource in enumerate(resources[:3], 1):
                            response += f"{i}. {resource['title']} - {resource['url']}\n"
                        return response
                    else:
                        # Generate resources
                        resources_json = self._get_resources_for_skill(skill)
                        resources = json.loads(resources_json)["resources"]
                        response = f"Here are some resources to improve your {skill} skills:\n"
                        for i, resource in enumerate(resources[:3], 1):
                            response += f"{i}. {resource['title']} - {resource['url']}\n"
                        return response
        
        # No rule-based response
        return None
    
    def generate_skill_profile(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate a comprehensive skill profile based on the identified skills.
        
        Args:
            context: The agent context
            
        Returns:
            Dictionary with skill profile
        """
        if not self.identified_skills:
            return {
                "overall_assessment": "Not enough information to generate a skill profile.",
                "strengths": [],
                "areas_for_improvement": [],
                "recommended_learning_path": "Continue the conversation to allow for skill assessment."
            }
        
        # Prepare skills data
        skills_data = []
        for skill_name, data in self.identified_skills.items():
            skills_data.append({
                "skill_name": skill_name,
                "category": data.get("category", "unknown"),
                "proficiency_level": data.get("proficiency_level", "intermediate"),
                "feedback": data.get("feedback", ""),
                "mentions": self.skill_mentions.get(skill_name, 1)
            })
        
        # Generate profile
        return self._create_skill_profile_tool(skills_data)
    
    def get_resources_for_skill(self, skill_name: str, context: AgentContext) -> List[Dict[str, Any]]:
        """
        Get resources for improving a specific skill.
        
        Args:
            skill_name: The skill to get resources for
            context: The agent context
            
        Returns:
            List of resource dictionaries
        """
        if skill_name in self.identified_skills and "resources" in self.identified_skills[skill_name]:
            return self.identified_skills[skill_name]["resources"]
        
        # Generate resources
        proficiency = "intermediate"  # Default
        if skill_name in self.identified_skills:
            proficiency = self.identified_skills[skill_name].get("proficiency_level", "intermediate")
            
        result = self._suggest_resources_tool(skill_name, proficiency)
        return result.get("resources", []) 