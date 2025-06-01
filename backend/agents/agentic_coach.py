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
from backend.agents.templates.coach_templates import (
    EVALUATE_ANSWER_TEMPLATE,
    FINAL_SUMMARY_TEMPLATE
)
from backend.utils.llm_utils import (
    invoke_chain_with_error_handling,
    parse_json_with_fallback,
    format_conversation_history
)
from backend.utils.common import safe_get_or_default
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

Remember: You are not just analyzing - you are actively helping the user improve by finding the right resources. **Always provide multiple learning resources to add real value to the user's learning journey.**"""


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
            return self._fallback_evaluate_answer(question, answer, justification, conversation_history)
        
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
            return self._fallback_evaluate_answer(question, answer, justification, conversation_history)
    
    def generate_final_summary_with_resources(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a final coaching summary with intelligent resource discovery.
        
        Returns:
            A dictionary containing the final summary with recommended resources.
        """
        if not self.agent_executor:
            # Fallback to simple summary if agent setup failed
            return self._fallback_final_summary(conversation_history)
        
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
                    return self._parse_agentic_summary(last_message.content)
            
            return self._create_default_summary()
            
        except Exception as e:
            self.logger.error(f"Error in agentic final summary: {e}")
            return self._fallback_final_summary(conversation_history)
    
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

Format your final response as a JSON object with these keys:
- patterns_tendencies
- strengths  
- weaknesses
- improvement_focus_areas
- recommended_resources (this should be populated by your search tool usage)

**CRITICAL**: You must actually USE the search tool multiple times to find at least 3-4 resources. Do not proceed without doing multiple searches.
"""
        return prompt
    
    def _parse_agentic_summary(self, content: str) -> Dict[str, Any]:
        """Parse the agentic summary response into the expected format."""
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
                return self._create_default_summary()
            
            parsed = json.loads(json_str)
            
            # Ensure all required keys exist
            required_keys = ["patterns_tendencies", "strengths", "weaknesses", "improvement_focus_areas"]
            for key in required_keys:
                if key not in parsed:
                    parsed[key] = f"Could not generate {key.replace('_', ' ')} feedback."
            
            # Extract and format resources from the agent's tool usage
            parsed["recommended_resources"] = self._extract_resources_from_agent_response(content)
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing agentic summary: {e}")
            return self._create_default_summary()
    
    def _extract_resources_from_agent_response(self, agent_response: str) -> List[Dict[str, Any]]:
        """
        Extract resources from the agent's response when it used the search tool.
        
        Args:
            agent_response: The full response from the agent
            
        Returns:
            List of formatted resources for frontend consumption
        """
        resources = []
        
        try:
            # Look for search tool results in the agent response
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
                    if current_resource and all(key in current_resource for key in ["title", "url", "description"]):
                        resources.append(current_resource)
                    break
                
                if in_search_results:
                    # Parse numbered resource entries
                    if line and line[0].isdigit() and "." in line:
                        # Save previous resource if it has required fields
                        if current_resource and all(key in current_resource for key in ["title", "url", "description"]):
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
                    
                    elif line.startswith("Domain Quality:"):
                        current_resource["domain_quality"] = line.replace("Domain Quality:", "").strip()
            
            # Add the last resource if exists and not already added
            if current_resource and all(key in current_resource for key in ["title", "url", "description"]):
                # Check if this resource is already in the list (avoid duplicates)
                resource_exists = any(
                    r["title"] == current_resource["title"] and r["url"] == current_resource["url"] 
                    for r in resources
                )
                if not resource_exists:
                    resources.append(current_resource)
            
            # Ensure required fields exist and validate
            valid_resources = []
            for resource in resources:
                if all(key in resource for key in ["title", "url", "description"]):
                    # Ensure required fields exist
                    if "resource_type" not in resource:
                        resource["resource_type"] = "article"
                    valid_resources.append(resource)
            
            self.logger.info(f"Extracted {len(valid_resources)} resources from agent response")
            return valid_resources
            
        except Exception as e:
            self.logger.error(f"Error extracting resources from agent response: {e}")
            return []
    
    def _create_default_summary(self) -> Dict[str, Any]:
        """Create a default summary structure."""
        return {
            "patterns_tendencies": "Could not generate patterns/tendencies feedback.",
            "strengths": "Could not generate strengths feedback.",
            "weaknesses": "Could not generate weaknesses feedback.",
            "improvement_focus_areas": "Could not generate improvement focus areas.",
            "recommended_resources": self._get_hardcoded_fallback_resources()
        }
    
    def _fallback_evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Fallback evaluation method if agentic approach fails."""
        # Use the original template-based approach
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        
        try:
            chain = LLMChain(
                llm=self.llm,
                prompt=PromptTemplate.from_template(EVALUATE_ANSWER_TEMPLATE),
                output_key="evaluation_text"
            )
            
            inputs = {
                "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
                "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
                "conversation_history": format_conversation_history(conversation_history, max_messages=10, max_content_length=200),
                "question": question or "No question provided.",
                "answer": answer or "No answer provided.",
                "justification": justification or "No justification provided."
            }
            
            response = invoke_chain_with_error_handling(
                chain, inputs, self.logger, "FallbackEvaluateAnswerChain", output_key="evaluation_text"
            )
            
            if isinstance(response, str) and response.strip():
                return response
            elif isinstance(response, dict) and 'evaluation_text' in response:
                return response['evaluation_text']
            
        except Exception as e:
            self.logger.error(f"Error in fallback evaluation: {e}")
        
        return "Could not generate coaching feedback for this answer."
    
    def _fallback_final_summary(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback summary method if agentic approach fails."""
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        
        try:
            chain = LLMChain(
                llm=self.llm,
                prompt=PromptTemplate.from_template(FINAL_SUMMARY_TEMPLATE),
                output_key="summary_json"
            )
            
            inputs = {
                "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
                "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
                "conversation_history": format_conversation_history(conversation_history)
            }
            
            response = invoke_chain_with_error_handling(
                chain, inputs, self.logger, "FallbackFinalSummaryChain", output_key="summary_json"
            )
            
            if isinstance(response, dict):
                summary = response
            elif isinstance(response, str):
                summary = parse_json_with_fallback(response, self._create_default_summary(), self.logger)
            else:
                summary = self._create_default_summary()
            
            # Generate actual resources using the search service if we have search topics
            if "resource_search_topics" in summary and summary["resource_search_topics"]:
                self.logger.info("Fallback: Generating resources from search topics")
                summary["recommended_resources"] = self._generate_resources_from_topics(summary["resource_search_topics"])
            elif "recommended_resources" not in summary or not summary["recommended_resources"]:
                # Generate default resources based on conversation analysis
                self.logger.info("Fallback: Generating default resources")
                summary["recommended_resources"] = self._generate_default_resources_from_conversation(conversation_history)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in fallback summary: {e}")
            return self._create_default_summary_with_resources()
    
    def _generate_resources_from_topics(self, topics: List[str]) -> List[Dict[str, Any]]:
        """Generate resources from search topics using the search service."""
        resources = []
        
        self.logger.info(f"Generating resources from {len(topics)} topics: {topics}")
        
        try:
            for i, topic in enumerate(topics[:3]):  # Limit to first 3 topics
                self.logger.info(f"Searching for resources for topic {i+1}: {topic}")
                
                # Use asyncio to run the async search
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    topic_resources = loop.run_until_complete(
                        self.search_service.search_resources(
                            skill=topic,
                            proficiency_level="intermediate",
                            num_results=3,
                            use_cache=False  # Don't use cache for fresh results
                        )
                    )
                    
                    # Convert Resource objects to dictionaries
                    for resource in topic_resources[:2]:  # Take top 2 from each topic
                        resource_dict = {
                            "title": resource.title,
                            "url": resource.url,
                            "description": resource.description,
                            "resource_type": resource.resource_type,
                            "relevance_score": resource.relevance_score
                        }
                        resources.append(resource_dict)
                        self.logger.info(f"Added resource: {resource.title[:50]}...")
                    
                finally:
                    loop.close()
        
        except Exception as e:
            self.logger.error(f"Error generating resources from topics: {e}")
            # Fall back to hardcoded resources
            resources = self._get_hardcoded_fallback_resources()
        
        self.logger.info(f"Generated {len(resources)} total resources from topics")
        return resources[:4]  # Ensure we don't exceed 4 resources
    
    def _generate_default_resources_from_conversation(self, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate default resources based on conversation analysis."""
        self.logger.info("Generating default resources based on conversation patterns")
        
        # Analyze conversation for skill gaps
        conversation_text = " ".join([msg.get("content", "") for msg in conversation_history])
        
        default_skills = []
        
        # Check for algorithm/data structure mentions
        if any(term in conversation_text.lower() for term in ["sort", "algorithm", "complexity", "data structure"]):
            default_skills.append("algorithms")
        
        # Check for system design mentions
        if any(term in conversation_text.lower() for term in ["system", "design", "architecture", "scale"]):
            default_skills.append("system design")
        
        # Check for communication issues
        if any(term in conversation_text.lower() for term in ["not sure", "don't know", "can't remember"]):
            default_skills.append("technical communication")
        
        # Default to programming fundamentals if no specific patterns found
        if not default_skills:
            default_skills = ["programming fundamentals", "interview preparation"]
        
        # Generate resources for identified skills
        resources = []
        for skill in default_skills[:3]:  # Max 3 skills
            try:
                search_results = self.search_tool._run(
                    skill=skill,
                    proficiency_level="intermediate",
                    num_results=2
                )
                skill_resources = self._extract_resources_from_search_text(search_results)
                resources.extend(skill_resources[:2])  # Take top 2 from each skill
            except Exception as e:
                self.logger.error(f"Error searching for {skill}: {e}")
        
        # Ensure we have at least 3 resources by adding fallbacks if needed
        if len(resources) < 3:
            fallback_resources = self._get_hardcoded_fallback_resources()
            resources.extend(fallback_resources[:3 - len(resources)])
        
        return resources[:4]  # Maximum 4 resources
    
    def _extract_resources_from_search_text(self, search_text: str) -> List[Dict[str, Any]]:
        """Extract resources from search tool output text."""
        resources = []
        
        if "No suitable free learning resources found" in search_text:
            return resources
        
        lines = search_text.split('\n')
        current_resource = {}
        
        for line in lines:
            line = line.strip()
            
            if line and line[0].isdigit() and "." in line:
                # Save previous resource
                if current_resource and all(key in current_resource for key in ["title", "url", "description"]):
                    resources.append(current_resource)
                
                # Start new resource
                title = line.split(".", 1)[1].strip()
                if title.startswith("**") and title.endswith("**"):
                    title = title[2:-2]
                current_resource = {"title": title}
            
            elif line.startswith("Type:"):
                current_resource["resource_type"] = line.replace("Type:", "").strip()
            elif line.startswith("URL:"):
                current_resource["url"] = line.replace("URL:", "").strip()
            elif line.startswith("Description:"):
                current_resource["description"] = line.replace("Description:", "").strip()
        
        # Add last resource
        if current_resource and all(key in current_resource for key in ["title", "url", "description"]):
            if "resource_type" not in current_resource:
                current_resource["resource_type"] = "article"
            resources.append(current_resource)
        
        return resources
    
    def _get_hardcoded_fallback_resources(self) -> List[Dict[str, Any]]:
        """Get hardcoded fallback resources as a last resort."""
        return [
            {
                "title": "Free Programming Courses on freeCodeCamp",
                "url": "https://www.freecodecamp.org/learn",
                "description": "Comprehensive free coding curriculum with hands-on projects and certifications.",
                "resource_type": "course"
            },
            {
                "title": "Algorithm Fundamentals on Khan Academy",
                "url": "https://www.khanacademy.org/computing/computer-science/algorithms",
                "description": "Learn algorithmic thinking and fundamental computer science concepts.",
                "resource_type": "course"
            },
            {
                "title": "Technical Interview Preparation",
                "url": "https://www.geeksforgeeks.org/interview-preparation/",
                "description": "Practice coding problems and learn interview strategies for technical roles.",
                "resource_type": "tutorial"
            }
        ]
    
    def _create_default_summary_with_resources(self) -> Dict[str, Any]:
        """Create a default summary structure with fallback resources."""
        return {
            "patterns_tendencies": "Could not generate patterns/tendencies feedback.",
            "strengths": "Could not generate strengths feedback.",
            "weaknesses": "Could not generate weaknesses feedback.",
            "improvement_focus_areas": "Could not generate improvement focus areas.",
            "recommended_resources": self._get_hardcoded_fallback_resources()
        }
    
    def process(self, context: AgentContext) -> Any:
        """
        Main processing function for the AgenticCoachAgent.
        Primary logic is in specific methods called by Orchestrator.
        """
        return {"status": "AgenticCoachAgent processed context, primary logic is in specific methods."} 