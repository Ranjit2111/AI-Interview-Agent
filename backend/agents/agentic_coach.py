"""
Coach Agent using fallback template-based approach with intelligent resource recommendations.
This agent provides coaching feedback and intelligently searches for learning resources.
"""

import logging
import json
from typing import Dict, Any, List, Optional

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

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


class AgenticCoachAgent(BaseAgent):
    """
    Coach agent that provides intelligent coaching feedback and resource discovery.
    Uses template-based approach with integrated search functionality.
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
        
        # Create the search tool for resource discovery
        self.search_tool = LearningResourceSearchTool(
            search_service=search_service,
            logger=self.logger.getChild("SearchTool")
        )
        
        self.logger.info("AgenticCoachAgent initialized with search functionality")
    
    def evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        justification: Optional[str], 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Evaluates a single question-answer pair using template-based approach.
        
        Returns:
            A string containing conversational coaching feedback.
        """
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
                chain, inputs, self.logger, "EvaluateAnswerChain", output_key="evaluation_text"
            )
            
            if isinstance(response, str) and response.strip():
                return response
            elif isinstance(response, dict) and 'evaluation_text' in response:
                return response['evaluation_text']
            
        except Exception as e:
            self.logger.error(f"Error in evaluation: {e}")
        
        return "Could not generate coaching feedback for this answer."
    
    def generate_final_summary_with_resources(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a final coaching summary with intelligent resource discovery.
        Enhanced with detailed error logging for debugging.
        
        Returns:
            A dictionary containing the final summary with recommended resources.
        """
        try:
            self.logger.info("🚀 Starting final summary generation with resources")
            
            # Step 1: Validate input
            if not conversation_history:
                self.logger.error("❌ No conversation history provided for final summary")
                return self._create_default_summary()
            
            self.logger.info(f"📝 Processing conversation with {len(conversation_history)} messages")
            
            # Step 2: Prepare LLM chain
            try:
                chain = LLMChain(
                    llm=self.llm,
                    prompt=PromptTemplate.from_template(FINAL_SUMMARY_TEMPLATE),
                    output_key="summary_json"
                )
                self.logger.info("✅ LLM chain created successfully")
            except Exception as e:
                self.logger.exception(f"❌ Failed to create LLM chain: {e}")
                return self._create_default_summary()
            
            # Step 3: Prepare inputs
            try:
                inputs = {
                    "resume_content": safe_get_or_default(self.resume_content, DEFAULT_VALUE_NOT_PROVIDED),
                    "job_description": safe_get_or_default(self.job_description, DEFAULT_VALUE_NOT_PROVIDED),
                    "conversation_history": format_conversation_history(conversation_history)
                }
                
                self.logger.info(f"📊 Input prepared - Resume: {len(inputs['resume_content'])} chars, "
                               f"Job desc: {len(inputs['job_description'])} chars, "
                               f"History: {len(inputs['conversation_history'])} chars")
                
            except Exception as e:
                self.logger.exception(f"❌ Failed to prepare LLM inputs: {e}")
                return self._create_default_summary()
            
            # Step 4: Invoke LLM chain
            try:
                self.logger.info("🤖 Invoking LLM chain for final summary...")
                response = invoke_chain_with_error_handling(
                    chain, inputs, self.logger, "FinalSummaryChain", output_key="summary_json"
                )
                
                if response is None:
                    self.logger.error("❌ LLM chain returned None response")
                    return self._create_default_summary()
                
                self.logger.info(f"✅ LLM chain response received: {type(response)}")
                
            except Exception as e:
                self.logger.exception(f"❌ LLM chain invocation failed: {e}")
                return self._create_default_summary()
            
            # Step 5: Process LLM response
            try:
                if isinstance(response, dict):
                    summary = response
                    self.logger.info("✅ Response is already a dictionary")
                elif isinstance(response, str):
                    self.logger.info("📄 Response is string, parsing JSON...")
                    summary = parse_json_with_fallback(response, self._create_default_summary(), self.logger)
                    if summary == self._create_default_summary():
                        self.logger.error("❌ JSON parsing failed, using default summary")
                else:
                    self.logger.warning(f"⚠️ Unexpected response type: {type(response)}, using default")
                    summary = self._create_default_summary()
                    
            except Exception as e:
                self.logger.exception(f"❌ Failed to process LLM response: {e}")
                summary = self._create_default_summary()
            
            # Step 6: Generate resources using search tool
            if "resource_search_topics" in summary and summary["resource_search_topics"]:
                try:
                    self.logger.info(f"🔍 Generating resources for {len(summary['resource_search_topics'])} topics: {summary['resource_search_topics']}")
                    
                    generated_resources = self._generate_resources_with_reasoning(
                        summary["resource_search_topics"], 
                        summary
                    )
                    
                    if generated_resources:
                        summary["recommended_resources"] = generated_resources
                        self.logger.info(f"✅ Generated {len(generated_resources)} resources successfully")
                    else:
                        self.logger.warning("⚠️ Resource generation returned empty results")
                    
                except Exception as e:
                    self.logger.exception(f"❌ Error generating resources (will use fallback): {e}")
            else:
                self.logger.info("ℹ️ No resource search topics found in summary")
            
            # Step 7: Ensure fallback resources
            if "recommended_resources" not in summary or not summary["recommended_resources"]:
                self.logger.info("📚 Adding fallback resources")
                summary["recommended_resources"] = self._get_hardcoded_fallback_resources()
            
            # Step 8: Final validation
            try:
                resource_count = len(summary.get("recommended_resources", []))
                summary_keys = list(summary.keys()) if isinstance(summary, dict) else []
                
                self.logger.info(f"✅ Final summary completed: {len(summary_keys)} sections, {resource_count} resources")
                self.logger.info(f"📋 Summary sections: {summary_keys}")
                
                return summary
                
            except Exception as e:
                self.logger.exception(f"❌ Final validation failed: {e}")
                return self._create_default_summary()
            
        except Exception as e:
            self.logger.exception(f"❌ Unexpected error in final summary generation: {e}")
            return self._create_default_summary()
    
    def _generate_resources_with_reasoning(self, search_topics: List[str], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate resources with reasoning for each recommendation.
        Enhanced with detailed error logging.
        
        Args:
            search_topics: List of topics to search for
            summary: The coaching summary containing context for reasoning
            
        Returns:
            List of resources with reasoning
        """
        generated_resources = []
        
        if not search_topics:
            self.logger.warning("⚠️ No search topics provided for resource generation")
            return generated_resources
        
        try:
            # Extract key improvement areas for reasoning context
            weaknesses = summary.get("weaknesses", "")
            improvement_areas = summary.get("improvement_focus_areas", "")
            
            self.logger.info(f"🎯 Extracting context - Weaknesses: {len(weaknesses)} chars, Improvements: {len(improvement_areas)} chars")
            
            # Determine number of resources dynamically based on topics (3-6 resources)
            max_resources_per_topic = max(1, min(2, 6 // len(search_topics)))
            max_total_resources = min(6, len(search_topics) * 2)
            
            self.logger.info(f"📊 Resource limits: {max_resources_per_topic} per topic, {max_total_resources} total")
            
            for i, topic in enumerate(search_topics[:3]):  # Limit to 3 topics max
                try:
                    self.logger.info(f"🔍 Processing topic {i+1}/{min(3, len(search_topics))}: '{topic}'")
                    
                    # Determine proficiency level based on performance
                    proficiency_level = self._determine_proficiency_level(weaknesses, topic)
                    self.logger.info(f"📈 Determined proficiency level for '{topic}': {proficiency_level}")
                    
                    # Search for resources
                    try:
                        self.logger.info(f"🌐 Searching for resources: skill='{topic}', level='{proficiency_level}', count={max_resources_per_topic}")
                        search_results = self.search_tool._run(
                            skill=topic, 
                            proficiency_level=proficiency_level, 
                            num_results=max_resources_per_topic
                        )
                        
                        if search_results:
                            self.logger.info(f"✅ Search completed for '{topic}': {len(search_results)} chars of results")
                        else:
                            self.logger.warning(f"⚠️ Empty search results for topic '{topic}'")
                            continue
                            
                    except Exception as search_error:
                        self.logger.exception(f"❌ Search failed for topic '{topic}': {search_error}")
                        continue
                    
                    # Extract resources and add reasoning
                    try:
                        topic_resources = self._extract_resources_from_search_text(search_results)
                        self.logger.info(f"📚 Extracted {len(topic_resources)} resources for topic '{topic}'")
                        
                        for j, resource in enumerate(topic_resources):
                            if len(generated_resources) >= max_total_resources:
                                self.logger.info(f"🛑 Reached maximum resource limit ({max_total_resources})")
                                break
                                
                            try:
                                # Add reasoning based on the topic and user's performance
                                resource["reasoning"] = self._generate_resource_reasoning(
                                    resource, topic, weaknesses, improvement_areas
                                )
                                
                                generated_resources.append(resource)
                                self.logger.debug(f"✅ Added resource {j+1} for topic '{topic}': {resource.get('title', 'Unknown')}")
                                
                            except Exception as reasoning_error:
                                self.logger.error(f"❌ Failed to add reasoning for resource {j+1} in topic '{topic}': {reasoning_error}")
                                continue
                        
                    except Exception as extraction_error:
                        self.logger.exception(f"❌ Resource extraction failed for topic '{topic}': {extraction_error}")
                        continue
                    
                    if len(generated_resources) >= max_total_resources:
                        break
                        
                except Exception as topic_error:
                    self.logger.exception(f"❌ Error processing topic '{topic}': {topic_error}")
                    continue
            
            self.logger.info(f"🎉 Resource generation completed: {len(generated_resources)} total resources")
            return generated_resources
            
        except Exception as e:
            self.logger.exception(f"❌ Unexpected error in resource generation: {e}")
            return []
    
    def _determine_proficiency_level(self, weaknesses: str, topic: str) -> str:
        """
        Determine appropriate proficiency level based on identified weaknesses.
        
        Args:
            weaknesses: The weaknesses section from the summary
            topic: The topic being searched for
            
        Returns:
            Proficiency level string
        """
        if not weaknesses:
            return "intermediate"
        
        weaknesses_lower = weaknesses.lower()
        topic_lower = topic.lower()
        
        # Check for fundamental gaps
        if any(word in weaknesses_lower for word in ["basic", "fundamental", "foundation", "beginner"]):
            return "beginner"
        
        # Check for advanced needs
        if any(word in weaknesses_lower for word in ["advanced", "complex", "deep", "sophisticated"]):
            return "advanced"
        
        # Topic-specific adjustments
        if topic_lower in weaknesses_lower:
            # If the topic is specifically mentioned in weaknesses, start with beginner
            return "beginner"
        
        return "intermediate"
    
    def _generate_resource_reasoning(self, resource: Dict[str, Any], topic: str, 
                                   weaknesses: str, improvement_areas: str) -> str:
        """
        Generate reasoning for why a specific resource was recommended.
        
        Args:
            resource: The resource dictionary
            topic: The topic this resource addresses
            weaknesses: User's weaknesses
            improvement_areas: Areas for improvement
            
        Returns:
            Reasoning string explaining why this resource was recommended
        """
        resource_type = resource.get("resource_type", "resource")
        
        # Create reasoning based on the resource type and topic
        reasoning_templates = {
            "course": f"This {resource_type} will help you build foundational knowledge in {topic}",
            "tutorial": f"This {resource_type} provides step-by-step guidance to improve your {topic} skills",
            "documentation": f"This official documentation will deepen your understanding of {topic}",
            "article": f"This {resource_type} covers key concepts that will strengthen your {topic} knowledge",
            "video": f"This {resource_type} offers visual learning to enhance your {topic} abilities",
            "interactive": f"This hands-on {resource_type} will let you practice {topic} skills directly",
            "community": f"This community resource provides ongoing support for learning {topic}"
        }
        
        base_reasoning = reasoning_templates.get(
            resource_type.lower(), 
            f"This resource will help you improve your {topic} skills"
        )
        
        # Add specific context based on weaknesses if available
        if weaknesses and topic.lower() in weaknesses.lower():
            base_reasoning += f", addressing the gaps identified in your interview performance"
        
        return base_reasoning
    
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
    
    def _create_default_summary(self) -> Dict[str, Any]:
        """Create a default summary structure."""
        return {
            "patterns_tendencies": "Could not generate patterns/tendencies feedback.",
            "strengths": "Could not generate strengths feedback.",
            "weaknesses": "Could not generate weaknesses feedback.",
            "improvement_focus_areas": "Could not generate improvement focus areas.",
            "recommended_resources": self._get_hardcoded_fallback_resources()
        }
    
    def _get_hardcoded_fallback_resources(self) -> List[Dict[str, Any]]:
        """Get hardcoded fallback resources as a last resort."""
        return [
            {
                "title": "Free Programming Courses on freeCodeCamp",
                "url": "https://www.freecodecamp.org/learn",
                "description": "Comprehensive free coding curriculum with hands-on projects and certifications.",
                "resource_type": "course",
                "reasoning": "This comprehensive platform will help you build strong programming fundamentals across multiple technologies"
            },
            {
                "title": "Algorithm Fundamentals on Khan Academy",
                "url": "https://www.khanacademy.org/computing/computer-science/algorithms",
                "description": "Learn algorithmic thinking and fundamental computer science concepts.",
                "resource_type": "course",
                "reasoning": "This course will strengthen your problem-solving skills and algorithmic thinking abilities"
            },
            {
                "title": "Technical Interview Preparation",
                "url": "https://www.geeksforgeeks.org/interview-preparation/",
                "description": "Practice coding problems and learn interview strategies for technical roles.",
                "resource_type": "tutorial",
                "reasoning": "This resource provides targeted practice for technical interviews to improve your performance"
            }
        ]
    
    def process(self, context: AgentContext) -> Any:
        """
        Main processing function for the AgenticCoachAgent.
        Primary logic is in specific methods called by Orchestrator.
        """
        return {"status": "AgenticCoachAgent processed context, primary logic is in specific methods."} 