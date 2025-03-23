# AI Interviewer Agent - Codebase Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Directory Structure](#directory-structure)
5. [Backend Components](#backend-components)
6. [Frontend Components](#frontend-components)
7. [Data Flow](#data-flow)
8. [Key Integration Points](#key-integration-points)
9. [Development Guidelines](#development-guidelines)
10. [Testing](#testing)
11. [Documentation References](#documentation-references)

## Introduction

This guide provides a comprehensive overview of the AI Interviewer Agent codebase, designed to help developers understand the system architecture, components, and their interactions. The document serves as a map for navigating the codebase and understanding how different parts work together.

## Project Overview

The AI Interviewer Agent is a sophisticated multi-agent system for AI-powered interview preparation and coaching. It features:

- AI-Driven Interview Simulations with adaptive questioning
- Personalized Coaching with detailed feedback
- Skill Assessment with identification of strengths and areas for improvement
- Web Search integration for resource recommendations
- Speech-to-Text and Text-to-Speech capabilities

The system is built using Python (FastAPI) for the backend and JavaScript/React (Next.js) for the frontend.

## System Architecture

The AI Interviewer Agent follows a multi-agent architecture with specialized components:

1. **Interviewer Agent**: Conducts interviews with adaptive questioning
2. **Coach Agent**: Provides feedback on interview responses
3. **Skill Assessor Agent**: Identifies skills, proficiency levels, and recommends resources
4. **Orchestrator**: Coordinates communication between agents and manages interview flow

The system uses an event-based communication pattern through an Event Bus to facilitate agent interactions.

## Directory Structure

```
project/
├── backend/                 # Python backend code
│   ├── agents/              # Agent implementation
│   │   ├── templates/       # Prompt templates for agents
│   │   ├── utils/           # Agent utilities
│   │   ├── base.py          # Base agent class
│   │   ├── coach.py         # Coach agent implementation
│   │   ├── interviewer.py   # Interviewer agent implementation
│   │   ├── orchestrator.py  # Orchestrator for agent coordination
│   │   └── skill_assessor.py # Skill assessment agent
│   ├── api/                 # API endpoints
│   │   ├── agent_api.py     # Agent-related API endpoints
│   │   ├── resource_api.py  # Resource-related API endpoints
│   │   └── speech_api.py    # Speech processing endpoints
│   ├── database/            # Database connections and models
│   ├── models/              # Data models
│   │   ├── interview.py     # Interview-related models
│   │   └── user.py          # User-related models
│   ├── schemas/             # Pydantic schemas for API
│   ├── services/            # Service layer
│   │   ├── data_management.py # Data management service
│   │   ├── search_service.py  # Web search service
│   │   └── session_manager.py # Session management service
│   ├── tests/               # Unit and integration tests
│   ├── utils/               # Utility functions
│   │   ├── docs_generator.py # Documentation generator
│   │   ├── event_bus.py      # Event bus for agent communication
│   │   └── vector_store.py   # Vector storage utilities
│   ├── main.py              # Application entry point
│   └── requirements.txt     # Backend dependencies
├── frontend/                # JavaScript/React frontend
│   ├── components/          # React components
│   │   ├── CameraView.js    # Camera component for video
│   │   ├── SkillCard.js     # Component for displaying skills
│   │   ├── SkillResources.js # Component for skill resources
│   │   ├── SpeechInput.js   # Speech input component
│   │   └── SpeechOutput.js  # Speech output component
│   ├── pages/               # Next.js pages
│   │   ├── index.js         # Homepage
│   │   └── skills.js        # Skills assessment page
│   ├── src/                 # Source code
│   │   └── api/             # API client code
│   ├── styles/              # CSS styles
│   │   ├── globals.css      # Global styles
│   │   ├── SkillCard.module.css     # Styles for SkillCard
│   │   ├── SkillResources.module.css # Styles for SkillResources
│   │   └── Skills.module.css # Styles for Skills page
│   ├── next.config.js       # Next.js configuration
│   ├── package.json         # Frontend dependencies
│   └── tailwind.config.js   # Tailwind CSS configuration
├── docs/                    # Documentation
│   ├── agents/              # Agent documentation
│   ├── api/                 # API documentation
│   ├── architecture/        # Architecture documentation
│   ├── dev/                 # Developer guides
│   ├── features/            # Feature documentation
│   └── sprint*/             # Sprint-specific documentation
├── project_plan.md          # Project development plan
├── README.md                # Project overview
└── requirements.txt         # Project dependencies
```

## Backend Components

### Agents

The agents are the core of the system, implementing specialized AI roles:

1. **BaseAgent** (`agents/base.py`)
   - Abstract base class for all agents
   - Implements common functionality and LLM interactions
   - Provides template management and tool integration

2. **InterviewerAgent** (`agents/interviewer.py`)
   - Conducts interview sessions
   - Implements adaptive questioning based on user responses
   - Supports different interview styles

3. **CoachAgent** (`agents/coach.py`)
   - Provides feedback on interview responses
   - Uses frameworks like STAR for structured feedback
   - Offers improvement suggestions

4. **SkillAssessorAgent** (`agents/skill_assessor.py`)
   - Evaluates technical and soft skills
   - Determines proficiency levels
   - Recommends learning resources

5. **OrchestratorAgent** (`agents/orchestrator.py`)
   - Coordinates other agents
   - Manages interview flow
   - Handles state transitions

### API Endpoints

1. **Agent API** (`api/agent_api.py`)
   - Endpoints for agent interactions
   - Interview session management
   - Response processing

2. **Resource API** (`api/resource_api.py`)
   - Endpoints for resource recommendations
   - Resource feedback collection
   - Resource effectiveness tracking

3. **Speech API** (`api/speech_api.py`)
   - Speech-to-text processing
   - Text-to-speech generation
   - Voice selection

### Services

1. **SearchService** (`services/search_service.py`)
   - Web search integration (Serper.dev/SerpAPI)
   - Resource classification and ranking
   - Search query optimization

2. **SessionManager** (`services/session_manager.py`)
   - Manages interview sessions
   - Handles session state
   - Provides context management

3. **DataManagement** (`services/data_management.py`)
   - Data persistence
   - Query interface
   - Transaction management

### Utilities

1. **EventBus** (`utils/event_bus.py`)
   - Event-based communication system
   - Event publishing and subscription
   - Agent coordination

2. **VectorStore** (`utils/vector_store.py`)
   - FAISS integration for vector storage
   - Embedding generation
   - Similarity search

## Frontend Components

### Pages

1. **Home Page** (`pages/index.js`)
   - Entry point for the application
   - Interview session interface
   - Speech interaction controls

2. **Skills Page** (`pages/skills.js`)
   - Skill assessment display
   - Resource recommendations
   - Progress tracking

### Components

1. **SpeechInput/Output** (`components/SpeechInput.js`, `components/SpeechOutput.js`)
   - Speech-to-text and text-to-speech interfaces
   - Voice selection
   - Audio controls

2. **SkillCard** (`components/SkillCard.js`)
   - Displays individual skills
   - Shows proficiency levels
   - Provides resource links

3. **SkillResources** (`components/SkillResources.js`)
   - Displays recommended resources
   - Categorizes by resource type
   - Implements filtering and sorting

### API Client

1. **Agent API Client** (`src/api/agentApi.js`)
   - Handles API requests to backend
   - Manages authentication
   - Error handling

## Data Flow

1. **Interview Session Flow**
   - User initiates an interview session through the frontend
   - Frontend sends request to Agent API
   - Orchestrator coordinates the interview flow
   - Interviewer Agent generates questions
   - User responses are processed by Coach Agent for feedback
   - Skill Assessor evaluates skills and recommends resources
   - Results are returned to the frontend for display

2. **Resource Recommendation Flow**
   - Skill Assessor identifies skill gaps
   - SearchService generates queries based on skills
   - Web search APIs provide results
   - Results are processed, classified, and ranked
   - Resources are displayed in the SkillResources component
   - User feedback is collected for future improvement

## Key Integration Points

1. **LLM Integration**
   - Google Gemini API (primarily gemma-3 model)
   - Prompt template system for structured inputs
   - Response parsing and extraction

2. **Speech Processing**
   - Browser Web Speech API for speech-to-text
   - Kokoro TTS for text-to-speech
   - Real-time audio streaming

3. **Web Search**
   - Dual provider support (Serper.dev and SerpAPI)
   - Provider-specific API clients
   - Result normalization and processing

## Development Guidelines

1. **Agent Development**
   - Extend BaseAgent for new agent types
   - Implement required abstract methods
   - Create templates in agents/templates directory
   - Register in agents/__init__.py

2. **API Extension**
   - Follow RESTful design principles
   - Use Pydantic schemas for validation
   - Include proper error handling
   - Add documentation with docstrings

3. **Frontend Development**
   - Use React functional components with hooks
   - Follow component-based architecture
   - Implement responsive design
   - Use Tailwind CSS for styling

## Testing

1. **Unit Tests** (`tests/`)
   - Agent testing (test_coach.py, test_interviewer.py, etc.)
   - Service testing (test_search_service.py)
   - Utility testing

2. **Integration Tests** (`tests/test_integration.py`)
   - End-to-end flows
   - API endpoint testing
   - Agent coordination testing

3. **Performance Tests** (`tests/test_performance.py`)
   - Response time testing
   - Load testing
   - Resource utilization testing

## Documentation References

- [Agent Architecture](docs/agent_architecture.md) - Details on agent design
- [API Contracts](docs/api/api_contracts.md) - API specifications
- [Template System](docs/template_system.md) - Prompt template documentation
- [Web Search Integration](docs/web_search_integration.md) - Web search implementation
- [Performance Optimization](docs/performance_optimization.md) - Optimization strategies 