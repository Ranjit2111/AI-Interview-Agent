# AI Interviewer Agent - File Index

This document provides a quick reference guide to all key files in the AI Interviewer Agent project, organized by component type.

## Backend Files

### Core Files

- `backend/main.py` - Main application entry point
- `backend/__init__.py` - Backend package initialization
- `backend/setup_kokoro_tts.py` - TTS setup and configuration

### Agent Files

- `backend/agents/base.py` - Base agent class implementation
- `backend/agents/interviewer.py` - Interviewer agent implementation
- `backend/agents/coach.py` - Coach agent implementation
- `backend/agents/skill_assessor.py` - Skill assessor agent implementation
- `backend/agents/orchestrator.py` - Orchestrator for agent coordination

#### Agent Templates

- `backend/agents/templates/coach_templates.py` - Prompt templates for coach agent
- `backend/agents/templates/interviewer_templates.py` - Prompt templates for interviewer agent
- `backend/agents/templates/skill_assessor_templates.py` - Prompt templates for skill assessor

#### Agent Utilities

- `backend/agents/utils/llm_utils.py` - Utilities for LLM interaction
- `backend/agents/utils/prompt_utils.py` - Utilities for prompt management
- `backend/agents/utils/template_utils.py` - Utilities for template processing

### API Endpoints

- `backend/api/agent_api.py` - API endpoints for agent interaction
- `backend/api/resource_api.py` - API endpoints for resource management
- `backend/api/speech_api.py` - API endpoints for speech processing

### Database

- `backend/database/connection.py` - Database connection management
- `backend/database/models.py` - Database model definitions
- `backend/database/repositories.py` - Data access repositories

### Models

- `backend/models/interview.py` - Interview data models
- `backend/models/resource.py` - Resource data models
- `backend/models/user.py` - User data models
- `backend/models/session.py` - Session data models

### Schemas

- `backend/schemas/base.py` - Base schema definitions
- `backend/schemas/interview.py` - Interview schema definitions
- `backend/schemas/resource.py` - Resource schema definitions
- `backend/schemas/user.py` - User schema definitions

### Services

- `backend/services/data_management.py` - Data management services
- `backend/services/event_bus.py` - Event bus implementation
- `backend/services/search_service.py` - Web search service
- `backend/services/session_manager.py` - Session management service
- `backend/services/speech_service.py` - Speech processing service

### Utilities

- `backend/utils/config.py` - Configuration utilities
- `backend/utils/logging.py` - Logging utilities
- `backend/utils/validators.py` - Input validation utilities
- `backend/utils/web_search.py` - Web search utilities

### Tests

- `backend/tests/test_coach.py` - Tests for coach agent
- `backend/tests/test_interviewer.py` - Tests for interviewer agent
- `backend/tests/test_skill_assessor.py` - Tests for skill assessor agent
- `backend/tests/test_api.py` - Tests for API endpoints
- `backend/tests/test_services.py` - Tests for services

## Frontend Files

### Core Files

- `frontend/next.config.js` - Next.js configuration
- `frontend/tailwind.config.js` - Tailwind CSS configuration
- `frontend/postcss.config.js` - PostCSS configuration

### Pages

- `frontend/pages/index.js` - Home page
- `frontend/pages/_app.js` - App wrapper
- `frontend/pages/interview.js` - Interview page
- `frontend/pages/resources.js` - Resources page
- `frontend/pages/skills.js` - Skills page

### Components

- `frontend/components/CameraView.js` - Camera view component
- `frontend/components/InterviewSession.js` - Interview session component
- `frontend/components/ResourceList.js` - Resource list component
- `frontend/components/SkillDisplay.js` - Skill display component
- `frontend/components/SpeechInput.js` - Speech input component
- `frontend/components/SpeechOutput.js` - Speech output component
- `frontend/components/Transcript.js` - Transcript display component

### Styles

- `frontend/styles/globals.css` - Global styles

### API Client

- `frontend/api/client.js` - API client for backend communication

## Documentation Files

### Project Documentation

- `README.md` - Main project README
- `project_plan.md` - Project planning document
- `codebase_guide.md` - Comprehensive codebase guide
- `component_relationships.md` - Component relationship guide

### Agent Documentation

- `docs/agents/base_agent_reference.md` - Base agent reference
- `docs/agents/interviewer_agent.md` - Interviewer agent documentation
- `docs/agents/coach_agent.md` - Coach agent documentation
- `docs/agents/skill_assessor_agent.md` - Skill assessor documentation
- `docs/agents/orchestrator.md` - Orchestrator documentation

### API Documentation

- `docs/api/api_contracts.md` - API contract documentation
- `docs/api/resource_api.md` - Resource API documentation
- `docs/api/agent_api.md` - Agent API documentation
- `docs/api/speech_api.md` - Speech API documentation

### Integration Documentation

- `docs/integrations/web_search.md` - Web search integration
- `docs/integrations/speech_processing.md` - Speech processing integration
- `docs/integrations/llm_integration.md` - LLM integration

### Development Documentation

- `docs/development/setup.md` - Development setup guide
- `docs/development/testing.md` - Testing guide
- `docs/development/deployment.md` - Deployment guide
