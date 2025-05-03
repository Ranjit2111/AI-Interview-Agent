import pytest
import uuid
import json
from backend.agents.orchestrator import SessionManager
from backend.models.interview import InterviewSession, InterviewStyle, SessionMode
from backend.config import get_logger # Assuming logger setup is needed


# Basic fixture for a valid session config (can be expanded)
@pytest.fixture
def valid_session_config():
    """Provides a reusable valid InterviewSession configuration.
    
    Returns:
        InterviewSession: A test session config with default values.
    """
    # Use default UUID generation or specify one for testing
    test_session_id = str(uuid.uuid4()) 
    return InterviewSession(
        id=test_session_id, # Correct field name is 'id'
        user_id="test-user-pytest",
        job_role="Software Engineer",
        job_description="Develop awesome software.",
        resume_content="Experienced developer.",
        interview_style=InterviewStyle.FORMAL,
        company_name="PyTest Inc.",
        difficulty="medium",
        target_question_count=3,
        mode=SessionMode.INTERVIEW
        # Add other required fields if any based on model definition
    )

# Test based on the first block from the original __main__
def test_session_manager_basic_flow(valid_session_config):
    """Tests a basic conversation flow through the session manager.
    
    Tests initialization, message processing, conversation history tracking,
    ending the interview and retrieving final results and stats.
    
    Args:
        valid_session_config: Fixture providing test session configuration
    """
    manager = SessionManager(
        session_id=valid_session_config.id, 
        user_id=valid_session_config.user_id, 
        session_config=valid_session_config
    )
    
    assert manager.session_id == valid_session_config.id
    assert manager.user_id == valid_session_config.user_id
    
    print("--- Starting Test Interview Flow ---") # Use print for demo clarity in tests
    
    # Initial message (often empty to trigger intro)
    response1 = manager.process_message("")
    print(f"[Assistant ({response1.get('agent')})]: {response1.get('content')}")
    assert isinstance(response1, dict)
    assert response1.get("role") == "assistant"
    assert response1.get("agent") == "interviewer"
    assert len(response1.get("content", "")) > 0
    # Could add more specific checks on content if needed
    
    # Second message (user response)
    user_msg2 = "I have experience with Python and building APIs."
    response2 = manager.process_message(user_msg2)
    print(f"[User]: {user_msg2}")
    print(f"[Assistant ({response2.get('agent')})]: {response2.get('content')}")
    assert isinstance(response2, dict)
    assert response2.get("role") == "assistant"
    
    # Check conversation history
    history = manager.get_conversation_history()
    assert len(history) == 4 # user_empty, assistant_intro, user_msg2, assistant_response2
    assert history[0]["role"] == "user" and history[0]["content"] == ""
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user" and history[2]["content"] == user_msg2
    assert history[3]["role"] == "assistant"

    # Third message (user response) - assuming 3 questions configured
    user_msg3 = "A challenge was optimizing a slow database query."
    response3 = manager.process_message(user_msg3)
    print(f"[User]: {user_msg3}")
    print(f"[Assistant ({response3.get('agent')})]: {response3.get('content')}")
    assert isinstance(response3, dict)
    assert response3.get("role") == "assistant"
    
    print("\n--- Ending Test Interview ---")
    final_results = manager.end_interview()
    print("\nFinal Session Results:")
    print(json.dumps(final_results, indent=2))
    
    assert isinstance(final_results, dict)
    assert final_results.get("status") == "Interview Ended"
    assert final_results.get("session_id") == valid_session_config.id
    # Check for expected keys, even if values might be None or error dicts
    assert "coaching_summary" in final_results 
    assert "skill_profile" in final_results
    
    print("\n--- Test Session Stats ---")
    stats = manager.get_session_stats()
    print(json.dumps(stats, indent=2))
    
    assert isinstance(stats, dict)
    assert stats.get("session_id") == valid_session_config.id
    assert stats.get("total_messages") == 6 # 3 user + 3 assistant
    assert stats.get("user_messages") == 3
    assert stats.get("assistant_messages") == 3
    assert stats.get("total_api_calls") >= 3 # Should have at least 3 interviewer calls

# Test based on the second block (different config, reset)
def test_session_manager_reset_flow():
    """Tests session manager reset functionality.
    
    Tests creating a session with different config parameters,
    processing messages, getting stats, ending the session,
    and verifying reset behavior clears all state.
    """
    test_session_id = "test-session-reset-123"
    config = InterviewSession(
        id=test_session_id, 
        user_id="test-user-reset",
        job_role="Data Analyst",
        interview_style=InterviewStyle.BEHAVIORAL, # Different style
        mode=SessionMode.INTERVIEW,
        difficulty='easy', # Different difficulty
        target_question_count=2 # Shorter interview
    )
    manager = SessionManager(session_id=config.id, user_id=config.user_id, session_config=config)
    
    # Process a couple of messages
    resp1 = manager.process_message("Hello!")
    assert resp1.get("role") == "assistant"
    print(f"[Assistant]: {resp1.get('content')}")
    
    resp2 = manager.process_message("My main strength is attention to detail.")
    assert resp2.get("role") == "assistant"
    print(f"[User]: My main strength is attention to detail.")
    print(f"[Assistant]: {resp2.get('content')}")
    
    # Get stats mid-way
    stats_before_end = manager.get_session_stats()
    assert stats_before_end.get("total_messages") == 4 
    
    # End interview
    final = manager.end_interview()
    assert final.get("status") == "Interview Ended"
    print("\nFinal Results (Reset Flow):")
    print(json.dumps(final, indent=2))
    
    # Reset session
    manager.reset_session()
    print("\n--- Session Reset ---")
    
    # Verify reset state
    history_after_reset = manager.get_conversation_history()
    assert len(history_after_reset) == 0
                    
    stats_after_reset = manager.get_session_stats()
    assert stats_after_reset.get("total_messages") == 0
    assert stats_after_reset.get("user_messages") == 0
    assert stats_after_reset.get("assistant_messages") == 0
    assert stats_after_reset.get("total_api_calls") == 0
    assert len(manager._agents) == 0 # Check agents are cleared
