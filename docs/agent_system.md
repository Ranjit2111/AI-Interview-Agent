# Agent System Documentation

## Overview

The AI Interviewer Agent uses a multi-agent architecture with specialized agents handling different aspects of the interview process. This document outlines the agent system design, communication patterns, and implementation details for developers.

## Agent Architecture

The agent system follows a modular design with the following key components:

1. **Base Agent**: Abstract foundation class implementing common agent functionality
2. **Specialized Agents**: Role-specific implementations (Interviewer, Coach, Skill Assessor)
3. **Agent Orchestrator**: Central coordinator that manages agent interactions
4. **Event Bus**: Communication system that enables agents to exchange information
5. **Agent Context**: State management for preserving conversation history and metadata

### Class Hierarchy

```
BaseAgent (Abstract)
├── InterviewerAgent
├── CoachAgent
└── SkillAssessorAgent

AgentOrchestrator
├── manages InterviewerAgent
├── manages CoachAgent
└── manages SkillAssessorAgent
```

## Core Components

### BaseAgent

The `BaseAgent` class provides foundational functionality for all agent types:

```python
class BaseAgent:
    def __init__(self, api_key, model_name, planning_interval, event_bus, logger):
        # Initialization logic
      
    def _call_llm(self, prompt, context):
        # Interface with LLM
      
    def _publish_event(self, event_type, data):
        # Publish event to the event bus
      
    def _handle_event(self, event):
        # Process incoming events
```

Key features:

- LLM integration through standardized interface
- Event publishing and subscription
- Context management
- Planning intervals for agent reflection

### AgentContext

The `AgentContext` class maintains state across interactions:

```python
class AgentContext:
    def __init__(self, session_id, user_id=None):
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_history = []
        self.metadata = {}
      
    def add_message(self, role, content, metadata=None):
        # Add message to history
      
    def get_history_as_text(self, max_tokens=None):
        # Get formatted conversation history
```

Key features:

- Session and user tracking
- Conversation history management
- Metadata storage
- Serialization/deserialization

### Event Bus

The `EventBus` implements a publish/subscribe pattern for agent communication:

```python
class EventBus:
    def __init__(self):
        self.subscribers = {}
        self.event_history = []
      
    def publish(self, event):
        # Distribute event to subscribers
      
    def subscribe(self, event_type, callback):
        # Register subscriber callback
      
    def unsubscribe(self, event_type, callback):
        # Remove subscriber callback
```

Key features:

- Topic-based filtering with wildcard support
- Event history tracking
- Error handling for subscriber callbacks

### Agent Orchestrator

The `AgentOrchestrator` coordinates the multi-agent system:

```python
class AgentOrchestrator:
    def __init__(self, api_key, model_name, logger, mode, job_role, job_description, interview_style):
        # Initialize and configure agents based on mode
      
    def process_input(self, input_text, user_id=None):
        # Route input to appropriate agent(s)
      
    def switch_mode(self, new_mode):
        # Change orchestrator mode
      
    def switch_agent(self, agent_type):
        # Activate specific agent
```

Key features:

- Dynamic agent initialization based on mode
- Input routing and response aggregation
- Mode switching for different interview experiences
- Command handling

## Specialized Agents

### Interviewer Agent

Conducts the interview by generating questions, evaluating responses, and guiding the conversation flow.

Key capabilities:

- Question generation based on job context
- Response evaluation
- Conversation flow management
- Interview style adaptation

### Coach Agent

Provides real-time feedback on interview responses using frameworks like STAR.

Key capabilities:

- STAR analysis (Situation, Task, Action, Result)
- Feedback categorization (structure, content, delivery)
- Constructive suggestion generation
- Personalized improvement guidance

### Skill Assessor Agent

Identifies and evaluates technical and soft skills mentioned in responses.

Key capabilities:

- Skill identification and categorization
- Proficiency assessment
- Skill gap analysis
- Learning resource recommendation

## Communication Patterns

### Event-Driven Architecture

The agent system uses event-driven communication with the following patterns:

1. **Publish/Subscribe**: Agents publish events and subscribe to topics of interest
2. **Command Pattern**: Orchestrator issues commands to agents
3. **Observer Pattern**: Agents observe and react to system state changes

### Event Types

Common event types in the system include:

- `user_message`: New input from the user
- `agent_response`: Response generated by an agent
- `feedback_generated`: Feedback created by the Coach Agent
- `skill_identified`: Skill detected by the Skill Assessor
- `mode_changed`: Orchestrator mode was changed
- `agent_switched`: Active agent was changed

### Event Format

Events follow a standardized format:

```python
@dataclass
class Event:
    event_type: str
    source: str
    data: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

## LLM Integration

### Prompt Construction

Agents use structured prompts with standardized components:

1. **System Context**: Information about the agent's role and capabilities
2. **Conversation History**: Previous exchanges for context
3. **User Input**: The current message to process
4. **Instruction**: Specific task for the LLM to perform
5. **Format**: Expected response structure

### Planning Intervals

Agents can utilize "planning intervals" to reflect on the conversation and adjust their approach. This is inspired by the smallagents pattern:

```python
if self.planning_steps % self.planning_interval == 0:
    self._perform_planning(context)
```

## Implementation Guide

### Creating a New Agent Type

To create a new specialized agent:

1. Inherit from `BaseAgent`
2. Implement required methods
3. Register with the `AgentOrchestrator`

Example:

```python
class CustomAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
      
    def process_message(self, message, context):
        # Custom processing logic
        return response
```

### Subscribing to Events

To make an agent react to specific events:

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.event_bus.subscribe("skill_identified", self._handle_skill_event)
  
def _handle_skill_event(self, event):
    # Process skill information
```

### Customizing the Orchestrator

To modify the orchestrator's behavior:

1. Add a new mode to `OrchestratorMode`
2. Update `_initialize_agents()` to handle the new mode
3. Implement logic for the new coordination pattern

## Testing Agents

The system includes a testing framework for agent behavior:

1. **Mock Services**: Fake LLM and external APIs for testing
2. **Test Fixtures**: Reusable contexts and event buses
3. **Event Assertions**: Verify event publishing and handling

Example test:

```python
def test_interviewer_question_generation():
    # Initialize test components
    context = AgentContext("test-session")
    agent = InterviewerAgent(api_key=MOCK_API_KEY)
  
    # Process a message
    response = agent.process_message("Tell me about your experience", context)
  
    # Assert expected behavior
    assert "?" in response  # Response contains a question
```

## Performance Considerations

### Token Management

The system optimizes token usage through:

1. Context windowing (trimming conversation history)
2. Prompt compression techniques
3. Selective event inclusion in prompts

### Rate Limiting

Google Gemini API rate limits are handled with:

1. Backoff mechanisms for retries
2. Token counting to stay within limits
3. Request batching where appropriate

## Security Considerations

- API keys stored in environment variables
- No external data transmission (local processing)
- Input validation and sanitization
- Proper error handling to prevent information leakage

## Best Practices

1. **Event Design**: Keep events focused and specific
2. **Agent Responsibility**: Maintain clear separation of concerns
3. **Context Management**: Be mindful of token usage in context
4. **Error Handling**: Implement robust error recovery
5. **Testing**: Write tests for agent interactions

## Future Extensions

The agent system is designed for extensibility with these potential future additions:

1. **Web Search Agent**: Retrieve information from the internet
2. **Coding Agent**: Evaluate technical code solutions
3. **Voice Analysis Agent**: Assess audio delivery aspects
4. **Memory Agent**: Maintain long-term user profile

---

This documentation provides a comprehensive overview of the agent system. Developers should refer to the specific class implementations for detailed API references and method signatures.
