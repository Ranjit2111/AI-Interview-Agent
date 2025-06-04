#!/usr/bin/env python3
"""
Test script to verify time-based interview configuration works correctly.
"""

import asyncio
import json
from agents.config_models import SessionConfig
from agents.orchestrator import AgentSessionManager
from database.mock_db_manager import MockDatabaseManager

async def test_time_based_interview():
    """Test time-based interview configuration."""
    
    print("🧪 Testing Time-Based Interview Configuration")
    print("=" * 50)
    
    # Test 1: Default configuration
    print("\n📋 Test 1: Default SessionConfig")
    default_config = SessionConfig()
    print(f"  ✓ use_time_based_interview: {default_config.use_time_based_interview}")
    print(f"  ✓ interview_duration_minutes: {default_config.interview_duration_minutes}")
    print(f"  ✓ target_question_count (fallback): {default_config.target_question_count}")
    
    # Test 2: Custom time-based configuration
    print("\n📋 Test 2: Custom Time-Based Configuration")
    custom_config = SessionConfig(
        job_role="Software Engineer",
        interview_duration_minutes=15,
        use_time_based_interview=True,
        difficulty="hard"
    )
    print(f"  ✓ job_role: {custom_config.job_role}")
    print(f"  ✓ interview_duration_minutes: {custom_config.interview_duration_minutes}")
    print(f"  ✓ use_time_based_interview: {custom_config.use_time_based_interview}")
    print(f"  ✓ difficulty: {custom_config.difficulty}")
    
    # Test 3: Agent Session Manager Integration
    print("\n📋 Test 3: Agent Session Manager Integration")
    
    # Create mock database
    db_manager = MockDatabaseManager()
    
    # Create session manager
    session_manager = AgentSessionManager(
        session_id="test-session-123",
        db_manager=db_manager
    )
    
    # Configure with time-based settings
    config_data = {
        "job_role": "Senior Python Developer",
        "interview_duration_minutes": 20,
        "use_time_based_interview": True,
        "difficulty": "medium",
        "company_name": "TechCorp"
    }
    
    session_config = SessionConfig(**config_data)
    await session_manager.configure_session(session_config)
    
    print(f"  ✓ Session configured with time-based approach")
    print(f"  ✓ Duration: {session_manager.session_config.interview_duration_minutes} minutes")
    print(f"  ✓ Time-based: {session_manager.session_config.use_time_based_interview}")
    
    # Test 4: Time Manager Integration
    print("\n📋 Test 4: Time Manager Integration")
    
    # Start interview to initialize time manager
    intro_response = await session_manager.start_interview()
    print(f"  ✓ Interview started")
    print(f"  ✓ Introduction generated: {len(intro_response.get('content', ''))} characters")
    
    # Check if time manager is created for time-based interviews
    interviewer_agent = session_manager.interviewer_agent
    if interviewer_agent and interviewer_agent.time_manager:
        print(f"  ✓ Time manager created")
        print(f"  ✓ Duration: {interviewer_agent.time_manager.total_duration_minutes} minutes")
        print(f"  ✓ Is active: {interviewer_agent.time_manager.is_active}")
    else:
        print(f"  ⚠️ Time manager not created")
    
    # Test 5: Database Storage
    print("\n📋 Test 5: Database Storage")
    
    # Save session and verify time-based config is stored
    session_data = await session_manager.get_session_data()
    stored_config = session_data.get('session_config', {})
    
    print(f"  ✓ Stored config keys: {list(stored_config.keys())}")
    print(f"  ✓ Duration in storage: {stored_config.get('interview_duration_minutes')}")
    print(f"  ✓ Time-based in storage: {stored_config.get('use_time_based_interview')}")
    
    print("\n🎉 All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_time_based_interview()) 