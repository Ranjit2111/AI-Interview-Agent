"""
Tests for the base agent module.
"""

import pytest
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.base import BaseAgent, AgentContext
from backend.utils.event_bus import EventBus, Event


class TestBaseAgent(BaseAgent):
    """Test implementation of BaseAgent for testing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_input_called = False
    
    def process_input(self, input_text, context=None):
        self.process_input_called = True
        return f"Processed: {input_text}"


@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")


@pytest.fixture
def agent(mock_env):
    """Create a test agent instance."""
    return TestBaseAgent()


@pytest.fixture
def context():
    """Create a test context."""
    return AgentContext(session_id="test_session", user_id="test_user")


class TestAgentContext:
    """Tests for the AgentContext class."""
    
    @pytest.fixture
    def context(self):
        """Create a test context."""
        return AgentContext()
    
    def test_initialization(self, context):
        """Test that context initializes properly."""
        assert context.messages == []
        assert context.metadata == {}
    
    def test_add_message(self, context):
        """Test adding messages to context."""
        # Add a message
        context.add_message("user", "Hello")
        
        # Verify message was added
        assert len(context.messages) == 1
        assert context.messages[0]["role"] == "user"
        assert context.messages[0]["content"] == "Hello"
        assert "timestamp" in context.messages[0]
    
    def test_get_history_as_text(self, context):
        """Test getting message history as text."""
        # Add some messages
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there!")
        
        # Get history as text
        history = context.get_history_as_text()
        
        # Verify history format
        assert "user: Hello" in history
        assert "assistant: Hi there!" in history
    
    def test_to_langchain_messages(self, context):
        """Test converting to LangChain messages."""
        # Add some messages
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there!")
        
        # Convert to LangChain messages
        messages = context.to_langchain_messages()
        
        # Verify messages
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"
    
    def test_serialization(self, context):
        """Test context serialization."""
        # Add some data
        context.add_message("user", "Hello")
        context.metadata["test_key"] = "test_value"
        
        # Serialize context
        context_dict = context.to_dict()
        
        # Verify serialization
        assert "messages" in context_dict
        assert "metadata" in context_dict
        assert context_dict["metadata"]["test_key"] == "test_value"
    
    def test_deserialization(self):
        """Test context deserialization."""
        # Create test data
        test_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "metadata": {"test_key": "test_value"}
        }
        
        # Create context from data
        context = AgentContext.from_dict(test_data)
        
        # Verify deserialization
        assert len(context.messages) == 1
        assert context.messages[0]["content"] == "Hello"
        assert context.metadata["test_key"] == "test_value"


class TestBaseAgentClass:
    """Tests for the BaseAgent class."""
    
    def test_agent_initialization(self, mock_env):
        """Test that agent initializes properly."""
        agent = TestBaseAgent()
        assert agent.api_key == "test_api_key"
        assert agent.model_name == "gemini-1.5-pro"
        assert agent.planning_interval == 0
        assert agent.step_count == 0
        assert agent.llm is not None
        assert agent.event_bus is not None
        assert agent.current_context is None
    
    def test_create_context(self, agent):
        """Test creating a new context."""
        context = agent.create_context(user_id="test_user")
        assert context.user_id == "test_user"
        assert agent.current_context is context
    
    def test_process_input(self, agent, context):
        """Test processing input."""
        response = agent.process_input("Hello", context)
        assert response == "Processed: Hello"
        assert agent.process_input_called
    
    def test_load_context(self, agent, context):
        """Test loading a context."""
        agent.load_context(context)
        assert agent.current_context is context
    
    @patch.object(BaseAgent, 'publish_event')
    def test_publish_event(self, mock_publish, agent):
        """Test publishing an event."""
        agent.publish_event("test_event", {"data": "value"})
        mock_publish.assert_called_once_with("test_event", {"data": "value"})
    
    def test_subscribe(self, agent):
        """Test subscribing to events."""
        callback = MagicMock()
        agent.subscribe("test_event", callback)
        
        # Publish an event and verify callback was called
        event = Event("test_event", "test_source", {"data": "value"})
        agent.event_bus.publish(event)
        
        callback.assert_called_once()
        args, _ = callback.call_args
        assert args[0] is event


if __name__ == "__main__":
    pytest.main(["-v"]) 