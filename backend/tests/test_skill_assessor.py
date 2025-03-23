"""
Test module for the SkillAssessorAgent.
Tests skill extraction, proficiency assessment, and resource recommendation.
"""
import os
import json
import pytest
from unittest.mock import MagicMock, patch

from backend.agents.skill_assessor import SkillAssessorAgent, ProficiencyLevel, SkillCategory
from backend.agents.base import AgentContext
from backend.utils.event_bus import EventBus


@pytest.fixture
def mock_api_key():
    """Mock API key for tests."""
    return "test_api_key"


@pytest.fixture
def event_bus():
    """Event bus fixture."""
    return EventBus()


@pytest.fixture
def agent_context():
    """Agent context fixture."""
    context = AgentContext(session_id="test_session_id", user_id="test_user_id")
    return context


@pytest.fixture
def skill_assessor(mock_api_key, event_bus):
    """SkillAssessorAgent fixture."""
    # Use mock LLM to avoid API calls
    with patch("backend.agents.skill_assessor.ChatGoogleGenerativeAI") as MockLLM:
        # Configure the mock LLM
        mock_llm = MagicMock()
        MockLLM.return_value = mock_llm
        
        # Create the skill assessor agent
        agent = SkillAssessorAgent(
            api_key=mock_api_key,
            model_name="mock-model",
            planning_interval=0,
            event_bus=event_bus,
            job_role="Software Engineer",
            technical_focus=True
        )
        
        # Replace LLM chains with mocks
        agent.skill_extraction_chain = MagicMock()
        agent.proficiency_chain = MagicMock()
        agent.resource_chain = MagicMock()
        agent.profile_chain = MagicMock()
        
        yield agent


def test_skill_extraction(skill_assessor, agent_context):
    """Test skill extraction from text."""
    # Configure mock response
    mock_skills = [
        {"skill_name": "python", "category": "language", "confidence": 0.9},
        {"skill_name": "flask", "category": "framework", "confidence": 0.8},
        {"skill_name": "problem solving", "category": "soft", "confidence": 0.7}
    ]
    skill_assessor.skill_extraction_chain.invoke.return_value = {
        "extracted_skills": mock_skills
    }
    
    # Test extraction
    response = "I have 5 years of experience with Python, and I've built several web applications using Flask."
    skills = skill_assessor._extract_skills_tool(response)
    
    # Verify the mock was called correctly
    skill_assessor.skill_extraction_chain.invoke.assert_called_once()
    
    # Verify the extracted skills
    assert len(skills) == 3
    assert skills[0]["skill_name"] == "python"
    assert skills[1]["category"] == "framework"
    assert skills[2]["confidence"] == 0.7


def test_proficiency_assessment(skill_assessor, agent_context):
    """Test proficiency assessment for a skill."""
    # Configure mock response
    skill_assessor.proficiency_chain.invoke.return_value = {"proficiency_level": "advanced"}
    
    # Test assessment
    skill = "python"
    context = "I've been using Python for 5 years, and I've built several complex applications. I'm familiar with advanced features like decorators, context managers, and metaprogramming."
    proficiency = skill_assessor._assess_proficiency_tool(skill, context)
    
    # Verify the mock was called correctly
    skill_assessor.proficiency_chain.invoke.assert_called_once()
    
    # Verify the proficiency level
    assert proficiency == {"proficiency_level": "advanced"}


def test_resource_recommendation(skill_assessor, agent_context):
    """Test resource recommendation for a skill."""
    # Configure mock response
    mock_resources = {
        "resources": [
            {
                "type": "book",
                "title": "Python Cookbook",
                "url": "https://example.com/python-cookbook",
                "description": "Recipes for mastering Python 3"
            },
            {
                "type": "online_course",
                "title": "Advanced Python Programming",
                "url": "https://example.com/advanced-python",
                "description": "Mastering advanced Python techniques"
            }
        ]
    }
    skill_assessor.resource_chain.invoke.return_value = {"resources": mock_resources}
    
    # Test resource recommendation
    skill = "python"
    proficiency_level = "intermediate"
    resources = skill_assessor._suggest_resources_tool(skill, proficiency_level)
    
    # Verify the mock was called correctly
    skill_assessor.resource_chain.invoke.assert_called_once()
    
    # Verify the resources
    assert resources == {"resources": mock_resources}


def test_identify_skills_in_text(skill_assessor):
    """Test the text-based skill identification."""
    # Initialize skill keywords for testing
    skill_assessor.skill_keywords = {
        "languages": ["python", "javascript", "java"],
        "frameworks": ["react", "angular", "django", "flask"],
        "soft_skills": ["communication", "problem solving", "teamwork"]
    }
    
    # Test skill identification
    text = "I'm proficient in Python and JavaScript, and I've built web applications using Django and React. I'm also good at problem solving and teamwork."
    skills = skill_assessor._identify_skills_in_text(text)
    
    # Verify the identified skills
    skill_names = [skill[0] for skill in skills]
    assert "python" in skill_names
    assert "javascript" in skill_names
    assert "django" in skill_names
    assert "react" in skill_names
    assert "problem solving" in skill_names
    assert "teamwork" in skill_names
    assert "angular" not in skill_names


def test_get_resources_for_skill(skill_assessor):
    """Test retrieving resources for a skill."""
    # Test resource retrieval
    skill = "python"
    resources_json = skill_assessor._get_resources_for_skill(skill)
    
    # Verify the resources format
    resources = json.loads(resources_json)
    assert "resources" in resources
    assert len(resources["resources"]) > 0
    
    # Verify resource structure
    resource = resources["resources"][0]
    assert "title" in resource
    assert "url" in resource
    assert "description" in resource
    assert "type" in resource
    
    # Verify the skill name is used in the resources
    assert any(skill.lower() in resource["title"].lower() for resource in resources["resources"])
    
    # Test caching
    assert skill in skill_assessor.resource_cache


def test_process_input(skill_assessor, agent_context):
    """Test processing user input."""
    # Test processing with a basic message
    skill_assessor._process_input_rule_based = MagicMock(return_value="Rule-based response")
    
    # Process input
    response = skill_assessor.process_input("I know Python and JavaScript", agent_context)
    
    # Verify the method was called correctly
    skill_assessor._process_input_rule_based.assert_called_once()
    
    # Verify the response
    assert response == "Rule-based response"


def test_calculate_relevance(skill_assessor):
    """Test calculating relevance score for search results."""
    # Create mock search result
    class MockSearchResult:
        def __init__(self, title, snippet, url):
            self.title = title
            self.snippet = snippet
            self.url = url
    
    # Test different scenarios
    result1 = MockSearchResult(
        "Learn Python Programming", 
        "Comprehensive guide to Python programming for beginners",
        "https://www.example.com/python-tutorial"
    )
    result2 = MockSearchResult(
        "Web Development Guide", 
        "Learn HTML, CSS, JavaScript, and Python for web development",
        "https://www.example.com/web-dev"
    )
    result3 = MockSearchResult(
        "Coding Resources", 
        "Various resources for learning to code",
        "https://www.coursera.org/python-course"
    )
    
    # Calculate relevance scores
    score1 = skill_assessor._calculate_relevance(result1, "python")
    score2 = skill_assessor._calculate_relevance(result2, "python")
    score3 = skill_assessor._calculate_relevance(result3, "python")
    
    # Verify the scores
    assert score1 > score2  # "python" in title and snippet and URL is more relevant
    assert score2 > score3  # "python" in snippet is more relevant than just in URL
    assert score3 > 0  # educational domain and python in URL has some relevance 