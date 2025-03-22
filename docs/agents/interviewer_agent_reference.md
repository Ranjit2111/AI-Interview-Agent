# Interviewer Agent Reference Guide

## Overview

The Interviewer Agent is responsible for conducting technical interviews with users. It manages the flow of the interview, generates questions, evaluates answers, and provides a comprehensive interview experience. The agent simulates a realistic interview scenario by asking contextually relevant questions and providing professional responses.

## File Structure and Responsibilities

### Main Files

- **`backend/agents/interviewer.py`**: Core implementation of the interviewer agent
- **`backend/agents/templates/interviewer_templates.py`**: Templates used by the interviewer agent
- **`backend/agents/utils/llm_utils.py`**: Utility functions for LLM operations

### Key Relationships

The Interviewer Agent inherits from the BaseAgent class (`backend/agents/base.py`) and relies on templates defined in `interviewer_templates.py` for generating prompts. It uses utility functions from `llm_utils.py` for error handling and JSON parsing.

## Key Classes and Methods

### `InterviewerAgent` Class

The main class that implements the interviewer agent functionality.

#### Lifecycle Methods

- **`__init__(self, config={}, **kwargs)`**: Initializes the agent with configuration parameters
- **`_setup_llm_chains(self)`**: Sets up the language model chains for different operations
- **`invoke(self, state, events, config={})`**: Main entry point for agent invocation

#### State Management Methods

- **`_get_system_prompt(self)`**: Generates the system prompt based on job context
- **`_initialize_state(self, request)`**: Sets up initial interview state
- **`_handle_transition(self, state, events)`**: Manages state transitions during the interview

#### Core Logic Methods

- **`_think_about_input(self, user_input, context)`**: Analyzes user input to determine intent
- **`_reason_about_next_action(self, context)`**: Decides the next action based on context
- **`_do_action(self, action_data, context)`**: Performs the specified action
- **`_generate_next_question_tool(self, context)`**: Generates a new interview question

#### Utility Methods

- **`_get_interview_context(self, state)`**: Compiles the context for the interview
- **`process_input(self, user_input, state)`**: Processes user input and updates state

### Interview States

The agent operates through a state machine with the following states:

1. **`INITIALIZING`**: Setting up the interview session
2. **`INTRODUCTION`**: Introducing the interview process
3. **`QUESTIONING`**: Asking interview questions and evaluating responses
4. **`FOLLOWING_UP`**: Asking follow-up questions based on previous answers
5. **`SUMMARIZING`**: Providing a summary of the interview
6. **`ENDED`**: Interview has concluded

## Templates

The following templates from `interviewer_templates.py` are used:

- **`INTERVIEWER_SYSTEM_PROMPT`**: Defines the interviewer's persona and behavior
- **`THINK_TEMPLATE`**: Used to analyze user input
- **`REASON_TEMPLATE`**: Used to determine the next action
- **`QUESTION_GENERATION_TEMPLATE`**: Creates interview questions
- **`ANSWER_EVALUATION_TEMPLATE`**: Evaluates candidate responses
- **`RESPONSE_FORMAT_TEMPLATE`**: Ensures consistent response formatting
- **`INTERVIEW_SUMMARY_TEMPLATE`**: Generates interview summaries

## Data Flow and Dependencies

### Main Workflow

1. **Initialization**:
   - Agent is created with configuration
   - LLM chains are set up
   - System prompt is generated

2. **Introduction**:
   - Agent introduces itself and explains the interview process
   - Initial context is gathered

3. **Question Generation**:
   - Agent uses job context to generate relevant questions
   - Questions increase in difficulty based on performance

4. **Answer Processing**:
   - User answers are analyzed using `_think_about_input`
   - Evaluation is performed using templates

5. **Follow-up and Transitions**:
   - Agent may ask follow-up questions based on responses
   - State transitions are managed by `_handle_transition`

6. **Summarizing**:
   - Agent provides a comprehensive interview summary

### Event Handling

The agent responds to the following events:

- **`StateChangedEvent`**: Triggered when the interview state changes
- **`UserInputEvent`**: Triggered when the user provides input
- **`InterviewEndEvent`**: Triggered when the interview concludes

## Common Modifications

### Adding New Question Types

To add a new question type:

1. Update the `QUESTION_GENERATION_TEMPLATE` in `interviewer_templates.py` to include the new type
2. Adjust the `_generate_next_question_tool` method to handle the new type
3. Update the evaluation logic if necessary

### Modifying Evaluation Criteria

To change how answers are evaluated:

1. Update the `ANSWER_EVALUATION_TEMPLATE` in `interviewer_templates.py`
2. Modify the JSON schema expected in the response
3. Adjust any processing of evaluation results

### Changing Interview Flow

To modify the interview flow:

1. Update the state machine in `_handle_transition`
2. Add or modify state handlers in `_do_action`
3. Update the transition logic based on new requirements

### Adjusting Persona

To change the interviewer's persona:

1. Update the `INTERVIEWER_SYSTEM_PROMPT` in `interviewer_templates.py`
2. Modify the response formatting to match the new persona

## Best Practices

1. **Template Usage**:
   - Keep all LLM interactions in templates
   - Document template placeholders
   - Test templates with various inputs

2. **Error Handling**:
   - Always use `invoke_chain_with_error_handling` for LLM calls
   - Provide meaningful default responses
   - Add fallback behavior for critical functions

3. **State Management**:
   - Maintain clean state transitions
   - Keep context information updated
   - Validate state before processing

4. **Performance Considerations**:
   - Minimize token usage in prompts
   - Batch similar operations
   - Cache frequently used information

## Common Issues and Solutions

### Issue: Questions are not relevant to the job role

**Solution**: Check the job context being passed to the agent and ensure it's properly included in the `QUESTION_GENERATION_TEMPLATE`. You may need to enhance the template to be more specific about using the job context.

### Issue: Evaluations are inconsistent

**Solution**: Modify the `ANSWER_EVALUATION_TEMPLATE` to provide more structured guidance and clearer evaluation criteria. Consider implementing a scoring rubric or specific points to address in the evaluation.

### Issue: Interview flow feels mechanical

**Solution**: Enhance the `INTERVIEWER_SYSTEM_PROMPT` to include more personality and conversational elements. Also, consider adding more varied transition phrases in the response formatting.

### Issue: Agent gets stuck in a state

**Solution**: Review the state transition logic in `_handle_transition` and add appropriate fallback mechanisms. Ensure all state transitions are properly handled and have timeout or retry mechanisms. 