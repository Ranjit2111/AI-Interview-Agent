"""
Skill assessor agent that evaluates a user's technical competencies during the interview.
This agent identifies skills demonstrated, assesses proficiency levels, and suggests resources for improvement.
"""

import logging
import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime
from enum import Enum

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

try:
    # Try standard import in production
    from backend.agents.base import BaseAgent, AgentContext
    from backend.utils.event_bus import Event, EventBus, EventType
    from backend.services.llm_service import LLMService
    from backend.services.search_service import Resource
    from backend.agents.templates.skill_templates import (
        SKILL_SYSTEM_PROMPT,
        SKILL_EXTRACTION_TEMPLATE,
        PROFICIENCY_ASSESSMENT_TEMPLATE,
        RESOURCE_SUGGESTION_TEMPLATE,
        SKILL_PROFILE_TEMPLATE
    )
    from backend.utils.llm_utils import invoke_chain_with_error_handling
except ImportError:
    # Use relative imports for development/testing
    from .base import BaseAgent, AgentContext
    from ..utils.event_bus import Event, EventBus, EventType
    from ..services.llm_service import LLMService
    from ..services.search_service import Resource
    from .templates.skill_templates import (
        SKILL_SYSTEM_PROMPT,
        SKILL_EXTRACTION_TEMPLATE,
        PROFICIENCY_ASSESSMENT_TEMPLATE,
        RESOURCE_SUGGESTION_TEMPLATE,
        SKILL_PROFILE_TEMPLATE
    )
    from ..utils.llm_utils import invoke_chain_with_error_handling


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
        llm_service: LLMService,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        job_role: str = "",
        technical_focus: bool = True
    ):
        """
        Initialize the skill assessor agent.
        
        Args:
            llm_service: Language model service
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            job_role: Target job role for skill relevance
            technical_focus: Whether to focus on technical skills
        """
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.job_role = job_role
        self.technical_focus = technical_focus
        self.interview_session_id = None
        self.current_question = None
        self.current_answer = None
        self.identified_skills: Dict[str, Dict[str, Any]] = {}  # Store assessment data per skill
        self.skill_mentions: Dict[str, int] = {} # Count mentions per skill
        self.resource_cache: Dict[str, List[Dict[str, Any]]] = {}  # Cache resources per skill
        self.last_assessment_time = None
        
        # Setup LLM chains using self.llm from llm_service
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
        
        self.skill_keywords = self._initialize_skill_keywords()
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe(EventType.INTERVIEWER_RESPONSE, self._handle_interviewer_response)
            self.event_bus.subscribe(EventType.USER_MESSAGE, self._handle_user_response)
            self.event_bus.subscribe(EventType.INTERVIEW_SUMMARY, self._handle_interview_summary)
            self.event_bus.subscribe(EventType.SESSION_START, self._handle_session_start)
            self.event_bus.subscribe(EventType.SESSION_RESET, self._handle_session_reset)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the skill assessor agent.
        
        Returns:
            System prompt string
        """
        return SKILL_SYSTEM_PROMPT.format(job_role=self.job_role or "[Not Specified]")
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains using self.llm.
        """
        # Skill extraction chain
        self.skill_extraction_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(SKILL_EXTRACTION_TEMPLATE)
        )
        
        # Proficiency assessment chain
        self.proficiency_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(PROFICIENCY_ASSESSMENT_TEMPLATE)
        )
        
        # Resource suggestion chain (fallback if search fails)
        self.resource_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(RESOURCE_SUGGESTION_TEMPLATE)
        )
        
        # Skill profile chain (for generating the final profile)
        self.profile_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(SKILL_PROFILE_TEMPLATE)
        )
    
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
    
    def _handle_interviewer_response(self, event: Event) -> None:
        """
        Handle interviewer response event.
        
        Args:
            event: The event with interviewer response
        """
        # Corrected: Check for nested 'response' key
        if not event.data or 'response' not in event.data:
            self.logger.warning("Received interviewer event without 'response' data.")
            return
        # Corrected: Access content from nested structure
        self.current_question = event.data['response'].get("content")
        self.logger.debug(f"SkillAssessor stored current question: {self.current_question[:50]}...")
    
    def _handle_user_response(self, event: Event) -> None:
        """
        Handle user response event.
        
        Args:
            event: The event with user response
        """
        # Corrected: Check for nested 'message' key
        if not event.data or 'message' not in event.data:
            self.logger.warning("Received user response event without 'message' data.")
            return
        # Corrected: Access content from nested structure
        self.current_answer = event.data['message'].get("content")
        self.logger.debug(f"SkillAssessor received answer: {self.current_answer[:50]}...")
        
        # Trigger analysis of the received answer
        if self.current_answer:
            self._analyze_single_response(self.current_answer)
    
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
        extracted_skills = self._extract_skills(response)
        
        # Update skill mention counts
        for skill_data in extracted_skills:
            skill_name = skill_data["skill_name"].lower()
            self.skill_mentions[skill_name] = self.skill_mentions.get(skill_name, 0) + 1
            
            # If this is a new skill or has high confidence, assess proficiency
            if (skill_name not in self.identified_skills or 
                skill_data.get("confidence", 0) > self.identified_skills[skill_name].get("confidence", 0)):
                
                # Assess proficiency for the skill
                assessment = self._assess_proficiency(skill_name, response)
                
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
                resources = self._suggest_resources(
                    skill_name, 
                    assessment.get("proficiency_level", "intermediate")
                )
                
                # Store resources
                self.identified_skills[skill_name]["resources"] = resources.get("resources", [])
        
        self.last_assessment_time = datetime.now()
    
    def _extract_skills(self, response: str) -> List[Dict[str, Any]]:
        """
        Extracts skills from text using an LLM chain.
        
        Args:
            response: The text to extract skills from
            
        Returns:
            List of skill dictionaries
        """
        default_skills = [] # Fallback value
        extracted_data = invoke_chain_with_error_handling(
            chain=self.skill_extraction_chain,
            inputs={"job_role": self.job_role or "[Not Specified]", "response": response},
            logger=self.logger,
            chain_name="Skill Extraction Chain",
            output_key="extracted_skills", # Expecting JSON output under this key
            default_creator=lambda: default_skills
        )

        # Validate the structure (should be a list of dicts)
        if isinstance(extracted_data, list) and all(isinstance(item, dict) for item in extracted_data):
            # Emit event (consider adding session_id if available)
            self.publish_event(EventType.SKILL_EXTRACTED, {"skills": extracted_data})
            return extracted_data
        else:
            self.logger.warning(f"Skill extraction returned invalid data type: {type(extracted_data)}. Falling back.")
            # Fallback to simpler keyword extraction
            skills_tuples = self._identify_skills_in_text(response)
            formatted_fallback = [
                {"skill_name": skill[0], "category": skill[1], "confidence": 0.6} 
                for skill in skills_tuples
            ]
            if formatted_fallback:
                self.publish_event(EventType.SKILL_EXTRACTED, {"skills": formatted_fallback, "fallback_used": True})
            return formatted_fallback
    
    def _assess_proficiency(self, skill: str, context: str) -> Dict[str, Any]:
        """
        Assess proficiency level for a skill using an LLM chain.
        
        Args:
            skill: The skill to assess
            context: The context for the assessment
            
        Returns:
            Dictionary with proficiency assessment data
        """
        default_assessment = {
            "proficiency_level": ProficiencyLevel.INTERMEDIATE.value,
            "confidence": 0.5,
            "justification": "Default assessment due to processing error."
        }
        assessment_data = invoke_chain_with_error_handling(
            chain=self.proficiency_chain,
            inputs={"skill": skill, "job_role": self.job_role or "[Not Specified]", "context": context},
            logger=self.logger,
            chain_name="Proficiency Assessment Chain",
            output_key="proficiency_assessment", 
            default_creator=lambda: default_assessment
        )
        
        # Basic validation of the parsed dictionary
        if isinstance(assessment_data, dict) and \
           isinstance(assessment_data.get("proficiency_level"), str) and \
           isinstance(assessment_data.get("confidence"), (int, float)):
            # Validate enum value
            try:
                ProficiencyLevel(assessment_data["proficiency_level"])
                assessment_data["confidence"] = float(assessment_data["confidence"])
                # Emit event
                self.publish_event(EventType.SKILL_ASSESSED, {
                    "skill": skill,
                    "proficiency": assessment_data["proficiency_level"],
                    "confidence": assessment_data["confidence"],
                    "justification": assessment_data.get("justification", "N/A")
                })
                return assessment_data
            except ValueError:
                self.logger.warning(f"Invalid proficiency level '{assessment_data['proficiency_level']}' received, using default.")
                return default_assessment
        else:
            self.logger.error(f"Proficiency assessment returned invalid data: {assessment_data}")
            return default_assessment
    
    async def _suggest_resources(self, skill: str, proficiency_level: str) -> List[Dict[str, Any]]:
        """
        Suggest resources, trying search service first, then LLM fallback.

        Args:
            skill: The skill to get resources for
            proficiency_level: Current proficiency level

        Returns:
            List of resource dictionaries
        """
        cache_key = f"{skill.lower()}_{proficiency_level.lower()}"
        if cache_key in self.resource_cache:
            self.logger.debug(f"Returning cached resources for {skill} ({proficiency_level})")
            return self.resource_cache[cache_key]

        resources = []
        search_service_used = False
        try:
            try:
                from backend.services import get_search_service
            except ImportError:
                from ..services import get_search_service
                
            search_service = get_search_service()
            if search_service:
                self.logger.debug(f"Attempting to use search service for {skill} resources...")
                
                search_service_results: List[Resource] = await search_service.search_resources(
                    skill=skill,
                    proficiency_level=proficiency_level,
                    job_role=self.job_role, # Pass the agent's job_role
                    num_results=3 # Keep num_results or make configurable
                )
                
                if search_service_results:
                    resources = [] # Ensure resources is initialized here
                    for res_obj in search_service_results: # res_obj is a Resource instance
                        resources.append({
                            "title": res_obj.title, 
                            "url": res_obj.url, 
                            "type": res_obj.resource_type, # Access attribute
                            "snippet": res_obj.description # Access attribute
                        })
                    search_service_used = True
                    self.logger.info(f"Found {len(resources)} resources for '{skill}' via search service.")
                else:
                    self.logger.warning(f"Search service returned no results for skill: {skill}, proficiency: {proficiency_level}")
            else:
                self.logger.warning("Search service is not available.")

        except Exception as e:
            self.logger.error(f"Error using search service for skill '{skill}': {e}", exc_info=True)

        # Fallback to LLM if search failed or no results
        if not search_service_used:
            self.logger.info(f"Using LLM fallback for '{skill}' resources.")
            
            llm_response = invoke_chain_with_error_handling(
                chain=self.resource_chain,
                inputs={"skill": skill, "proficiency_level": proficiency_level, "job_role": self.job_role or "[Not Specified]"},
                logger=self.logger,
                chain_name="Resource Suggestion Chain",
                output_key="resources", # Expecting JSON list output
                default_creator=lambda: []
            )
            if isinstance(llm_response, list):
                # Basic validation of resource structure
                validated_resources = []
                for r in llm_response:
                    if isinstance(r, dict) and "title" in r and "url" in r:
                        validated_resources.append({
                            "type": r.get("type", "link"),
                            "title": r["title"],
                            "url": r["url"],
                            "description": r.get("description", "")
                        })
                resources = validated_resources
                if not resources:
                    self.logger.warning(f"LLM resource suggestion for '{skill}' returned list with invalid structure.")
            else:
                self.logger.warning(f"LLM resource suggestion for '{skill}' did not return a list. Got: {type(llm_response)}")
                resources = [] # Ensure empty list on failure

        # Cache results (even if empty)
        self.resource_cache[cache_key] = resources
        
        # Publish event only if resources were actually found
        if resources:
            self.publish_event(EventType.RESOURCES_SUGGESTED, {"skill": skill, "resources": resources})
            
        return resources
    
    def generate_skill_profile(self) -> Dict[str, Any]:
        """
        Generates a comprehensive skill profile based on accumulated assessments.
        
        Returns:
            Dictionary with the structured skill profile (skills and levels)
        """
        self.logger.info("Generating skill profile...")
        default_profile = {
            "job_role": self.job_role or "[Not Specified]",
            "assessed_skills": []
            # Removed summary, recommendations etc. - template defines output structure
        }
        
        if not self.identified_skills:
            self.logger.warning("No skills identified to generate profile.")
            return default_profile
        
        # Prepare skills data for the profile chain template
        skills_data_for_prompt = []
        for skill_name, data in self.identified_skills.items():
            skills_data_for_prompt.append({
                "skill_name": skill_name,
                "category": data.get("category", "unknown"),
                "assessed_proficiency": data.get("proficiency_level", "intermediate"),
                "assessment_confidence": data.get("confidence", 0.5),
                "assessment_justification": data.get("justification", "N/A"),
                "evidence_mentions": self.skill_mentions.get(skill_name, 1)
            })
        
        profile_data = invoke_chain_with_error_handling(
            chain=self.profile_chain,
            inputs={
                "skills_json": json.dumps(skills_data_for_prompt),
                "job_role": self.job_role or "[Not Specified]"
            },
            logger=self.logger,
            chain_name="Skill Profile Generation Chain",
            output_key="skill_profile", # Expecting JSON output
            default_creator=lambda: default_profile
        )

        # Basic validation
        if isinstance(profile_data, dict) and "assessed_skills" in profile_data:
            self.logger.info(f"Skill profile generated successfully for {len(profile_data['assessed_skills'])} skills.")
            # Publish event
            self.publish_event(EventType.SKILL_PROFILE_GENERATED, {"profile": profile_data})
            return profile_data
        else:
            self.logger.error(f"Skill profile generation returned invalid data: {profile_data}")
            return default_profile
    
    def _identify_skills_in_text(self, text: str) -> List[Tuple[str, str]]:
        """
        Identify skills mentioned in text using keyword matching.
        
        Args:
            text: The text to extract skills from
            
        Returns:
            List of tuples (skill, category)
        """
        text_lower = text.lower()
        found_skills = []
        # Use the initialized keywords
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    # Return the original skill name casing if needed, but lowercase match is fine
                    found_skills.append((skill, category))
        # Remove duplicates while preserving order (if needed, though set is faster)
        seen = set()
        unique_found = []
        for skill, cat in found_skills:
            if skill not in seen:
                unique_found.append((skill, cat))
                seen.add(skill)
        return unique_found
    
    def _handle_session_start(self, event: Event) -> None:
        """
        Handles session start to get config and reset state.
        
        Args:
            event: The session start event object
        """
        self.logger.info(f"SkillAssessorAgent handling {event.event_type}.")
        self._reset_state() # Reset state first
        
        # Extract config from event data and update attributes
        if event.data and 'config' in event.data:
            config_data = event.data['config']
            self.logger.info(f"SkillAssessorAgent updating config from event: {config_data}")
            self.job_role = config_data.get('job_role', "")
            # Add other config updates if needed by skill assessor
            # self.technical_focus = config_data.get('technical_focus', True)
            
            # Re-initialize skill keywords based on the potentially new job role
            self.skill_keywords = self._initialize_skill_keywords()
            self.logger.info(f"Re-initialized skill keywords for job role: {self.job_role}")
        else:
             self.logger.warning("SESSION_START event received without config data.")
            
    
    def _handle_session_reset(self, event: Event) -> None:
        """
        Handles session reset event.
        
        Args:
            event: The event with session reset
        """
        self.logger.info("SkillAssessor handling session_reset event.")
        self._reset_state()
    
    def _reset_state(self) -> None:
        """
        Resets the internal state of the SkillAssessor.
        """
        self.interview_session_id = None
        self.current_question = None
        self.current_answer = None
        self.identified_skills = {}
        self.skill_mentions = {}
        self.resource_cache = {}
        self.logger.debug("SkillAssessor state reset.")
    
    def _analyze_single_response(self, response: str) -> None:
        """
        Analyzes a single user response to extract and assess skills.
        
        Args:
            response: The response to analyze
        """
        self.logger.debug(f"Analyzing response for skills: {response[:100]}...")
        extracted_skills = self._extract_skills(response)
        
        for skill_data in extracted_skills:
            skill_name = skill_data.get("skill_name", "").lower()
            if not skill_name:
                continue
            
            category = skill_data.get("category", "unknown")
            confidence = skill_data.get("confidence", 0.6) # Default confidence if missing
            
            # Update mention count
            self.skill_mentions[skill_name] = self.skill_mentions.get(skill_name, 0) + 1
            
            # Assess proficiency (only if confidence is high enough or skill is new)
            assessment_threshold = 0.7
            if confidence >= assessment_threshold or skill_name not in self.identified_skills:
                # Use question+answer as context if available
                assessment_context = f"Question: {self.current_question}\nAnswer: {response}" \
                                     if self.current_question else response
                                    
                assessment = self._assess_proficiency(skill_name, assessment_context)
                
                # Update stored skill data if assessment confidence is good
                if assessment.get("confidence", 0) > 0.5:
                    self.identified_skills[skill_name] = {
                        "skill_name": skill_name,
                        "category": category,
                        "proficiency_level": assessment.get("proficiency_level", ProficiencyLevel.INTERMEDIATE.value),
                        "justification": assessment.get("justification", "N/A"),
                        "confidence": assessment.get("confidence"),
                        "last_updated": datetime.now().isoformat()
                    }
                    self.logger.info(f"Assessed/Updated skill: '{skill_name}' to level '{self.identified_skills[skill_name]['proficiency_level']}'")
                    # Suggest resources on demand via get_suggested_resources
                else:
                    self.logger.debug(f"Skipping proficiency update for '{skill_name}' due to low assessment confidence ({assessment.get('confidence'):.2f})")
            else:
                self.logger.debug(f"Skipping proficiency assessment for '{skill_name}' (confidence {confidence:.2f} < {assessment_threshold} or already assessed). Update mention count only.")
    
    def process(self, context: AgentContext) -> Any:
        """
        Default process method. SkillAssessor is primarily reactive via event handlers
        or specific method calls from SessionManager (e.g., generate_skill_profile).
        
        Args:
            context: The agent context
            
        Returns:
            Any result from the process
        """
        self.logger.debug("SkillAssessor process method called (typically inactive). Context received.")
        # Potential future use: Trigger analysis based on full context
        # if context.conversation_history:
        #     self._analyze_single_response(context.conversation_history[-1].get('content', ''))
        return None # No direct response generation
    
    def get_suggested_resources(self, skill_name: str) -> List[Dict[str, Any]]:
        """
        Gets suggested resources for a specific skill, triggering generation if needed.
        Called explicitly by SessionManager or potentially another agent.
        
        Args:
            skill_name: The skill to get resources for
            
        Returns:
            List of resource dictionaries
        """
        skill_name_lower = skill_name.lower()
        proficiency = ProficiencyLevel.INTERMEDIATE.value # Default
        if skill_name_lower in self.identified_skills:
            proficiency = self.identified_skills[skill_name_lower].get("proficiency_level", proficiency)
        
        # This now handles caching and generation logic
        return self._suggest_resources(skill_name_lower, proficiency)
    
    def _create_skill_profile_tool(self, skills_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive skill profile from accumulated skill data.
        
        Args:
            skills_data: List of skill dictionaries with assessment data
            
        Returns:
            Structured skill profile
        """
        self.logger.info(f"Creating skill profile from {len(skills_data)} identified skills.")
        
        try:
            # Use the existing generate_skill_profile method which already does most of the work
            profile = self.generate_skill_profile()
            
            # Add additional context about when the profile was generated
            profile["generated_at"] = datetime.now().isoformat()
            profile["skills_count"] = len(skills_data)
            
            # Publish event with the generated skill profile
            self.publish_event(EventType.SKILL_ASSESSMENT, {
                "skill_profile": profile,
                "skills_count": len(skills_data)
            })
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error creating skill profile: {e}", exc_info=True)
            return {
                "error": "Failed to generate skill profile",
                "job_role": self.job_role or "[Not Specified]",
                "reason": str(e)
            }