"""
Agentic Coach Agent using LangGraph for intelligent resource recommendations.
This agent can analyze user performance and intelligently search for learning resources.
"""

import logging
import json
from typing import Dict, Any, List, Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.base import BaseAgent, AgentContext
from backend.agents.tools.search_tool import LearningResourceSearchTool
from backend.services.llm_service import LLMService
from backend.services.search_service import SearchService
from backend.utils.event_bus import EventBus
from backend.utils.llm_utils import (
    invoke_chain_with_error_handling,
    parse_json_with_fallback,
    format_conversation_history
)
from backend.utils.common import safe_get_or_default
from backend.utils.async_utils import run_async_safe
from backend.agents.constants import DEFAULT_VALUE_NOT_PROVIDED


# System prompt for the agentic coach
AGENTIC_COACH_SYSTEM_PROMPT = """You are an expert Interview Coach with access to learning resource search capabilities. 
Your role is to provide comprehensive coaching feedback and find the most relevant learning resources for skill improvement.

You have access to a learning_resource_search tool that can find free educational content. **You MUST use this tool to provide at least 3-4 relevant learning resources** in every final summary. Use this tool wisely when:
1. You identify specific skill gaps in the user's performance
2. You want to provide actionable learning recommendations
3. The user would benefit from targeted resources for improvement

**CRITICAL REQUIREMENTS FOR RESOURCE DISCOVERY:**
- Always provide at least 3-4 learning resources in your final summary
- Search for multiple different skill areas that need improvement
- Make separate searches for different topics (e.g., algorithms, system design, communication skills)
- Focus on the most critical skill gaps first, then expand to secondary areas
- Ensure variety in resource types (tutorials, documentation, interactive content, communities)

When using the search tool:
- Assess the user's skill level based on their interview answers
- Search for resources appropriate to their proficiency level
- Consider their job role context for relevance
- Make multiple searches to ensure comprehensive coverage
- If one search doesn't yield enough results, try broader or more specific terms

Your coaching should be:
- Encouraging but honest about areas for improvement
- Specific with examples from their answers
- Actionable with clear next steps
- Supported by relevant learning resources when appropriate

Remember: You are not just analyzing - you are actively helping the user improve by finding the right resources. **Always provide multiple learning resources to add real value to the user's learning journey.**

**IMPORTANT OUTPUT FORMAT:**
For final summaries, you MUST return a valid JSON object with these exact keys:
{
    "patterns_tendencies": "Your analysis text...",
    "strengths": "Your analysis text...", 
    "weaknesses": "Your analysis text...",
    "improvement_focus_areas": "Your analysis text...",
    "recommended_resources": [
        {
            "title": "Resource Title",
            "url": "https://example.com",
            "description": "Resource description",
            "resource_type": "tutorial|course|documentation|article",
            "relevance_score": 0.85
        }
    ]
}

Make sure to populate recommended_resources with actual results from your search tool usage."""


class AgenticCoachAgent(BaseAgent):
    """
    Agentic coach agent that uses LangGraph for intelligent decision-making
    about performance analysis and resource discovery.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        search_service: SearchService,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        resume_content: Optional[str] = None,
        job_description: Optional[str] = None,
    ):
        super().__init__(llm_service=llm_service, event_bus=event_bus, logger=logger)
        
        self.search_service = search_service
        self.resume_content = resume_content or ""
        self.job_description = job_description or ""
        
        # Create the search tool
        self.search_tool = LearningResourceSearchTool(
            search_service=search_service,
            logger=self.logger.getChild("SearchTool")
        )
        
        # Create the agentic executor using LangGraph
        self._setup_agentic_executor()
    
    def _setup_agentic_executor(self) -> None:
        """Set up the LangGraph reactive agent with tools and memory."""
        try:
            # Create the reactive agent with search tool - use simpler approach without memory for now
            self.agent_executor = create_react_agent(
                model=self.llm,
                tools=[self.search_tool]
            )
            
            self.logger.info("Agentic coach executor created successfully with search tool")
            
        except Exception as e:
            self.logger.error(f"Failed to create agentic executor: {e}")
            # Fallback: set to None and handle gracefully
            self.agent_executor = None
    
    def evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Evaluates a single question-answer pair using the agentic approach.
        
        Returns:
            A string containing conversational coaching feedback.
        """
        if not self.agent_executor:
            # Fallback to simple evaluation if agent setup failed
            return self._simple_evaluate_answer(question, answer, justification, conversation_history)
        
        try:
            # Create the evaluation prompt for the agent
            evaluation_prompt = self._build_evaluation_prompt(
                question, answer, justification, conversation_history
            )
            
            # Get thread configuration for this conversation
            config = {"configurable": {"thread_id": f"eval_{hash(question + answer)}"}}
            
            # Run the agent
            messages = [HumanMessage(content=evaluation_prompt)]
            result = self.agent_executor.invoke({"messages": messages}, config)
            
            # Extract the final response
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
            
            return "Could not generate coaching feedback for this answer."
            
        except Exception as e:
            self.logger.error(f"Error in agentic evaluation: {e}")
            return self._simple_evaluate_answer(question, answer, justification, conversation_history)
    
    def generate_final_summary_with_resources(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a final coaching summary with intelligent resource discovery.
        
        Returns:
            A dictionary containing the final summary with recommended resources.
        """
        if not self.agent_executor:
            # Fallback to simple summary if agent setup failed
            return self._simple_final_summary(conversation_history)
        
        try:
            # Create the summary prompt for the agent
            summary_prompt = self._build_summary_prompt(conversation_history)
            
            # Get thread configuration
            config = {"configurable": {"thread_id": f"summary_{hash(str(conversation_history))}"}}
            
            # Run the agent
            messages = [HumanMessage(content=summary_prompt)]
            result = self.agent_executor.invoke({"messages": messages}, config)
            
            # Extract and parse the final response
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return self._parse_structured_summary(last_message.content)
            
            return self._create_default_summary()
            
        except Exception as e:
            self.logger.error(f"Error in agentic final summary: {e}")
            return self._simple_final_summary(conversation_history)
    
    def _build_evaluation_prompt(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Build the evaluation prompt for the agentic coach."""
        history_str = format_conversation_history(conversation_history, max_messages=10, max_content_length=200)
        
        prompt = f"""
You are an expert Interview Coach providing quick, focused coaching feedback on a candidate's answer.

**Context Information:**
Resume Content: {safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED)}
Job Description: {safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED)}
Previous Conversation History: {history_str}

**Current Question & Answer to Evaluate:**
Question: {question or "No question provided."}
Candidate's Answer: {answer or "No answer provided."}
Interviewer's Assessment: {justification or "No assessment provided."}

**Important Context Notes:**
- The "Interviewer's Assessment" reflects how the interviewer evaluated this specific answer
- Focus ONLY on the current question-answer pair and previous context
- Do NOT anticipate or reference future questions or topics
- Provide coaching based solely on what has happened so far in the interview

**Your Task:**
Provide brief, conversational coaching feedback for this specific answer. Focus on what they did well and one key area for improvement. 

Keep your response concise and encouraging (2-3 sentences max). Do NOT search for resources in per-turn feedback - save that for the final summary.

Provide your feedback as natural, encouraging coaching advice, not as a structured format.
"""
        return prompt
    
    def _build_summary_prompt(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Build the summary prompt for the agentic coach."""
        history_str = format_conversation_history(conversation_history)
        
        prompt = f"""
{AGENTIC_COACH_SYSTEM_PROMPT}

**Context Information:**
Resume Content: {safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED)}
Job Description: {safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED)}
Full Conversation History: {history_str}

**Your Task:**
Provide a comprehensive final coaching summary after analyzing the entire interview session. You MUST use the learning_resource_search tool 
to find specific learning resources for the user's identified weaknesses and improvement areas.

**MANDATORY REQUIREMENTS:**
- You MUST provide at least 3-4 different learning resources
- You MUST make multiple searches for different skill areas (e.g., technical skills, communication, problem-solving)
- Each search should target specific weaknesses you identify
- If your first search only finds 1-2 resources, make additional searches with different terms

**Search Strategy:**
1. Identify 3-4 main areas for improvement from the interview
2. For each area, use the learning_resource_search tool with appropriate skill terms
3. Search for both specific technical skills and general interview/soft skills
4. Ensure you get a variety of resource types

**Your analysis should include:**
1. **Patterns & Tendencies**: Consistent behaviors across answers
2. **Strengths**: What they did well with specific examples
3. **Weaknesses**: Areas for development with explanations
4. **Improvement Focus**: Top 2-3 areas to work on
5. **Learning Resources**: Results from your multiple search tool usages

**Example Search Areas to Consider:**
- Technical skills (algorithms, system design, coding practices)
- Communication skills (technical explanation, clarity)
- Problem-solving approach
- Domain-specific knowledge
- Interview skills and confidence

**CRITICAL**: You must actually USE the search tool multiple times to find at least 3-4 resources. Do not proceed without doing multiple searches.
"""
        return prompt
    
    def _parse_structured_summary(self, content: str) -> Dict[str, Any]:
        """
        Parse the agentic summary response using structured JSON extraction.
        
        Args:
            content: The full response from the agent
            
        Returns:
            Parsed summary dictionary
        """
        try:
            # Try to extract JSON from the response
            if "```json" in content:
                # Extract JSON from markdown code block
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            elif "{" in content and "}" in content:
                # Try to find JSON object in the content
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                # No JSON found, create default structure
                self.logger.warning("No JSON structure found in agent response")
                return self._create_default_summary()
            
            parsed = json.loads(json_str)
            
            # Ensure all required keys exist
            required_keys = ["patterns_tendencies", "strengths", "weaknesses", "improvement_focus_areas"]
            for key in required_keys:
                if key not in parsed:
                    parsed[key] = f"Could not generate {key.replace('_', ' ')} feedback."
            
            # Validate and extract resources
            resources = parsed.get("recommended_resources", [])
            if not resources or not isinstance(resources, list):
                # Extract resources from search tool usage in the response
                self.logger.info("No structured resources found, extracting from search results")
                resources = self._extract_resources_from_search_results(content)
                parsed["recommended_resources"] = resources
            
            # Ensure we have at least some resources
            if len(resources) < 2:
                self.logger.warning("Insufficient resources found, adding fallbacks")
                fallback_resources = self._get_minimal_fallback_resources()
                resources.extend(fallback_resources[:3 - len(resources)])
                parsed["recommended_resources"] = resources[:4]
            
            return parsed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            return self._create_default_summary()
        except Exception as e:
            self.logger.error(f"Error parsing structured summary: {e}")
            return self._create_default_summary()
    
    def _extract_resources_from_search_results(self, agent_response: str) -> List[Dict[str, Any]]:
        """
        Extract resources from search tool results in agent response.
        
        Args:
            agent_response: The full response from the agent
            
        Returns:
            List of extracted resource dictionaries
        """
        resources = []
        
        try:
            lines = agent_response.split('\n')
            in_search_results = False
            current_resource = {}
            
            for line in lines:
                line = line.strip()
                
                # Detect start of search results
                if "Found " in line and "free learning resources" in line:
                    in_search_results = True
                    continue
                
                # Stop processing at end markers
                if in_search_results and ("All resources have been filtered" in line or line.startswith("```")):
                    if self._is_valid_resource(current_resource):
                        resources.append(current_resource)
                    break
                
                if in_search_results:
                    # Parse numbered resource entries
                    if line and line[0].isdigit() and "." in line:
                        # Save previous resource if valid
                        if self._is_valid_resource(current_resource):
                            resources.append(current_resource)
                        
                        # Start new resource
                        title = line.split(".", 1)[1].strip()
                        if title.startswith("**") and title.endswith("**"):
                            title = title[2:-2]  # Remove markdown bold
                        current_resource = {"title": title}
                    
                    elif line.startswith("Type:"):
                        current_resource["resource_type"] = line.replace("Type:", "").strip()
                    elif line.startswith("URL:"):
                        current_resource["url"] = line.replace("URL:", "").strip()
                    elif line.startswith("Description:"):
                        current_resource["description"] = line.replace("Description:", "").strip()
                    elif line.startswith("Relevance Score:"):
                        score_str = line.replace("Relevance Score:", "").strip()
                        try:
                            current_resource["relevance_score"] = float(score_str)
                        except ValueError:
                            current_resource["relevance_score"] = 0.0
            
            # Add the last resource if valid
            if self._is_valid_resource(current_resource):
                resources.append(current_resource)
            
            self.logger.info(f"Extracted {len(resources)} resources from search results")
            return resources
            
        except Exception as e:
            self.logger.error(f"Error extracting resources from search results: {e}")
            return []
    
    def _is_valid_resource(self, resource: Dict[str, Any]) -> bool:
        """Check if a resource has all required fields."""
        required_fields = ["title", "url", "description"]
        return all(field in resource and resource[field] for field in required_fields)
    
    def _simple_evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Simple evaluation fallback when agentic approach fails."""
        try:
            # Basic template-based evaluation
            if not answer or len(answer.strip()) < 10:
                return "Consider providing more detailed answers to help the interviewer understand your thought process."
            
            if any(phrase in answer.lower() for phrase in ["i don't know", "not sure", "can't remember"]):
                return "When you're uncertain, try to think through the problem out loud or discuss related concepts you do know."
            
            return "Good answer! Consider adding more specific examples or details to strengthen your response."
            
        except Exception as e:
            self.logger.error(f"Error in simple evaluation: {e}")
            return "Could not generate coaching feedback for this answer."
    
    def _simple_final_summary(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple summary fallback when agentic approach fails."""
        try:
            # Analyze conversation for basic patterns
            conversation_text = " ".join([msg.get("content", "") for msg in conversation_history])
            
            # Generate basic resources based on conversation content
            resources = self._generate_contextual_resources(conversation_text)
            
            return {
                "patterns_tendencies": "Unable to generate detailed pattern analysis. Consider reviewing your answers for consistency and depth.",
                "strengths": "You engaged well with the interview process and provided responses to all questions.",
                "weaknesses": "Consider providing more specific examples and technical details in your answers.",
                "improvement_focus_areas": "Focus on: 1) Adding specific examples to answers, 2) Providing technical details, 3) Practicing common interview questions.",
                "recommended_resources": resources
            }
            
        except Exception as e:
            self.logger.error(f"Error in simple summary: {e}")
            return self._create_default_summary()
    
    def _generate_contextual_resources(self, conversation_text: str) -> List[Dict[str, Any]]:
        """Generate resources based on conversation content."""
        resources = []
        
        # Identify skill areas from conversation
        skill_keywords = {
            "algorithm": "algorithms and data structures",
            "python": "Python programming",
            "javascript": "JavaScript development", 
            "system": "system design",
            "database": "database design",
            "api": "API development"
        }
        
        identified_skills = []
        for keyword, skill in skill_keywords.items():
            if keyword in conversation_text.lower():
                identified_skills.append(skill)
        
        # Use search service to find resources
        for skill in identified_skills[:2]:  # Limit to 2 skills
            try:
                search_results = run_async_safe(
                    self.search_service.search_resources(
                        skill=skill,
                        proficiency_level="intermediate",
                        num_results=2,
                        use_cache=True
                    )
                )
                
                for resource in search_results[:2]:  # Top 2 per skill
                    resources.append({
                        "title": resource.title,
                        "url": resource.url,
                        "description": resource.description,
                        "resource_type": resource.resource_type,
                        "relevance_score": resource.relevance_score
                    })
                    
            except Exception as e:
                self.logger.error(f"Error searching for {skill}: {e}")
        
        # Add fallbacks if needed
        if len(resources) < 3:
            fallback_resources = self._get_minimal_fallback_resources()
            resources.extend(fallback_resources[:3 - len(resources)])
        
        return resources[:4]  # Maximum 4 resources
    
    def _get_minimal_fallback_resources(self) -> List[Dict[str, Any]]:
        """Get minimal fallback resources as last resort."""
        return [
            {
                "title": "freeCodeCamp - Learn to Code for Free",
                "url": "https://www.freecodecamp.org/learn",
                "description": "Comprehensive free coding curriculum with hands-on projects.",
                "resource_type": "course",
                "relevance_score": 0.8
            },
            {
                "title": "Technical Interview Preparation",
                "url": "https://www.geeksforgeeks.org/interview-preparation/",
                "description": "Practice coding problems and learn interview strategies.",
                "resource_type": "tutorial",
                "relevance_score": 0.7
            },
            {
                "title": "Khan Academy Computer Science",
                "url": "https://www.khanacademy.org/computing",
                "description": "Free educational content for computer science fundamentals.",
                "resource_type": "course",
                "relevance_score": 0.7
            }
        ]
    
    def _create_default_summary(self) -> Dict[str, Any]:
        """Create a default summary structure."""
        return {
            "patterns_tendencies": "Could not generate detailed patterns analysis.",
            "strengths": "Could not generate detailed strengths feedback.",
            "weaknesses": "Could not generate detailed weaknesses feedback.",
            "improvement_focus_areas": "Could not generate detailed improvement focus areas.",
            "recommended_resources": self._get_minimal_fallback_resources()
        }
    
    def process(self, context: AgentContext) -> Any:
        """
        Main processing function for the AgenticCoachAgent.
        Primary logic is in specific methods called by Orchestrator.
        """
        return {"status": "AgenticCoachAgent processed context, primary logic is in specific methods."} 