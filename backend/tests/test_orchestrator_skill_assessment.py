"""
Test module for integrating the Orchestrator with the SkillAssessorAgent.
Tests the orchestration of skill assessment flows.
"""
import os
import json
import pytest
from unittest.mock import MagicMock, patch

from backend.agents.orchestrator import Orchestrator
from backend.agents.skill_assessor import SkillAssessorAgent
from backend.utils.event_bus import EventBus, EventType
from backend.agents.base import AgentContext
from backend.models.interview import InterviewSession, SessionMode, SkillAssessment


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
def mock_db_session():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_interview_session(mock_db_session):
    """Mock interview session."""
    session = MagicMock(spec=InterviewSession)
    session.id = "test_session_id"
    session.user_id = "test_user_id"
    session.mode = SessionMode.SKILL_ASSESSMENT
    session.conversation_history = []
    
    # Mock the database session to return our mock interview session
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = session
    
    return session


@pytest.fixture
def orchestrator(mock_api_key, event_bus, mock_db_session):
    """Orchestrator fixture with mocked agents."""
    # Use mock agents to avoid API calls
    with patch("backend.agents.orchestrator.InterviewerAgent") as MockInterviewer, \
         patch("backend.agents.orchestrator.CoachAgent") as MockCoach, \
         patch("backend.agents.orchestrator.SkillAssessorAgent") as MockSkillAssessor:
        
        # Configure the mock agents
        mock_interviewer = MagicMock()
        mock_interviewer.process_input.return_value = "Interviewer response"
        MockInterviewer.return_value = mock_interviewer
        
        mock_coach = MagicMock()
        mock_coach.process_input.return_value = "Coach response"
        MockCoach.return_value = mock_coach
        
        mock_skill_assessor = MagicMock()
        mock_skill_assessor.process_input.return_value = "Skill assessor response"
        mock_skill_assessor._extract_skills_tool.return_value = [
            {"skill_name": "python", "category": "language", "confidence": 0.9},
            {"skill_name": "problem solving", "category": "soft", "confidence": 0.8}
        ]
        mock_skill_assessor._assess_proficiency_tool.return_value = {"proficiency_level": "intermediate"}
        mock_skill_assessor._suggest_resources_tool.return_value = {
            "resources": [
                {
                    "type": "course",
                    "title": "Advanced Python Programming",
                    "url": "https://example.com/python",
                    "description": "Learn advanced Python techniques"
                }
            ]
        }
        MockSkillAssessor.return_value = mock_skill_assessor
        
        # Create the orchestrator
        orchestrator = Orchestrator(
            api_key=mock_api_key,
            model_name="mock-model",
            event_bus=event_bus,
            db_session=mock_db_session
        )
        
        yield orchestrator


def test_initialize_skill_assessment_mode(orchestrator, mock_interview_session, agent_context):
    """Test initializing skill assessment mode."""
    # Mock the session to be in skill assessment mode
    mock_interview_session.mode = SessionMode.SKILL_ASSESSMENT
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Verify the skill assessor was initialized
    assert orchestrator.skill_assessor is not None
    assert orchestrator.current_agent == orchestrator.skill_assessor


def test_process_user_message_skill_assessment(orchestrator, mock_interview_session, agent_context):
    """Test processing a user message in skill assessment mode."""
    # Mock the session to be in skill assessment mode
    mock_interview_session.mode = SessionMode.SKILL_ASSESSMENT
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Process a message
    user_message = "I have extensive experience with Python and Django. I'm also good at problem solving."
    response = orchestrator.process_user_message(user_message, agent_context)
    
    # Verify the skill assessor processed the message
    orchestrator.skill_assessor.process_input.assert_called_once_with(user_message, agent_context)
    assert response == "Skill assessor response"


def test_skill_extraction_event(orchestrator, mock_interview_session, agent_context, mock_db_session, event_bus):
    """Test handling a skill extraction event."""
    # Mock the session to be in skill assessment mode
    mock_interview_session.mode = SessionMode.SKILL_ASSESSMENT
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Set up the event handler
    event_received = False
    
    def event_handler(event):
        nonlocal event_received
        event_received = True
        assert event.event_type == EventType.SKILL_EXTRACTED
        assert len(event.data["skills"]) == 2
        assert event.data["skills"][0]["skill_name"] == "python"
    
    event_bus.subscribe(EventType.SKILL_EXTRACTED, event_handler)
    
    # Emit the event
    skills = [
        {"skill_name": "python", "category": "language", "confidence": 0.9},
        {"skill_name": "problem solving", "category": "soft", "confidence": 0.8}
    ]
    orchestrator._handle_skill_extraction(skills, agent_context)
    
    # Verify the event was received and processed
    assert event_received
    
    # Verify skills were saved to the database
    mock_db_session.add.assert_called()


def test_skill_proficiency_assessment_event(orchestrator, mock_interview_session, agent_context, mock_db_session, event_bus):
    """Test handling a skill proficiency assessment event."""
    # Mock the session to be in skill assessment mode
    mock_interview_session.mode = SessionMode.SKILL_ASSESSMENT
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Set up the event handler
    event_received = False
    
    def event_handler(event):
        nonlocal event_received
        event_received = True
        assert event.event_type == EventType.SKILL_ASSESSED
        assert event.data["skill"] == "python"
        assert event.data["proficiency"] == "intermediate"
    
    event_bus.subscribe(EventType.SKILL_ASSESSED, event_handler)
    
    # Emit the event
    skill = "python"
    proficiency = "intermediate"
    feedback = "Good understanding of Python basics but could improve on advanced concepts."
    orchestrator._handle_skill_assessment(skill, proficiency, feedback, agent_context)
    
    # Verify the event was received and processed
    assert event_received
    
    # Verify assessment was saved to the database
    mock_db_session.add.assert_called()


def test_skill_resource_recommendation_event(orchestrator, mock_interview_session, agent_context, mock_db_session, event_bus):
    """Test handling a skill resource recommendation event."""
    # Mock the session to be in skill assessment mode
    mock_interview_session.mode = SessionMode.SKILL_ASSESSMENT
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Set up the event handler
    event_received = False
    
    def event_handler(event):
        nonlocal event_received
        event_received = True
        assert event.event_type == EventType.RESOURCES_SUGGESTED
        assert event.data["skill"] == "python"
        assert len(event.data["resources"]) == 1
        assert event.data["resources"][0]["title"] == "Advanced Python Programming"
    
    event_bus.subscribe(EventType.RESOURCES_SUGGESTED, event_handler)
    
    # Emit the event
    skill = "python"
    resources = [
        {
            "type": "course",
            "title": "Advanced Python Programming",
            "url": "https://example.com/python",
            "description": "Learn advanced Python techniques"
        }
    ]
    orchestrator._handle_resource_suggestion(skill, resources, agent_context)
    
    # Verify the event was received and processed
    assert event_received
    
    # Verify resources were saved to the database
    mock_db_session.add.assert_called()


def test_switch_to_skill_assessment_mode(orchestrator, mock_interview_session, agent_context, mock_db_session):
    """Test switching from interview mode to skill assessment mode."""
    # Mock the session to be in interview mode initially
    mock_interview_session.mode = SessionMode.INTERVIEW
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Switch to skill assessment mode
    orchestrator.switch_mode(SessionMode.SKILL_ASSESSMENT, agent_context)
    
    # Verify the mode was switched
    assert mock_interview_session.mode == SessionMode.SKILL_ASSESSMENT
    assert orchestrator.current_agent == orchestrator.skill_assessor
    
    # Verify the change was saved to the database
    mock_db_session.commit.assert_called()


def test_generate_skill_profile(orchestrator, mock_interview_session, agent_context, mock_db_session):
    """Test generating a skill profile for a session."""
    # Mock the session to be in skill assessment mode
    mock_interview_session.mode = SessionMode.SKILL_ASSESSMENT
    
    # Mock skill assessments in the database
    skill_assessment1 = MagicMock(spec=SkillAssessment)
    skill_assessment1.skill_name = "python"
    skill_assessment1.proficiency_level = "intermediate"
    skill_assessment1.feedback = "Good understanding of Python basics but could improve on advanced concepts."
    
    skill_assessment2 = MagicMock(spec=SkillAssessment)
    skill_assessment2.skill_name = "problem solving"
    skill_assessment2.proficiency_level = "advanced"
    skill_assessment2.feedback = "Excellent problem solving skills demonstrated throughout the interview."
    
    mock_interview_session.skill_assessments = [skill_assessment1, skill_assessment2]
    
    # Mock the profile generation from the skill assessor
    mock_profile = {
        "overall_assessment": "Strong technical foundation with excellent soft skills.",
        "strengths": ["problem solving", "communication"],
        "areas_for_improvement": ["advanced Python concepts", "system design"],
        "recommended_learning_path": "Focus on advanced Python techniques and system design principles."
    }
    orchestrator.skill_assessor.profile_chain.invoke.return_value = mock_profile
    
    # Initialize the session
    orchestrator.initialize_session(mock_interview_session)
    
    # Generate the profile
    profile = orchestrator.generate_skill_profile(agent_context)
    
    # Verify the profile was generated correctly
    assert profile == mock_profile 