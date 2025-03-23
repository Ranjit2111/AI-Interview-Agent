"""
Unit tests for the CoachAgent class.
Tests the core functionality of the coach agent.
"""

import pytest
import logging
import json
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

from backend.agents.coach import CoachAgent, CoachingMode, CoachingFocus
from backend.utils.event_bus import EventBus, Event, EventType
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
    context.set("job_role", "Software Engineer")
    context.set("experience_level", "mid-level")
    context.set("coaching_mode", CoachingMode.REAL_TIME)
    context.set("conversation_history", [
        {"role": "system", "content": "You are the interview coach for a Software Engineer position."},
        {"role": "assistant", "content": "Tell me about your experience with Python.", "agent": "interviewer"},
        {"role": "user", "content": "I have 5 years of experience with Python, working on web applications and data analysis projects."}
    ])
    context.set("last_question", "Tell me about your experience with Python.")
    context.set("last_answer", "I have 5 years of experience with Python, working on web applications and data analysis projects.")
    return context


@pytest.fixture
def coach_agent(mock_api_key, event_bus):
    """Create a coach agent for testing."""
    with patch('langchain_google_genai.ChatGoogleGenerativeAI'):
        agent = CoachAgent(
            api_key=mock_api_key,
            event_bus=event_bus,
            logger=logging.getLogger(__name__),
            coaching_mode=CoachingMode.REAL_TIME,
            coaching_focus=[CoachingFocus.CONTENT, CoachingFocus.COMMUNICATION],
            feedback_verbosity="detailed"
        )
        
        # Mock the LLM chain outputs to avoid API calls
        agent.analysis_chain = MagicMock()
        agent.analysis_chain.invoke.return_value = json.dumps({
            "strengths": ["Clear description of experience", "Mentioned specific domains"],
            "weaknesses": ["Lack of specific project examples", "No mention of technologies used with Python"],
            "clarity": 4,
            "relevance": 4,
            "specificity": 3,
            "completeness": 3,
            "overall_impression": "Good answer that could be improved with specific examples."
        })
        
        agent.tips_chain = MagicMock()
        agent.tips_chain.invoke.return_value = json.dumps({
            "tips": [
                "Provide specific project examples",
                "Mention key Python libraries and frameworks you've used",
                "Quantify achievements with metrics when possible"
            ],
            "example_improvement": "I have 5 years of experience with Python, working on web applications using Django and Flask, and data analysis projects with pandas and NumPy. For example, I developed a dashboard that reduced reporting time by 40% by automating data processing with Python."
        })
        
        agent.summary_chain = MagicMock()
        agent.summary_chain.invoke.return_value = json.dumps({
            "overall_performance": "Good technical communication with room for improvement in specificity.",
            "key_strengths": ["Technical knowledge", "Clear communication"],
            "primary_improvement_areas": ["More specific examples", "Quantify achievements"],
            "personalized_advice": "Focus on adding specific project examples and metrics to your answers."
        })
        
        agent.template_chain = MagicMock()
        agent.template_chain.invoke.return_value = json.dumps({
            "template": "When answering about my experience with [technology], I will mention: 1) Years of experience, 2) Specific projects, 3) Key libraries/frameworks used, 4) Challenges overcome, and 5) Measurable achievements.",
            "example_answer": "I have 5 years of experience with Python, primarily in web development and data analysis. I've built production RESTful APIs using Django and Flask, and implemented data pipelines with pandas and NumPy that process over 1TB of data daily. One challenge I overcame was optimizing a slow reporting system by implementing async processing, which reduced generation time by 60%."
        })
        
        agent.star_evaluation_chain = MagicMock()
        agent.star_evaluation_chain.invoke.return_value = json.dumps({
            "situation": {"present": False, "score": 0, "feedback": "You didn't describe a specific situation"},
            "task": {"present": True, "score": 3, "feedback": "You mentioned what you were doing but could be more specific"},
            "action": {"present": True, "score": 3, "feedback": "You mentioned working on projects but didn't detail specific actions"},
            "result": {"present": False, "score": 0, "feedback": "No mention of results or impact"},
            "overall_score": 1.5,
            "improvement_suggestion": "Structure your answer using the STAR method. Begin with a specific Situation, clearly state the Task, detail your Actions, and highlight the Results."
        })
        
        agent.communication_assessment_chain = MagicMock()
        agent.communication_assessment_chain.invoke.return_value = json.dumps({
            "clarity": {"score": 4, "feedback": "Your answer was clear and easy to understand"},
            "conciseness": {"score": 4, "feedback": "You were appropriately brief while covering your experience"},
            "structure": {"score": 3, "feedback": "Your answer had a logical flow but could use more structure"},
            "technical_accuracy": {"score": 4, "feedback": "Your technical terminology was accurate"},
            "overall_score": 3.75,
            "improvement_suggestion": "Consider using a more structured format for technical answers."
        })
        
        agent.completeness_evaluation_chain = MagicMock()
        agent.completeness_evaluation_chain.invoke.return_value = json.dumps({
            "key_points_covered": ["Years of experience", "Types of projects"],
            "missing_points": ["Specific frameworks/libraries", "Challenges and solutions", "Project outcomes"],
            "completeness_score": 2,
            "improvement_suggestion": "Include specific Python frameworks, libraries, and technologies you've used."
        })
        
        agent.personalized_feedback_chain = MagicMock()
        agent.personalized_feedback_chain.invoke.return_value = json.dumps({
            "personalized_feedback": "As a mid-level Software Engineer, your technical experience comes across clearly. To strengthen your answer for Python experience, I recommend adding specific examples of projects, mentioning key libraries like Django or Flask, and quantifying your achievements. This will help differentiate you from other candidates with similar years of experience.",
            "customized_example": "I have 5 years of experience with Python, focusing on web development with Django and data analysis with pandas. For example, I built a customer dashboard that processes 500K records daily, improving reporting efficiency by 40% by optimizing database queries and implementing async processing.",
            "recommended_approach": "For technical experience questions, use the framework: years of experience → specific technologies → project examples → challenges overcome → measurable results."
        })
        
        return agent


def test_initialization(coach_agent):
    """Test that the coach agent initializes correctly."""
    assert coach_agent is not None
    assert coach_agent.coaching_mode == CoachingMode.REAL_TIME
    assert CoachingFocus.CONTENT in coach_agent.coaching_focus
    assert CoachingFocus.COMMUNICATION in coach_agent.coaching_focus
    assert coach_agent.feedback_verbosity == "detailed"


def test_analyze_response_tool(coach_agent):
    """Test analyzing a user's response."""
    question = "Tell me about your experience with Python."
    response = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    
    analysis = coach_agent._analyze_response_tool(question, response)
    analysis_json = json.loads(analysis)
    
    assert "strengths" in analysis_json
    assert "weaknesses" in analysis_json
    assert "clarity" in analysis_json
    assert "overall_impression" in analysis_json


def test_generate_improvement_tips_tool(coach_agent):
    """Test generating improvement tips."""
    focus_area = "content"
    context = "Question: Tell me about your experience with Python. Answer: I have 5 years of experience with Python, working on web applications and data analysis projects."
    
    tips = coach_agent._generate_improvement_tips_tool(focus_area, context)
    tips_json = json.loads(tips)
    
    assert "tips" in tips_json
    assert "example_improvement" in tips_json
    assert len(tips_json["tips"]) > 0


def test_create_coaching_summary_tool(coach_agent):
    """Test creating a coaching summary."""
    interview_context = "Job role: Software Engineer. Experience level: Mid-level."
    qa_pairs = [
        {"question": "Tell me about your experience with Python.", 
         "answer": "I have 5 years of experience with Python, working on web applications and data analysis projects."}
    ]
    
    summary = coach_agent._create_coaching_summary_tool(interview_context, qa_pairs)
    summary_json = json.loads(summary)
    
    assert "overall_performance" in summary_json
    assert "key_strengths" in summary_json
    assert "primary_improvement_areas" in summary_json
    assert "personalized_advice" in summary_json


def test_generate_response_template_tool(coach_agent):
    """Test generating a response template."""
    question_type = "experience"
    example_question = "Tell me about your experience with Python."
    job_role = "Software Engineer"
    
    template = coach_agent._generate_response_template_tool(question_type, example_question, job_role)
    template_json = json.loads(template)
    
    assert "template" in template_json
    assert "example_answer" in template_json


def test_evaluate_star_method(coach_agent):
    """Test evaluating a response using the STAR method."""
    question = "Tell me about a time you solved a difficult problem."
    answer = "I have solved many difficult problems in my career."
    
    evaluation = coach_agent._evaluate_star_method(question, answer)
    
    assert "situation" in evaluation
    assert "task" in evaluation
    assert "action" in evaluation
    assert "result" in evaluation
    assert "overall_score" in evaluation
    assert "improvement_suggestion" in evaluation


def test_evaluate_communication_skills(coach_agent):
    """Test evaluating communication skills."""
    question = "Tell me about your experience with Python."
    answer = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    
    assessment = coach_agent._evaluate_communication_skills(question, answer)
    
    assert "clarity" in assessment
    assert "conciseness" in assessment
    assert "structure" in assessment
    assert "technical_accuracy" in assessment
    assert "overall_score" in assessment
    assert "improvement_suggestion" in assessment


def test_evaluate_response_completeness(coach_agent):
    """Test evaluating response completeness."""
    question = "Tell me about your experience with Python."
    answer = "I have 5 years of experience with Python, working on web applications and data analysis projects."
    job_role = "Software Engineer"
    
    evaluation = coach_agent._evaluate_response_completeness(question, answer, job_role)
    
    assert "key_points_covered" in evaluation
    assert "missing_points" in evaluation
    assert "completeness_score" in evaluation
    assert "improvement_suggestion" in evaluation


def test_process_input_feedback_request(coach_agent, agent_context):
    """Test processing a feedback request."""
    message = "Can you give me feedback on my last answer?"
    
    response = coach_agent.process_input(message, agent_context)
    
    assert isinstance(response, dict) or isinstance(response, str)
    if isinstance(response, dict):
        assert "feedback" in str(response).lower()
    else:
        assert "feedback" in response.lower()


def test_process_input_template_request(coach_agent, agent_context):
    """Test processing a template request."""
    message = "How should I structure my answer to questions about technical experience?"
    
    response = coach_agent.process_input(message, agent_context)
    
    assert isinstance(response, dict) or isinstance(response, str)
    if isinstance(response, dict):
        assert "template" in str(response).lower() or "structure" in str(response).lower()
    else:
        assert "template" in response.lower() or "structure" in response.lower()


def test_handle_interviewer_message(coach_agent, event_bus):
    """Test handling an interviewer message event."""
    # Create a mock event
    event = Event(
        type=EventType.AGENT_RESPONSE,
        data={
            "session_id": "test_session_id",
            "response": "Tell me about your experience with Python.",
            "agent": "interviewer"
        }
    )
    
    # Register a test event handler to capture coach insights
    insights_captured = []
    def test_handler(event):
        if event.type == EventType.COACH_INSIGHT:
            insights_captured.append(event.data)
    
    event_bus.subscribe(EventType.COACH_INSIGHT, test_handler)
    
    # Trigger the handler
    coach_agent._handle_interviewer_message(event)
    
    # Verify insights were published
    assert len(insights_captured) > 0


def test_handle_user_message(coach_agent, event_bus):
    """Test handling a user message event."""
    # Create a mock event
    event = Event(
        type=EventType.USER_RESPONSE,
        data={
            "session_id": "test_session_id",
            "message": "I have 5 years of experience with Python, working on web applications and data analysis projects.",
            "question": "Tell me about your experience with Python."
        }
    )
    
    # Register a test event handler to capture coach feedback
    feedback_captured = []
    def test_handler(event):
        if event.type == EventType.COACH_FEEDBACK:
            feedback_captured.append(event.data)
    
    event_bus.subscribe(EventType.COACH_FEEDBACK, test_handler)
    
    # Trigger the handler
    coach_agent._handle_user_message(event)
    
    # Verify feedback was published
    assert len(feedback_captured) > 0


def test_handle_interview_summary(coach_agent, event_bus):
    """Test handling an interview summary event."""
    # Create a mock event
    event = Event(
        type=EventType.INTERVIEW_SUMMARY,
        data={
            "session_id": "test_session_id",
            "summary": {
                "overall_assessment": "Good technical knowledge with some areas for improvement.",
                "strengths": ["Python knowledge", "Communication"],
                "areas_for_improvement": ["More specific examples", "STAR method usage"]
            }
        }
    )
    
    # Register a test event handler to capture coach summary
    summary_captured = []
    def test_handler(event):
        if event.type == EventType.COACH_SUMMARY:
            summary_captured.append(event.data)
    
    event_bus.subscribe(EventType.COACH_SUMMARY, test_handler)
    
    # Trigger the handler
    coach_agent._handle_interview_summary(event)
    
    # Verify summary was published
    assert len(summary_captured) > 0


def test_calculate_average_star_score(coach_agent):
    """Test calculating the average STAR score."""
    star_evaluation = {
        "situation": {"score": 4},
        "task": {"score": 3},
        "action": {"score": 4},
        "result": {"score": 2}
    }
    
    avg_score = coach_agent._calculate_average_star_score(star_evaluation)
    assert avg_score == 3.25 