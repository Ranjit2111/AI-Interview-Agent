# AI Interviewer Agent Documentation

Welcome to the AI Interviewer Agent documentation. This comprehensive guide provides information about the system architecture, components, and how to use and extend the application.

## Table of Contents

### System Architecture
- [System Architecture Overview](architecture/system_architecture.md)
- [Agent Architecture](architecture/agent_architecture.md)
- [Template System](architecture/template_system.md)

### Agent Documentation
- [Base Agent Reference](agents/base_agent_reference.md)
- [Interviewer Agent Reference](agents/interviewer_agent_reference.md)
- [Coach Agent Reference](agents/coach_agent_reference.md)
- [Skill Assessor Agent Reference](agents/skill_assessor_agent_reference.md)
- [Orchestrator Agent Reference](agents/orchestrator_agent_reference.md)

### Developer Guides
- [LLM Utilities](dev/llm_utils.md)

### API Documentation
- [API Contracts](api/api_contracts.md)
- [API Reference](api/api_docs/index.html) (generated)

## Project Overview

The AI Interviewer Agent is a sophisticated multi-agent system for AI-powered interview preparation and coaching. The system leverages modern LLM capabilities through the LangChain framework and Google Gemini models to provide:

- **Realistic Interview Simulations**: Conduct lifelike interview scenarios with adaptive questioning
- **Personalized Coaching**: Receive detailed feedback on interview responses using frameworks like STAR
- **Skill Assessment**: Identify strengths and areas for improvement in your responses
- **Comprehensive Documentation**: Access detailed guides for both users and developers

### Multi-Agent Architecture

The system is built around a multi-agent architecture where specialized agents collaborate:

1. **Interviewer Agent**: Conducts interviews with state-based flows
2. **Coach Agent**: Provides feedback and guidance using structured frameworks
3. **Skill Assessor Agent**: Identifies skill gaps and recommends resources

These agents communicate through an event-based system, enabling real-time collaboration during interview sessions.

## Getting Started

For setup instructions and prerequisites, please refer to the [main README](../README.md).

## Contributing

Contributions to the documentation are welcome. Please follow these guidelines:

1. Place system-level documentation in the `architecture` directory
2. Place agent-specific documentation in the `agents` directory
3. Place developer guides in the `dev` directory
4. Place API documentation in the `api` directory
5. Use markdown format with proper headings and links
6. Include code examples where appropriate
7. Update this index file when adding new documentation 