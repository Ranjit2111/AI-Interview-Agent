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
from backend.tests.utils.mock_services import MockGeminiAPI, MOCK_API_KEY


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


# Test implementation of BaseAgent for testing
class TestableBaseAgent(BaseAgent):
    """
    Implementation of BaseAgent for testing purposes.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def process_message(self, message: str, context: AgentContext):
        """
        Simple implementation of process_message for testing.
        
        Args:
            message: User message
            context: Agent context
            
        Returns:
            Response message
        """
        # Use the LLM to generate a response
        response = self._call_llm(
            prompt=f"Respond to this message: {message}",
            context=context
        )
        return response


class TestBaseAgent:
    """
    Tests for the BaseAgent class.
    """
    
    @pytest.fixture
    def mock_gemini_api(self):
        """Fixture for MockGeminiAPI."""
        return MockGeminiAPI({
            "Respond to this message: hello": "Hello! How can I help you today?",
            "Respond to this message: test": "This is a test response."
        })
    
    @pytest.fixture
    def event_bus(self):
        """Fixture for EventBus."""
        return EventBus()
    
    @pytest.fixture
    def agent_context(self):
        """Fixture for AgentContext."""
        context = AgentContext(session_id="test-session")
        return context
    
    @patch("langchain_google_generativeai.ChatGoogleGenerativeAI")
    def test_initialization(self, mock_llm):
        """Test BaseAgent initialization."""
        # Setup mock
        mock_llm.return_value = MagicMock()
        
        # Create agent
        agent = TestableBaseAgent(
            api_key=MOCK_API_KEY,
            model_name="gemini-1.5-pro"
        )
        
        # Check agent properties
        assert agent.api_key == MOCK_API_KEY
        assert agent.model_name == "gemini-1.5-pro"
        assert agent.planning_interval == 0
        assert agent.event_bus is not None
    
    def test_process_message_with_mock(self, mock_gemini_api, agent_context):
        """Test process_message with mocked LLM."""
        # Patch the LLM method
        with patch.object(TestableBaseAgent, '_call_llm', return_value="Hello! How can I help you today?"):
            agent = TestableBaseAgent(api_key=MOCK_API_KEY)
            
            # Process a message
            response = agent.process_message("hello", agent_context)
            
            # Check response
            assert response == "Hello! How can I help you today!"
    
    def test_event_publishing(self, event_bus, agent_context):
        """Test event publishing."""
        # Set up a listener
        received_events = []
        def event_listener(event):
            received_events.append(event)
        
        # Subscribe to all events
        event_bus.subscribe("*", event_listener)
        
        # Create agent with event bus
        agent = TestableBaseAgent(
            api_key=MOCK_API_KEY,
            event_bus=event_bus
        )
        
        # Publish an event
        agent._publish_event("test_event", {"data": "test_data"})
        
        # Check if event was received
        assert len(received_events) == 1
        assert received_events[0].event_type == "test_event"
        assert received_events[0].source == "TestableBaseAgent"
        assert received_events[0].data["data"] == "test_data"


if __name__ == "__main__":
    pytest.main(["-v"]) 