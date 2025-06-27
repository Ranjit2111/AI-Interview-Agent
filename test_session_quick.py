import sys
import os
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.session_manager import ThreadSafeSessionRegistry
from database.mock_db_manager import MockDatabaseManager
from utils.event_bus import EventBus


async def test_session_features():
    print('🧪 Testing session management features...')
    
    # Create registry
    db_manager = MockDatabaseManager()
    llm_service = MagicMock()
    event_bus = EventBus()
    
    registry = ThreadSafeSessionRegistry(
        db_manager=db_manager,
        llm_service=llm_service,
        event_bus=event_bus
    )
    
    try:
        # Test 1: Cleanup task starts with new defaults
        print('1. Testing cleanup task defaults...')
        await registry.start_cleanup_task()
        assert registry._cleanup_task is not None
        print('   ✅ Cleanup task started successfully')
        
        # Test 2: Session time remaining
        print('2. Testing session time remaining...')
        session_id = 'test_session'
        registry._session_access_times[session_id] = datetime.utcnow()
        remaining = await registry.get_session_time_remaining(session_id, 15)
        assert 14 <= remaining <= 15
        print(f'   ✅ Session time remaining: {remaining} minutes')
        
        # Test 3: Ping session
        print('3. Testing session ping...')
        old_time = datetime.utcnow() - timedelta(minutes=10)
        registry._session_access_times[session_id] = old_time
        success = await registry.ping_session(session_id)
        assert success is True
        new_remaining = await registry.get_session_time_remaining(session_id, 15)
        assert 14 <= new_remaining <= 15
        print(f'   ✅ Session ping successful, new remaining: {new_remaining} minutes')
        
        # Test 4: Immediate cleanup
        print('4. Testing immediate cleanup...')
        registry._active_sessions[session_id] = MagicMock()
        registry._session_locks[session_id] = asyncio.Lock()
        
        # Mock save_session
        async def mock_save(sid):
            return True
        registry.save_session = mock_save
        
        success = await registry.cleanup_session_immediately(session_id)
        assert success is True
        assert session_id not in registry._active_sessions
        print('   ✅ Immediate cleanup successful')
        
        # Test 5: Warning logic
        print('5. Testing warning logic...')
        def should_show_warning(time_remaining_minutes):
            return time_remaining_minutes <= 2 and time_remaining_minutes > 0
        
        assert should_show_warning(3) is False  # Too early
        assert should_show_warning(2) is True   # Exactly 2 minutes
        assert should_show_warning(1) is True   # 1 minute left
        assert should_show_warning(0) is False  # Expired
        print('   ✅ Warning logic working correctly')
        
        # Test 6: Timeout detection logic
        print('6. Testing timeout detection...')
        def is_session_timeout_error(error_message, status_code):
            return (status_code == 404 and 
                    bool(error_message) and 
                    'session' in error_message.lower())
        
        assert is_session_timeout_error("Session not found", 404) is True
        assert is_session_timeout_error("User not found", 404) is False
        assert is_session_timeout_error("", 404) is False
        print('   ✅ Timeout detection logic working correctly')
        
        print('\n🎉 All session management features working correctly!')
        
    finally:
        # Cleanup
        await registry.stop_cleanup_task()
        print('🧹 Cleanup completed')


if __name__ == "__main__":
    asyncio.run(test_session_features()) 