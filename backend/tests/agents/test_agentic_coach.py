"""
Comprehensive tests for the Agentic Coach Agent implementation.
Tests the agent's ability to provide coaching feedback and find learning resources.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from backend.agents.agentic_coach import AgenticCoachAgent
from backend.agents.tools.search_tool import LearningResourceSearchTool
from backend.services.llm_service import LLMService
from backend.services.search_service import SearchService, Resource
from backend.utils.event_bus import EventBus


class TestAgenticCoachAgent:
    """Test suite for the agentic coach agent."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing."""
        mock_service = Mock(spec=LLMService)
        mock_llm = Mock()
        mock_service.get_llm.return_value = mock_llm
        return mock_service
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service for testing."""
        mock_service = Mock(spec=SearchService)
        
        # Create sample resources
        sample_resources = [
            Resource(
                title="Python Basics Tutorial",
                url="https://realpython.com/python-basics/",
                description="Learn Python programming fundamentals with practical examples.",
                resource_type="tutorial",
                source="search",
                relevance_score=0.85,
                metadata={"domain_quality": "top"}
            ),
            Resource(
                title="Python Documentation",
                url="https://docs.python.org/3/tutorial/",
                description="Official Python tutorial and documentation.",
                resource_type="documentation",
                source="search",
                relevance_score=0.92,
                metadata={"domain_quality": "top"}
            )
        ]
        
        # Mock the async search method
        mock_service.search_resources = AsyncMock(return_value=sample_resources)
        return mock_service
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            {
                "role": "assistant",
                "agent": "interviewer", 
                "content": "Can you explain how you would implement a sorting algorithm?",
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "role": "user",
                "content": "Um, I think I would use bubble sort because it's simple...",
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
                "content": "I worked on a web application but I don't remember much about the technical details.",
                "timestamp": "2024-01-01T10:03:00"
            }
        ]
    
    @pytest.fixture
    def agentic_coach(self, mock_llm_service, mock_search_service, mock_event_bus):
        """Create an agentic coach agent for testing."""
        with patch('backend.agents.agentic_coach.create_react_agent') as mock_create_agent:
            # Mock the agent executor
            mock_executor = Mock()
            mock_create_agent.return_value = mock_executor
            
            coach = AgenticCoachAgent(
                llm_service=mock_llm_service,
                search_service=mock_search_service,
                event_bus=mock_event_bus,
                resume_content="Python developer with 2 years experience",
                job_description="Senior Python Developer position"
            )
            
            # Set the mock executor
            coach.agent_executor = mock_executor
            return coach
    
    def test_initialization(self, agentic_coach, mock_search_service):
        """Test that the agentic coach initializes correctly."""
        assert agentic_coach.search_service == mock_search_service
        assert agentic_coach.resume_content == "Python developer with 2 years experience"
        assert agentic_coach.job_description == "Senior Python Developer position"
        assert isinstance(agentic_coach.search_tool, LearningResourceSearchTool)
        assert agentic_coach.agent_executor is not None
    
    def test_evaluate_answer_with_agentic_response(self, agentic_coach, sample_conversation_history):
        """Test answer evaluation using the agentic approach."""
        # Mock agent response
        mock_response = {
            "messages": [
                Mock(content="Great question about sorting algorithms! I can see you mentioned bubble sort, which shows you understand the concept. However, for a senior developer role, interviewers typically expect knowledge of more efficient algorithms like quicksort or mergesort. Bubble sort has O(n²) time complexity, which isn't optimal for large datasets. I'd recommend studying time complexity analysis and practicing with more advanced sorting algorithms.")
            ]
        }
        agentic_coach.agent_executor.invoke.return_value = mock_response
        
        result = agentic_coach.evaluate_answer(
            question="Can you explain how you would implement a sorting algorithm?",
            answer="Um, I think I would use bubble sort because it's simple...",
            justification="Testing algorithm knowledge",
            conversation_history=sample_conversation_history
        )
        
        assert "bubble sort" in result.lower()
        assert "quicksort" in result.lower() or "mergesort" in result.lower()
        assert len(result) > 50  # Should be a substantial response
    
    def test_evaluate_answer_fallback(self, agentic_coach, sample_conversation_history):
        """Test fallback evaluation when agentic approach fails."""
        # Make agent executor fail
        agentic_coach.agent_executor = None
        
        with patch('langchain.chains.LLMChain') as mock_chain_class:
            mock_chain = Mock()
            mock_chain_class.return_value = mock_chain
            
            with patch('backend.agents.agentic_coach.invoke_chain_with_error_handling') as mock_invoke:
                mock_invoke.return_value = "Fallback coaching feedback provided."
                
                result = agentic_coach.evaluate_answer(
                    question="Test question",
                    answer="Test answer", 
                    justification="Test justification",
                    conversation_history=sample_conversation_history
                )
                
                assert result == "Fallback coaching feedback provided."
                mock_invoke.assert_called_once()
    
    def test_generate_final_summary_with_resources(self, agentic_coach, sample_conversation_history):
        """Test final summary generation with resource discovery."""
        # Mock agent response with search tool usage
        agent_response_content = '''
        Based on the interview analysis, here's my comprehensive feedback:

        I need to search for learning resources for the identified skill gaps.

        Found 2 free learning resources for 'Python algorithms':

        1. **Python Algorithms Tutorial**
           Type: tutorial
           URL: https://realpython.com/python-algorithms/
           Description: Comprehensive guide to implementing algorithms in Python.
           Relevance Score: 0.89

        2. **Algorithm Design Patterns**
           Type: article  
           URL: https://github.com/algorithm-patterns/python
           Description: Common algorithm patterns with Python implementations.
           Relevance Score: 0.85

        All resources have been filtered to exclude paid content.

        ```json
        {
            "patterns_tendencies": "You consistently showed uncertainty when discussing technical concepts, often using phrases like 'I think' or 'I don't remember much'. This suggests a need for deeper technical preparation.",
            "strengths": "You demonstrated honesty about your knowledge gaps and showed willingness to learn. Your communication style is clear and approachable.",
            "weaknesses": "Limited technical depth in algorithm knowledge and project details. Difficulty recalling specific technical implementations and best practices.",
            "improvement_focus_areas": "1. Study fundamental algorithms and data structures 2. Practice technical storytelling with specific examples 3. Prepare detailed project explanations with technical details"
        }
        ```
        '''
        
        mock_response = {
            "messages": [Mock(content=agent_response_content)]
        }
        agentic_coach.agent_executor.invoke.return_value = mock_response
        
        result = agentic_coach.generate_final_summary_with_resources(sample_conversation_history)
        
        # Verify summary structure
        assert "patterns_tendencies" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "improvement_focus_areas" in result
        assert "recommended_resources" in result
        
        # Verify resources were extracted
        resources = result["recommended_resources"]
        assert len(resources) == 2
        assert resources[0]["title"] == "Python Algorithms Tutorial"
        assert resources[0]["url"] == "https://realpython.com/python-algorithms/"
        assert resources[0]["resource_type"] == "tutorial"
        assert resources[1]["title"] == "Algorithm Design Patterns"
        
    def test_resource_extraction_from_agent_response(self, agentic_coach):
        """Test extraction of resources from agent response text."""
        agent_response = '''
        I'll help you find learning resources.

        Found 3 free learning resources for 'data structures':

        1. **Data Structures in Python**
           Type: course
           URL: https://www.coursera.org/learn/data-structures-python
           Description: Learn fundamental data structures using Python.
           Relevance Score: 0.92
           Domain Quality: top

        2. **Stack Overflow Data Structures Guide**
           Type: community
           URL: https://stackoverflow.com/questions/tagged/data-structures
           Description: Community discussions about data structure implementations.
           Relevance Score: 0.78

        3. **GitHub Data Structures Examples**
           Type: tutorial
           URL: https://github.com/topics/data-structures
           Description: Code examples and implementations of various data structures.
           Relevance Score: 0.85

        All resources have been filtered to exclude paid content.
        '''
        
        resources = agentic_coach._extract_resources_from_agent_response(agent_response)
        
        assert len(resources) == 3
        
        # Check first resource
        assert resources[0]["title"] == "Data Structures in Python"
        assert resources[0]["resource_type"] == "course"
        assert resources[0]["url"] == "https://www.coursera.org/learn/data-structures-python"
        assert resources[0]["description"] == "Learn fundamental data structures using Python."
        assert resources[0]["relevance_score"] == 0.92
        assert resources[0]["domain_quality"] == "top"
        
        # Check second resource
        assert resources[1]["title"] == "Stack Overflow Data Structures Guide"
        assert resources[1]["resource_type"] == "community"
        
        # Check third resource  
        assert resources[2]["title"] == "GitHub Data Structures Examples"
        assert resources[2]["resource_type"] == "tutorial"
    
    def test_resource_extraction_no_resources(self, agentic_coach):
        """Test resource extraction when no resources are found."""
        agent_response = '''
        I analyzed your interview performance but couldn't find specific learning resources 
        for the topics you need to improve on. You may want to search for more general 
        programming concepts.
        '''
        
        resources = agentic_coach._extract_resources_from_agent_response(agent_response)
        assert len(resources) == 0
    
    def test_create_default_summary(self, agentic_coach):
        """Test creation of default summary structure."""
        default_summary = agentic_coach._create_default_summary()
        
        required_keys = ["patterns_tendencies", "strengths", "weaknesses", "improvement_focus_areas", "recommended_resources"]
        for key in required_keys:
            assert key in default_summary
        
        assert isinstance(default_summary["recommended_resources"], list)
        assert len(default_summary["recommended_resources"]) == 0


class TestSearchTool:
    """Test suite for the search tool used by the agentic coach."""
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service for tool testing."""
        mock_service = Mock(spec=SearchService)
        
        # Create sample resources including some that should be filtered
        sample_resources = [
            Resource(
                title="Free Python Tutorial",
                url="https://realpython.com/python-basics/",
                description="Learn Python programming for free.",
                resource_type="tutorial", 
                source="search",
                relevance_score=0.85
            ),
            Resource(
                title="Buy Python Programming Book",
                url="https://amazon.com/python-book",
                description="Purchase this comprehensive Python book.",
                resource_type="book",
                source="search", 
                relevance_score=0.90
            ),
            Resource(
                title="Python Documentation",
                url="https://docs.python.org/",
                description="Official Python documentation.",
                resource_type="documentation",
                source="search",
                relevance_score=0.95
            )
        ]
        
        mock_service.search_resources = AsyncMock(return_value=sample_resources)
        return mock_service
    
    @pytest.fixture
    def search_tool(self, mock_search_service):
        """Create a search tool for testing."""
        return LearningResourceSearchTool(
            search_service=mock_search_service
        )
    
    def test_search_tool_filters_paid_content(self, search_tool):
        """Test that the search tool filters out paid content."""
        result = search_tool._run(
            skill="Python programming",
            proficiency_level="beginner",
            num_results=5
        )
        
        # Should contain free resources but filter out the "Buy" book
        assert "Free Python Tutorial" in result
        assert "Python Documentation" in result
        assert "Buy Python Programming Book" not in result
        assert "amazon.com" not in result
    
    def test_search_tool_format_for_llm(self, search_tool, mock_search_service):
        """Test that the search tool formats results correctly for LLM consumption."""
        # Create mock resources without paid content
        free_resources = [
            Resource(
                title="Python Basics",
                url="https://realpython.com/python-basics/",
                description="Learn Python fundamentals.",
                resource_type="tutorial",
                source="search",
                relevance_score=0.85,
                metadata={"domain_quality": "top"}
            )
        ]
        
        result_text = search_tool._format_results_for_llm(free_resources, "Python programming")
        
        assert "Found 1 free learning resources for 'Python programming'" in result_text
        assert "Python Basics" in result_text
        assert "https://realpython.com/python-basics/" in result_text
        assert "Learn Python fundamentals." in result_text
        assert "Type: tutorial" in result_text
        assert "Relevance Score: 0.85" in result_text
        assert "Domain Quality: top" in result_text
        assert "exclude paid content" in result_text


class TestIntegrationScenarios:
    """Integration tests simulating real coaching scenarios."""
    
    @pytest.fixture
    def realistic_coach_setup(self):
        """Set up a realistic coaching scenario."""
        # Mock services
        mock_llm_service = Mock(spec=LLMService)
        mock_search_service = Mock(spec=SearchService)
        mock_event_bus = Mock(spec=EventBus)
        
        # Sample resources for different skill areas
        algorithm_resources = [
            Resource(
                title="Algorithm Design Manual",
                url="https://www.algorithm-archive.org/",
                description="Free comprehensive guide to algorithm design and analysis.",
                resource_type="tutorial",
                source="search",
                relevance_score=0.92
            )
        ]
        
        communication_resources = [
            Resource(
                title="Technical Communication for Developers",
                url="https://dev.to/technical-communication-guide",
                description="Guide to improving technical communication skills.",
                resource_type="article", 
                source="search",
                relevance_score=0.87
            )
        ]
        
        # Mock search responses based on skill
        async def mock_search(skill, **kwargs):
            if "algorithm" in skill.lower():
                return algorithm_resources
            elif "communication" in skill.lower():
                return communication_resources
            else:
                return []
        
        mock_search_service.search_resources = mock_search
        
        # Create coach with mocked agent executor
        with patch('backend.agents.agentic_coach.create_react_agent') as mock_create_agent:
            mock_executor = Mock()
            mock_create_agent.return_value = mock_executor
            
            coach = AgenticCoachAgent(
                llm_service=mock_llm_service,
                search_service=mock_search_service,
                event_bus=mock_event_bus,
                resume_content="Software engineer with 3 years experience in web development",
                job_description="Senior Software Engineer - Full Stack Development"
            )
            
            coach.agent_executor = mock_executor
            return coach, mock_executor
    
    def test_coaching_scenario_weak_algorithms(self, realistic_coach_setup):
        """Test coaching scenario where user shows weakness in algorithms."""
        coach, mock_executor = realistic_coach_setup
        
        # Simulate conversation showing algorithm weakness
        conversation_history = [
            {
                "role": "assistant",
                "agent": "interviewer",
                "content": "How would you find the second largest element in an array?",
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "role": "user", 
                "content": "I'm not sure... maybe sort the array and take the second element?",
                "timestamp": "2024-01-01T10:01:00"
            },
            {
                "role": "assistant",
                "agent": "interviewer", 
                "content": "What's the time complexity of common sorting algorithms?",
                "timestamp": "2024-01-01T10:02:00"
            },
            {
                "role": "user",
                "content": "I don't really know the time complexities off the top of my head.",
                "timestamp": "2024-01-01T10:03:00" 
            }
        ]
        
        # Mock agent response focusing on algorithm improvement
        agent_response = '''
        Based on the interview, I've identified significant gaps in algorithm knowledge. Let me find resources.

        Found 1 free learning resources for 'algorithm fundamentals':

        1. **Algorithm Design Manual**
           Type: tutorial
           URL: https://www.algorithm-archive.org/
           Description: Free comprehensive guide to algorithm design and analysis.
           Relevance Score: 0.92

        ```json
        {
            "patterns_tendencies": "Shows uncertainty with algorithm problems and lacks knowledge of time complexity fundamentals.",
            "strengths": "Honest about knowledge gaps and willing to think through problems step by step.",
            "weaknesses": "Limited understanding of algorithm efficiency, time complexity, and optimization techniques.",
            "improvement_focus_areas": "1. Study fundamental algorithms and their time complexities 2. Practice algorithm implementation 3. Learn Big O notation and complexity analysis"
        }
        ```
        '''
        
        mock_executor.invoke.return_value = {
            "messages": [Mock(content=agent_response)]
        }
        
        result = coach.generate_final_summary_with_resources(conversation_history)
        
        # Verify coaching identifies algorithm weakness
        assert "algorithm" in result["weaknesses"].lower()
        assert "time complexity" in result["weaknesses"].lower()
        
        # Verify appropriate resources are recommended
        assert len(result["recommended_resources"]) == 1
        assert "Algorithm Design Manual" in result["recommended_resources"][0]["title"]
        assert result["recommended_resources"][0]["resource_type"] == "tutorial"
        
        # Verify improvement areas focus on algorithms
        assert "algorithm" in result["improvement_focus_areas"].lower()
        assert "complexity" in result["improvement_focus_areas"].lower() 