# Orchestrator Agent Reference Guide

## Overview

The Agent Orchestrator is responsible for coordinating multiple agents in the AI Interviewer system. It manages the lifecycle of agents, routes user input to the appropriate agents, aggregates responses from multiple agents, determines when to switch between agents, and maintains a coherent conversation flow. The orchestrator acts as the central coordination point for all agent interactions.

## File Structure

```
backend/
└── agents/
    ├── orchestrator.py         # AgentOrchestrator implementation
    ├── base.py                 # BaseAgent and AgentContext classes
    ├── interviewer.py          # InterviewerAgent implementation 
    ├── coach.py                # CoachAgent implementation
    └── skill_assessor.py       # SkillAssessorAgent implementation
```

## Key Classes and Enums

### AgentOrchestrator

The main orchestrator class responsible for coordinating multiple agents.

```python
class AgentOrchestrator:
    # ...implementation...
```

### OrchestratorMode

Enum-like class defining the different operating modes for the orchestrator.

```python
class OrchestratorMode(str):
    INTERVIEW_ONLY = "interview_only"
    INTERVIEW_WITH_COACHING = "interview_with_coaching"
    COACHING_ONLY = "coaching_only"
    SKILL_ASSESSMENT = "skill_assessment"
    FULL_FEEDBACK = "full_feedback"
```

## Orchestrator Modes

The orchestrator can operate in several modes, each activating different combinations of agents:

- **`INTERVIEW_ONLY`**: Only the interviewer agent responds to the user
- **`INTERVIEW_WITH_COACHING`**: The interviewer leads the conversation, with the coach providing feedback
- **`COACHING_ONLY`**: Only the coach agent responds to the user
- **`SKILL_ASSESSMENT`**: Focused on skill assessment through the skill assessor agent
- **`FULL_FEEDBACK`**: All agents provide feedback to each user input

## Key Methods

### Initialization and Setup Methods

- **`__init__`**: Initializes the orchestrator with configuration options
- **`_initialize_agents`**: Initializes agents based on the current mode

### Core Logic Methods

- **`process_input`**: Processes user input and routes it to the appropriate agent(s)
- **`_get_active_agent_response`**: Gets a response from the currently active agent
- **`_get_all_agent_responses`**: Gets responses from all active agents
- **`_format_multi_agent_response`**: Formats responses from multiple agents

### State Management Methods

- **`_get_agent_context`**: Gets or creates a context for an agent
- **`_handle_event`**: Handles events from the event bus

### Command Handling Methods

- **`_handle_help_command`**: Handles the /help command
- **`_handle_mode_command`**: Handles the /mode command
- **`_handle_reset_command`**: Handles the /reset command
- **`_handle_agents_command`**: Handles the /agents command
- **`_handle_switch_command`**: Handles the /switch command
- **`_handle_start_command`**: Handles the /start command
- **`_handle_end_command`**: Handles the /end command

## Available Commands

The orchestrator supports several slash commands for controlling the interview:

- **`/help`**: Shows the help message with available commands
- **`/mode [mode]`**: Shows or sets the orchestrator mode
- **`/reset`**: Resets the current session
- **`/agents`**: Lists available agents
- **`/switch [agent]`**: Switches to a different agent
- **`/start`**: Starts a new interview
- **`/end`**: Ends the current interview

## Data Flow

1. The user sends input to the orchestrator
2. The orchestrator adds the input to the conversation history
3. The orchestrator publishes a user_response event
4. The orchestrator checks if the input is a command
5. If it's a command, the orchestrator handles it directly
6. If it's not a command, the orchestrator determines which agent(s) should respond
7. The orchestrator gets responses from the appropriate agent(s)
8. The orchestrator formats and returns the response(s)

## Event Handling

The orchestrator subscribes to all events (`*`) and handles them in the `_handle_event` method. It publishes the following events:

- **`user_response`**: When the user provides input
- **`session_reset`**: When the session is reset
- **`interview_start`**: When a new interview starts
- **`interview_end`**: When an interview ends

## Common Modifications

### Adding a New Agent Type

To add a new type of agent to the orchestrator:

1. Import the new agent class at the top of the file
2. Update the `_initialize_agents` method to create an instance of the new agent
3. Update the orchestrator modes to include the new agent as needed

```python
from backend.agents.new_agent import NewAgent

# In _initialize_agents method
if self.mode in [OrchestratorMode.NEW_MODE]:
    new_agent = NewAgent(
        api_key=self.api_key,
        model_name=self.model_name,
        event_bus=self.event_bus,
        logger=self.logger
    )
    self.agents["new_agent"] = new_agent
```

### Adding a New Orchestrator Mode

To add a new orchestrator mode:

1. Add the new mode to the `OrchestratorMode` class
2. Update the `_initialize_agents` method to handle the new mode
3. Update the `_handle_mode_command` method to include the new mode

```python
class OrchestratorMode(str):
    # ... existing modes ...
    NEW_MODE = "new_mode"
```

### Customizing Multi-Agent Response Formatting

To customize how responses from multiple agents are formatted:

1. Modify the `_format_multi_agent_response` method
2. Change the formatting logic to suit your needs

```python
def _format_multi_agent_response(self, responses: Dict[str, str]) -> str:
    # Custom formatting logic
    # ...
    return formatted_response
```

### Adding a New Command

To add a new command:

1. Add the command handler to the `commands` dictionary in `__init__`
2. Implement the command handler method

```python
# In __init__ method
self.commands = {
    # ... existing commands ...
    "new_command": self._handle_new_command
}

def _handle_new_command(self, args: List[str]) -> str:
    # Command implementation
    return "New command executed"
```

## Best Practices

1. **Agent Coordination**: Use the event bus for asynchronous communication between agents
2. **Mode Selection**: Choose the appropriate orchestrator mode based on the user's needs
3. **Context Isolation**: Maintain separate contexts for each agent to prevent interference
4. **Response Formatting**: Format multi-agent responses carefully to ensure clarity
5. **Command Design**: Make commands intuitive and provide clear help text
6. **Event Design**: Use specific event types for clear communication

## Common Issues and Solutions

### Issue: Agents Not Receiving Events

**Solution**: Verify that the event bus is properly initialized and that agents are subscribing to the correct event types. Check if the event types match exactly between publishers and subscribers.

### Issue: Inconsistent Agent Responses

**Solution**: Ensure that each agent has its own isolated context. Check if the `_get_agent_context` method is being called properly for each agent interaction.

### Issue: Command Confusion

**Solution**: Improve command help text and provide more feedback when commands are used incorrectly. Consider adding examples to help text.

### Issue: Mode Switching Problems

**Solution**: When switching modes, ensure that all necessary agents are initialized. Update the `_initialize_agents` method to handle mode transitions gracefully.

## API Integration Points

The orchestrator integrates with the rest of the system through:

- **Direct Input Processing**: The `process_input` method is called directly by the API
- **Event Publications**: The orchestrator publishes events for other components to consume
- **Event Subscriptions**: The orchestrator subscribes to events from other components

## Extension Points

The orchestrator is designed to be extended in several ways:

1. **New Agents**: Add new agent types for specialized functionality
2. **New Modes**: Create new combinations of agents for different user needs
3. **New Commands**: Add new commands for additional user control
4. **Custom Response Formatting**: Change how multi-agent responses are presented 