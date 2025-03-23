# Agent Architecture Reference Guide

## Overview

The AI Interviewer Agent system implements a multi-agent architecture where specialized agents collaborate to provide a comprehensive interview preparation experience. Each agent focuses on a specific aspect of the interview process, allowing for modular development and clear separation of concerns.

## Agent Types

### 1. Interviewer Agent

**Primary Responsibility:** Conducts the interview session by asking questions, evaluating answers, and managing the interview flow.

**Key Features:**
- Implements a state machine to manage interview flow (introduction → questioning → evaluation → summary)
- Generates tailored questions based on job role and requirements
- Evaluates answers using structured templates and rubrics
- Produces comprehensive interview summaries with recommendations

**Files:**
- `backend/agents/interviewer.py`: Main implementation
- `backend/agents/templates/interviewer_templates.py`: Prompt templates
- `backend/docs/interviewer_agent_reference.md`: Reference documentation

### 2. Coach Agent

**Primary Responsibility:** Provides constructive feedback, guidance, and improvement suggestions.

**Key Features:**
- Evaluates responses using the STAR method framework
- Assesses communication skills and response completeness
- Provides personalized feedback based on experience level
- Generates practice questions with structured guidance

**Files:**
- `backend/agents/coach.py`: Main implementation
- `backend/agents/templates/coach_templates.py`: Prompt templates
- `backend/docs/coach_agent_reference.md`: Reference documentation

### 3. Skill Assessor Agent

**Primary Responsibility:** Identifies skill gaps and strengths based on interview performance.

**Key Features:**
- Maps responses to specific technical and soft skills
- Tracks skill demonstration across the interview
- Recommends learning resources for skill development
- Provides proficiency-level assessments

**Files:**
- `backend/agents/skill_assessor.py`: Main implementation
- `backend/agents/templates/skill_templates.py`: Prompt templates

## Agent Communication

Agents communicate with each other through an event-based system:

1. **Event Bus:** Central communication channel that enables publish/subscribe pattern
2. **Events:** Structured messages with standardized formats
3. **Event Handlers:** Agent methods that process specific event types

Example event types:
- `interview_started`: Signals the beginning of an interview session
- `question_asked`: Contains information about a question posed to the candidate
- `answer_received`: Includes the candidate's response for evaluation
- `coach_feedback`: Contains coaching advice on a response
- `interview_summary`: Provides the final interview assessment

## Code Organization

### Core Components

1. **Base Agent Class:**
   - Defined in `backend/agents/base.py`
   - Provides common functionality for all agents
   - Implements event handling infrastructure
   - Defines interface methods that all agents must implement

2. **Templates:**
   - Centralized in `backend/agents/templates/`
   - Separated by agent type (interviewer, coach, skill)
   - Standardized format with documented placeholders
   - Supports both production and development imports

3. **Utilities:**
   - Common functions in `backend/agents/utils/`
   - Error handling for LLM operations
   - JSON parsing with fallbacks
   - Scoring and evaluation helpers

### Modular Structure

The codebase follows these design principles:

1. **Separation of Concerns:**
   - Each agent handles a specific aspect of the interview process
   - Clear boundaries between different functionalities
   - Independent development and testing possible

2. **Template Externalization:**
   - All prompt engineering is separated from business logic
   - Templates are versioned and maintained in dedicated files
   - Changes to prompts don't require modifying agent code

3. **Flexible Import Structure:**
   - Support for both production and development environments
   - Try/except patterns for handling different import scenarios
   - Consistent approach across all modules

4. **Error Handling:**
   - Robust error management with fallback mechanisms
   - Default creators for when LLM responses fail
   - Consistent approach for JSON parsing and validation

## Agent Orchestration

The `AgentOrchestrator` class coordinates the multi-agent system:

1. **Mode Management:**
   - Determines which agents are active based on the current mode
   - Modes include: interview_only, coaching_only, full_feedback, etc.

2. **Response Composition:**
   - Combines outputs from multiple agents into cohesive responses
   - Formats agent responses with appropriate prefixes and styling
   - Ensures consistent user experience regardless of active agents

3. **Context Sharing:**
   - Maintains shared context accessible to all agents
   - Synchronizes state across the agent system
   - Provides history and memory for long-running sessions

## Best Practices for Agent Development

1. **Template Management:**
   - Keep templates in dedicated files
   - Document all placeholders
   - Use descriptive template names

2. **Error Handling:**
   - Always use `invoke_chain_with_error_handling` when calling LLM chains
   - Provide default creators for fallback responses
   - Handle exceptions gracefully

3. **Event Communication:**
   - Use standardized event types
   - Include all necessary context in event data
   - Subscribe only to relevant events

4. **Testing:**
   - Create unit tests for individual agent methods
   - Test template rendering with various inputs
   - Simulate events for testing handler methods

5. **Documentation:**
   - Maintain reference guides for each agent
   - Document event types and data structures
   - Update documentation when adding new features

## Future Enhancements

1. **Agent Specialization:**
   - More specialized coaching agents for different domains
   - Industry-specific interviewer agents
   - Role-specific skill assessors

2. **Improved Template Management:**
   - Version control for templates
   - A/B testing of different prompt strategies
   - Template performance metrics

3. **Enhanced Orchestration:**
   - Dynamic agent activation based on context
   - More sophisticated response composition
   - Multi-turn planning across agents 