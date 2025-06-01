"""
Integration test for the complete agentic coach system.
This test simulates a full interview session and verifies that:
1. The agentic coach can analyze user performance
2. The search tool finds appropriate learning resources
3. The coach coordinates everything correctly
4. The frontend receives properly formatted data
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from backend.agents.agentic_coach import AgenticCoachAgent
from backend.services.llm_service import LLMService
from backend.services.search_service import SearchService, Resource
from backend.utils.event_bus import EventBus


class TestAgenticCoachIntegration:
    """Integration tests for the complete agentic coach system."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        mock_service = Mock(spec=LLMService)
        mock_llm = Mock()
        mock_service.get_llm.return_value = mock_llm
        return mock_service
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service with realistic resources."""
        mock_service = Mock(spec=SearchService)
        
        # Comprehensive set of resources for different skills
        algorithm_resources = [
            Resource(
                title="Interactive Algorithm Visualizations",
                url="https://visualgo.net/",
                description="Visual learning tool for algorithms and data structures with step-by-step animations.",
                resource_type="interactive",
                source="search",
                relevance_score=0.94,
                metadata={"domain_quality": "top"}
            ),
            Resource(
                title="Algorithm Design Manual - Free Chapters",
                url="https://www.algorithm-archive.org/",
                description="Comprehensive guide to algorithm design patterns and analysis techniques.",
                resource_type="tutorial",
                source="search", 
                relevance_score=0.92,
                metadata={"domain_quality": "top"}
            )
        ]
        
        async def mock_search(skill, proficiency_level="intermediate", **kwargs):
            """Mock search that returns appropriate resources based on skill."""
            skill_lower = skill.lower()
            if "algorithm" in skill_lower or "data structure" in skill_lower:
                return algorithm_resources[:2]  # Return top 2 results
            else:
                return []
        
        mock_service.search_resources = mock_search
        return mock_service
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus."""
        return EventBus()
    
    @pytest.fixture
    def agentic_coach(self, mock_llm_service, mock_search_service, event_bus):
        """Create an agentic coach with mocked services."""
        logger = logging.getLogger("test")
        
        with patch('backend.agents.agentic_coach.create_react_agent') as mock_create_agent:
            # Mock the agentic coach's agent executor
            mock_executor = Mock()
            mock_create_agent.return_value = mock_executor
            
            coach = AgenticCoachAgent(
                llm_service=mock_llm_service,
                search_service=mock_search_service,
                event_bus=event_bus,
                logger=logger,
                resume_content="Software Engineer with 4 years experience in full-stack web development. Proficient in Python, JavaScript, and React.",
                job_description="We're looking for a senior engineer with strong algorithmic thinking and system design skills."
            )
            
            # Set up the mock executor to return realistic coaching responses
            self._setup_realistic_coach_responses(mock_executor)
            
            return coach
    
    def _setup_realistic_coach_responses(self, mock_executor):
        """Set up realistic responses for the agentic coach."""
        
        def mock_invoke(inputs, config=None):
            """Mock the invoke method to return realistic coaching responses."""
            messages = inputs.get("messages", [])
            if not messages:
                return {"messages": [Mock(content="No input provided.")]}
            
            user_message = messages[0].content if messages else ""
            
            # Determine response type based on the prompt content
            if "comprehensive final coaching summary" in user_message:
                # This is a final summary request - simulate the agent using search tools
                response_content = '''
                Based on my analysis of the entire interview session, I've identified several areas for improvement. 
                Let me search for targeted learning resources.
                
                Found 2 free learning resources for 'algorithm fundamentals':
                
                1. **Interactive Algorithm Visualizations**
                   Type: interactive
                   URL: https://visualgo.net/
                   Description: Visual learning tool for algorithms and data structures with step-by-step animations.
                   Relevance Score: 0.94
                   Domain Quality: top
                
                2. **Algorithm Design Manual - Free Chapters**
                   Type: tutorial
                   URL: https://www.algorithm-archive.org/
                   Description: Comprehensive guide to algorithm design patterns and analysis techniques.
                   Relevance Score: 0.92
                   Domain Quality: top
                
                All resources have been filtered to exclude paid content, books, and premium services.
                
                ```json
                {
                    "patterns_tendencies": "You consistently showed uncertainty when discussing technical concepts, often using hedging language like 'I think' or 'I'm not sure'. You also struggled to recall specific technical details from your past projects.",
                    "strengths": "You demonstrated good problem-solving intuition and honesty about your knowledge gaps. Your communication style is clear and you show willingness to learn.",
                    "weaknesses": "Limited depth in algorithm analysis and time complexity understanding. Difficulty providing specific technical details about past projects.",
                    "improvement_focus_areas": "1. Deep dive into algorithm complexity analysis and optimization techniques 2. Practice technical storytelling with specific examples and metrics 3. Build confidence in technical explanations through mock interviews"
                }
                ```
                '''
            else:
                response_content = "Good effort on that answer! Focus on being more specific about your technical approach."
            
            return {"messages": [Mock(content=response_content)]}
        
        mock_executor.invoke = mock_invoke
    
    def test_agentic_coach_evaluation_and_resources(self, agentic_coach):
        """Test the agentic coach's evaluation and resource discovery capabilities."""
        
        # Simulate a realistic interview conversation
        conversation_history = [
            {
                "role": "assistant",
                "agent": "interviewer", 
                "content": "Can you explain how you would implement a sorting algorithm?",
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "role": "user",
                "content": "Um, I think I would use bubble sort because it's the simplest to implement.",
                "timestamp": "2024-01-01T10:01:00"
            },
            {
                "role": "assistant",
                "agent": "interviewer",
                "content": "Tell me about a challenging project you worked on.",
                "timestamp": "2024-01-01T10:02:00"
            },
            {
                "role": "user", 
                "content": "I worked on a web application for user management, but I don't remember much about the specific technical details.",
                "timestamp": "2024-01-01T10:03:00"
            }
        ]
        
        # Test per-turn evaluation
        evaluation = agentic_coach.evaluate_answer(
            question="Can you explain how you would implement a sorting algorithm?",
            answer="Um, I think I would use bubble sort because it's the simplest to implement.",
            justification="Testing algorithm knowledge",
            conversation_history=conversation_history
        )
        
        # Verify evaluation response
        assert isinstance(evaluation, str)
        assert len(evaluation) > 20  # Should be a substantial response
        
        # Test final summary with resource discovery
        final_summary = agentic_coach.generate_final_summary_with_resources(conversation_history)
        
        # Verify final summary structure
        required_keys = ["patterns_tendencies", "strengths", "weaknesses", "improvement_focus_areas", "recommended_resources"]
        for key in required_keys:
            assert key in final_summary, f"Missing key: {key}"
            assert final_summary[key] is not None
        
        # Verify learning resources were found and properly formatted
        resources = final_summary["recommended_resources"]
        assert isinstance(resources, list)
        assert len(resources) > 0, "No learning resources were found"
        
        # Verify resource format matches frontend expectations
        for resource in resources:
            assert "title" in resource
            assert "url" in resource  
            assert "description" in resource
            assert "resource_type" in resource
            
            # Verify URLs are not placeholder/mock URLs
            assert resource["url"] != "#"
            assert "http" in resource["url"]
        
        # Verify specific resources were found
        resource_titles = [r["title"] for r in resources]
        assert "Interactive Algorithm Visualizations" in resource_titles
        assert "Algorithm Design Manual - Free Chapters" in resource_titles
        
        print(f"\n✅ Agentic coach integration test completed successfully!")
        print(f"📊 Evaluation response length: {len(evaluation)} characters")
        print(f"🎯 Summary keys: {list(final_summary.keys())}")
        print(f"📚 Learning resources found: {len(resources)}")
        for i, resource in enumerate(resources, 1):
            print(f"   {i}. {resource['title']} ({resource['resource_type']})")


if __name__ == "__main__":
    # Run the integration test
    pytest.main([__file__ + "::TestAgenticCoachIntegration::test_agentic_coach_evaluation_and_resources", "-v", "-s"]) 