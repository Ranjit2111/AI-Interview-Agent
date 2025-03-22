"""
Tests for the event bus module.
"""

import pytest
import json
from unittest.mock import MagicMock

from backend.utils.event_bus import EventBus, Event


@pytest.fixture
def event_bus():
    """Create an event bus instance for testing."""
    return EventBus()


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return Event(
        event_type="test_event",
        source="test_source",
        data={"key": "value"}
    )


class TestEvent:
    """Tests for the Event class."""
    
    def test_event_initialization(self):
        """Test that event initializes properly."""
        event = Event("test_event", "test_source", {"key": "value"})
        assert event.event_type == "test_event"
        assert event.source == "test_source"
        assert event.data == {"key": "value"}
        assert event.id  # Should have a UUID
        assert event.timestamp  # Should have a timestamp
    
    def test_to_dict(self, sample_event):
        """Test converting event to dictionary."""
        event_dict = sample_event.to_dict()
        assert event_dict["event_type"] == "test_event"
        assert event_dict["source"] == "test_source"
        assert event_dict["data"] == {"key": "value"}
        assert "id" in event_dict
        assert "timestamp" in event_dict
    
    def test_to_json(self, sample_event):
        """Test converting event to JSON."""
        event_json = sample_event.to_json()
        assert isinstance(event_json, str)
        
        # Should be valid JSON
        event_dict = json.loads(event_json)
        assert event_dict["event_type"] == "test_event"
    
    def test_from_dict(self):
        """Test creating event from dictionary."""
        event_dict = {
            "event_type": "test_event",
            "source": "test_source",
            "data": {"key": "value"},
            "id": "test_id",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        event = Event.from_dict(event_dict)
        assert event.event_type == "test_event"
        assert event.source == "test_source"
        assert event.data == {"key": "value"}
        assert event.id == "test_id"
        assert event.timestamp == "2023-01-01T00:00:00"
    
    def test_from_json(self):
        """Test creating event from JSON."""
        event_json = '{"event_type": "test_event", "source": "test_source", "data": {"key": "value"}, "id": "test_id", "timestamp": "2023-01-01T00:00:00"}'
        
        event = Event.from_json(event_json)
        assert event.event_type == "test_event"
        assert event.source == "test_source"
        assert event.data == {"key": "value"}
        assert event.id == "test_id"
        assert event.timestamp == "2023-01-01T00:00:00"


class TestEventBus:
    """Tests for the EventBus class."""
    
    def test_publish_subscribe(self, event_bus, sample_event):
        """Test basic publish/subscribe functionality."""
        # Create a mock callback
        callback = MagicMock()
        
        # Subscribe to the event type
        event_bus.subscribe("test_event", callback)
        
        # Publish the event
        event_bus.publish(sample_event)
        
        # Verify callback was called with the event
        callback.assert_called_once_with(sample_event)
    
    def test_wildcard_subscription(self, event_bus):
        """Test wildcard subscription that receives all events."""
        # Create a mock callback
        callback = MagicMock()
        
        # Subscribe to all events
        event_bus.subscribe("*", callback)
        
        # Publish two different events
        event1 = Event("event1", "source1", {"data": 1})
        event2 = Event("event2", "source2", {"data": 2})
        
        event_bus.publish(event1)
        event_bus.publish(event2)
        
        # Verify callback was called for both events
        assert callback.call_count == 2
        callback.assert_any_call(event1)
        callback.assert_any_call(event2)
    
    def test_multiple_subscribers(self, event_bus, sample_event):
        """Test multiple subscribers for the same event type."""
        # Create mock callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        # Subscribe both to the same event type
        event_bus.subscribe("test_event", callback1)
        event_bus.subscribe("test_event", callback2)
        
        # Publish the event
        event_bus.publish(sample_event)
        
        # Verify both callbacks were called
        callback1.assert_called_once_with(sample_event)
        callback2.assert_called_once_with(sample_event)
    
    def test_unsubscribe(self, event_bus, sample_event):
        """Test unsubscribing from events."""
        # Create a mock callback
        callback = MagicMock()
        
        # Subscribe to the event type
        event_bus.subscribe("test_event", callback)
        
        # Unsubscribe
        event_bus.unsubscribe("test_event", callback)
        
        # Publish the event
        event_bus.publish(sample_event)
        
        # Verify callback was not called
        callback.assert_not_called()
    
    def test_event_history(self, event_bus):
        """Test event history storage."""
        # Publish some events
        event1 = Event("event1", "source1", {"data": 1})
        event2 = Event("event2", "source2", {"data": 2})
        
        event_bus.publish(event1)
        event_bus.publish(event2)
        
        # Get all history
        history = event_bus.get_history()
        assert len(history) == 2
        assert history[0] is event1
        assert history[1] is event2
        
        # Get history for specific event type
        event_type_history = event_bus.get_history("event1")
        assert len(event_type_history) == 1
        assert event_type_history[0] is event1
    
    def test_get_event_types(self, event_bus):
        """Test getting registered event types."""
        # Subscribe to some event types
        callback = MagicMock()
        
        event_bus.subscribe("event1", callback)
        event_bus.subscribe("event2", callback)
        event_bus.subscribe("*", callback)
        
        # Get event types
        event_types = event_bus.get_event_types()
        assert len(event_types) == 3
        assert "event1" in event_types
        assert "event2" in event_types
        assert "*" in event_types
    
    def test_callback_error_handling(self, event_bus, sample_event):
        """Test that errors in callbacks are caught and don't affect other callbacks."""
        # Create callbacks, one of which raises an exception
        callback1 = MagicMock(side_effect=Exception("Test exception"))
        callback2 = MagicMock()
        
        # Subscribe both to the same event type
        event_bus.subscribe("test_event", callback1)
        event_bus.subscribe("test_event", callback2)
        
        # Publish the event (should not raise an exception)
        event_bus.publish(sample_event)
        
        # Verify second callback was still called
        callback2.assert_called_once_with(sample_event)


if __name__ == "__main__":
    pytest.main(["-v"]) 