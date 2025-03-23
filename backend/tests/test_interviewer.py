"""
Unit tests for the InterviewerAgent class.
Tests the core functionality of the interviewer agent.
"""

import pytest
import logging
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

from backend.models.interview import InterviewStyle
from backend.agents.interviewer import InterviewerAgent, InterviewState
from backend.utils.event_bus import EventBus
from backend.agents.base import AgentContext


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "test_api_key"


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return EventBus()


@pytest.fixture
def agent_context():
    """Create a test agent context."""
    context = AgentContext(session_id="test_session_id", user_id="test_user_id")
    context.set("interview_state", InterviewState.QUESTIONING)
    context.set("job_role", "Software Engineer")
    context.set("job_description", "Developing web applications and services")
    context.set("current_question", "Tell me about your experience with Python.")
    context.set("conversation_history", [
        {"role": "system", "content": "You are the interviewer for a Software Engineer position."},
        {"role": "assistant", "content": "Tell me about your experience with Python.", "agent": "interviewer"}
    ])
    return context


@pytest.fixture
def interviewer_agent(mock_api_key, event_bus):
    """Create an interviewer agent for testing."""
    with patch('langchain_google_genai.ChatGoogleGenerativeAI'):
        agent = InterviewerAgent(
            api_key=mock_api_key,
            event_bus=event_bus,
            logger=logging.getLogger(__name__),
            interview_style=InterviewStyle.TECHNICAL,
            job_role="Software Engineer",
            job_description="Developing web applications and services",
            difficulty_level="medium",
            question_count=5
        )
        
        # Mock the LLM chain outputs to avoid API calls
        agent.question_chain = MagicMock()
        agent.question_chain.invoke.return_value = "What challenges have you faced with Python and how did you overcome them?"
        
        agent.evaluation_chain = MagicMock()
        agent.evaluation_chain.invoke.return_value = json.dumps({
            "score": 4,
            "strengths": ["Clear explanation", "Good examples"],
            "areas_for_improvement": ["Could provide more specific examples"],
            "feedback": "Good answer with clear examples."
        })
        
        agent.think_chain = MagicMock()
        agent.think_chain.invoke.return_value = json.dumps({
            "understood_question": True,
            "answer_quality": "good",
            "key_points": ["Experience with Python", "Multiple projects"],
            "missing_information": ["Specific challenges faced"]
        })
        
        agent.reason_chain = MagicMock()
        agent.reason_chain.invoke.return_value = json.dumps({
            "next_action": "ask_follow_up",
            "rationale": "The candidate provided good information but didn't mention challenges",
            "follow_up_topic": "challenges with Python"
        })
        
        agent.planning_chain = MagicMock()
        agent.planning_chain.invoke.return_value = json.dumps({
            "current_phase": "technical_assessment",
            "topics_covered": ["Python experience"],
            "topics_to_cover": ["Problem solving", "System design"],
            "next_question_area": "challenges and problem solving"
        })
        
        agent.summary_chain = MagicMock()
        agent.summary_chain.invoke.return_value = json.dumps({
            "overall_assessment": "The candidate shows good technical knowledge",
            "technical_strengths": ["Python experience", "Web development"],
            "areas_for_improvement": ["Could provide more specific examples of problem solving"],
            "recommended_follow_up": "Dive deeper into system design experience"
        })
        
        agent.quality_assessment_chain = MagicMock()
        agent.quality_assessment_chain.invoke.return_value = json.dumps({
            "clarity": 4,
            "relevance": 4,
            "depth": 3,
            "conciseness": 4,
            "overall_quality": "good"
        })
        
        agent.follow_up_chain = MagicMock()
        agent.follow_up_chain.invoke.return_value = "Can you describe a specific challenge you encountered with Python and how you resolved it?"
        
        # Initialize the agent with some predefined questions
        agent.questions = [
            "Tell me about your experience with Python.",
            "What challenges have you faced with Python and how did you overcome them?",
            "Describe a complex problem you solved using Python.",
            "How do you approach system design?",
            "Tell me about your experience with team collaboration."
        ]
        agent.current_question_index = 0
        
        return agent


def test_initialization(interviewer_agent):
    """Test that the interviewer agent initializes correctly."""
    assert interviewer_agent is not None
    assert interviewer_agent.job_role == "Software Engineer"
    assert interviewer_agent.interview_style == InterviewStyle.TECHNICAL
    assert len(interviewer_agent.questions) == 5
    assert interviewer_agent.current_question_index == 0


def test_get_next_question(interviewer_agent):
    """Test getting the next question from the agent."""
    # Get the first question
    first_question = interviewer_agent._get_next_question()
    assert first_question == "Tell me about your experience with Python."
    assert interviewer_agent.current_question_index == 1
    
    # Get the second question
    second_question = interviewer_agent._get_next_question()
    assert second_question == "What challenges have you faced with Python and how did you overcome them?"
    assert interviewer_agent.current_question_index == 2


def test_process_answer(interviewer_agent, agent_context):
    """Test processing a user's answer."""
    answer = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    result = interviewer_agent._process_answer(answer, agent_context)
    
    assert "score" in result
    assert "strengths" in result
    assert "areas_for_improvement" in result
    assert "feedback" in result


def test_handle_questioning(interviewer_agent, agent_context):
    """Test handling a user's response during the questioning phase."""
    response = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    result = interviewer_agent._handle_questioning(response, agent_context)
    
    assert isinstance(result, str)
    assert "What challenges" in result  # Should contain the follow-up or next question


def test_handle_evaluation(interviewer_agent, agent_context):
    """Test handling the evaluation phase."""
    response = "I'd like to get feedback on my interview performance."
    result = interviewer_agent._handle_evaluation(response, agent_context)
    
    assert isinstance(result, str)
    assert "feedback" in result.lower()


def test_generate_follow_up_question(interviewer_agent):
    """Test generating a follow-up question."""
    original_question = "Tell me about your experience with Python."
    answer = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    
    follow_up = interviewer_agent._generate_follow_up_question(original_question, answer)
    assert isinstance(follow_up, str)
    assert "challenge" in follow_up.lower()


def test_assess_answer_quality(interviewer_agent):
    """Test assessing the quality of an answer."""
    question = "Tell me about your experience with Python."
    answer = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    
    assessment = interviewer_agent._assess_answer_quality(question, answer)
    assert "clarity" in assessment
    assert "relevance" in assessment
    assert "depth" in assessment
    assert "conciseness" in assessment
    assert "overall_quality" in assessment


def test_create_summary(interviewer_agent, agent_context):
    """Test creating an interview summary."""
    # Add some Q&A pairs to the context
    agent_context.set("qa_pairs", [
        {
            "question": "Tell me about your experience with Python.",
            "answer": "I have 5 years of experience with Python, working on web applications and data analysis projects."
        },
        {
            "question": "What challenges have you faced with Python and how did you overcome them?",
            "answer": "I encountered memory management issues with large datasets. I resolved this by implementing chunking and using generators."
        }
    ])
    
    summary = interviewer_agent._create_summary(agent_context)
    assert "overall_assessment" in summary
    assert "technical_strengths" in summary
    assert "areas_for_improvement" in summary
    assert "recommended_follow_up" in summary


def test_format_response_by_style(interviewer_agent):
    """Test formatting responses according to interview style."""
    content = "Tell me about your experience with Python."
    
    # Test technical style formatting
    interviewer_agent.interview_style = InterviewStyle.TECHNICAL
    technical_response = interviewer_agent._format_response_by_style(content, "question")
    assert technical_response.startswith("From a technical perspective")
    
    # Test formal style formatting
    interviewer_agent.interview_style = InterviewStyle.FORMAL
    formal_response = interviewer_agent._format_response_by_style(content, "question")
    assert "formal" in formal_response.lower()
    
    # Test casual style formatting
    interviewer_agent.interview_style = InterviewStyle.CASUAL
    casual_response = interviewer_agent._format_response_by_style(content, "question")
    assert "casual" in casual_response.lower()


def test_handle_interview_start(interviewer_agent, event_bus):
    """Test handling an interview start event."""
    # Create a mock event
    from backend.utils.event_bus import Event, EventType
    event = Event(
        type=EventType.INTERVIEW_START,
        data={
            "session_id": "test_session_id",
            "job_role": "Software Engineer",
            "job_description": "Developing web applications and services",
            "interview_style": "TECHNICAL"
        }
    )
    
    # Register a test event handler to capture the response
    response_captured = []
    def test_handler(event):
        if event.type == EventType.AGENT_RESPONSE:
            response_captured.append(event.data.get("response", ""))
    
    event_bus.subscribe(EventType.AGENT_RESPONSE, test_handler)
    
    # Trigger the handler
    interviewer_agent._handle_interview_start(event)
    
    # Verify a response was published
    assert len(response_captured) > 0
    assert "interview" in response_captured[0].lower() 