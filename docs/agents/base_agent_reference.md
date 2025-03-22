# Base Agent Reference Guide

## Overview

The Base Agent module provides the foundation for all specialized agents in the AI Interviewer system. It defines the `BaseAgent` abstract class that all other agent classes inherit from and the `AgentContext` class that maintains conversation state. These components handle common functionality such as LLM initialization, tool management, context tracking, and event handling.

## File Structure

```
backend/
└── agents/
    ├── base.py                 # BaseAgent and AgentContext classes
    ├── interviewer.py          # InterviewerAgent implementation
    ├── coach.py                # CoachAgent implementation
    ├── skill_assessor.py       # SkillAssessorAgent implementation
    └── orchestrator.py         # Agent coordination
```

## Key Classes

### AgentContext

A context object for agents to maintain state across interactions.

```python
class AgentContext:
    # ...implementation...
```

### BaseAgent

An abstract base class that all specialized agents inherit from.

```python
class BaseAgent(ABC):
    # ...implementation...
```

## AgentContext Class

The `AgentContext` class manages conversation state and history for agent interactions.

### Key Attributes

- **`session_id`**: Unique identifier for the conversation session
- **`user_id`**: Optional identifier for the user
- **`conversation_history`**: List of messages in the conversation
- **`metadata`**: Dictionary for storing additional context information
- **`created_at`**: Timestamp when the context was created
- **`last_updated`**: Timestamp when the context was last updated

### Key Methods

#### Constructor Methods

- **`__init__(session_id, user_id=None)`**: Initializes a new context object
- **`from_dict(data)`**: Class method to create a context from a dictionary

#### State Management Methods

- **`add_message(role, content, metadata=None)`**: Adds a message to the conversation history
- **`get_history_as_text(max_tokens=None)`**: Gets the conversation history as formatted text
- **`get_langchain_messages()`**: Converts conversation history to LangChain message format
- **`to_dict()`**: Converts the context to a dictionary

## BaseAgent Class

The `BaseAgent` abstract class provides common functionality for all agents.

### Key Attributes

- **`api_key`**: API key for the language model
- **`model_name`**: Name of the language model to use
- **`planning_interval`**: How often to run planning steps
- **`step_count`**: Counter for tracking interaction steps
- **`llm`**: LangChain LLM instance
- **`event_bus`**: Event bus for inter-agent communication
- **`logger`**: Logger for the agent
- **`current_context`**: Current conversation context
- **`tools`**: List of LangChain tools
- **`agent_executor`**: LangChain agent executor

### Key Methods

#### Lifecycle Methods

- **`__init__(api_key, model_name, planning_interval, event_bus, logger)`**: Initializes the agent
- **`_initialize_tools()`**: Abstract method to initialize tools for the agent
- **`_setup_agent_executor()`**: Sets up the LangChain agent executor

#### Core Logic Methods

- **`process_input(input_text, context)`**: Abstract method to process user input
- **`process_with_langchain(input_text, context)`**: Processes input using LangChain
- **`_get_system_prompt()`**: Gets the system prompt for the agent

#### Context Management Methods

- **`create_context(session_id, user_id)`**: Creates a new context
- **`load_context(context)`**: Loads an existing context

#### Planning Methods

- **`_should_plan()`**: Determines if planning should be executed
- **`_run_planning_step(context)`**: Runs a planning step

#### Event Handling Methods

- **`publish_event(event_type, data)`**: Publishes an event to the event bus
- **`subscribe(event_type, callback)`**: Subscribes to events of a specific type

## Data Flow

1. The agent receives input from a user or another component
2. The agent's context is updated with the new input
3. The input is processed using either specialized logic or LangChain tools
4. Events may be published to communicate with other agents
5. The agent generates a response and adds it to the context
6. The response is returned to the caller

## Common Modifications

### Adding New Tools

To add new tools to an agent:

1. Override the `_initialize_tools()` method in the specialized agent class
2. Add the new tools to the list returned by the method

```python
def _initialize_tools(self) -> List[Tool]:
    return [
        Tool(
            name="new_tool",
            func=self._new_tool_function,
            description="Description of the new tool"
        ),
        # ... other tools ...
    ]
```

### Customizing the System Prompt

To customize the system prompt:

1. Override the `_get_system_prompt()` method in the specialized agent class
2. Return the custom system prompt

```python
def _get_system_prompt(self) -> str:
    return (
        "You are a specialized AI assistant with specific capabilities. "
        "Your goal is to help users with tasks related to your specialization."
    )
```

### Adding Planning Capabilities

To add planning capabilities:

1. Set a non-zero `planning_interval` in the agent's initialization
2. Override the `_run_planning_step(context)` method to implement planning logic

```python
def _run_planning_step(self, context: AgentContext) -> Dict[str, Any]:
    # Analyze conversation history
    # Generate a plan for future responses
    return {
        "planning_completed": True,
        "plan": "Details of the plan"
    }
```

### Adding Custom Event Handling

To add custom event handling:

1. Subscribe to specific event types in the agent's initialization
2. Implement callback methods to handle the events

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.event_bus:
        self.event_bus.subscribe("custom_event", self._handle_custom_event)

def _handle_custom_event(self, event: Event) -> None:
    # Handle the custom event
    pass
```

## Best Practices

1. **Context Management**: Always update the context with new messages
2. **Tool Design**: Design tools to be self-contained, focused, and well-documented
3. **Error Handling**: Handle exceptions in agent methods to prevent crashes
4. **Logging**: Use the logger to record important events and debug information
5. **Event Coordination**: Use the event bus for loose coupling between agents
6. **Planning**: Implement planning for complex, multi-turn interactions
7. **API Management**: Handle API key management securely

## Common Issues and Solutions

### Issue: Agent Not Responding Correctly

**Solution**: Ensure the system prompt in `_get_system_prompt()` provides clear instructions. Check if the tools are properly defined and that the agent executor is initialized correctly.

### Issue: Context Getting Too Large

**Solution**: Implement context windowing or summarization in the agent's `process_input` method to prevent the context from becoming too large for the model's context window.

### Issue: Events Not Being Received

**Solution**: Verify that the event bus is properly initialized and that the agent is subscribing to the correct event types. Check for typos in event type strings.

### Issue: Tool Execution Failures

**Solution**: Add better error handling in tool functions. Make sure tool functions return the expected output format, and handle edge cases gracefully.

## API Integration Points

The Base Agent module provides several integration points for the rest of the system:

- **Event Bus**: Allows agents to communicate with each other and other components
- **Agent Context**: Provides a standardized way to maintain conversation state
- **Tool Interface**: Allows agents to provide specialized functionality to the LLM

## Extension Points

The Base Agent module is designed to be extended in several ways:

1. **Inheriting from BaseAgent**: Create specialized agents for specific tasks
2. **Adding New Tools**: Extend an agent's capabilities with new tools
3. **Customizing Prompts**: Change how the agent interacts with the LLM
4. **Adding Event Handlers**: React to events from other components
