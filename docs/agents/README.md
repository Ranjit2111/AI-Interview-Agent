# Agent Documentation

This directory contains detailed documentation for each agent in the AI Interviewer system.

## Contents

- [Base Agent Reference](base_agent_reference.md): Foundation reference for the BaseAgent class that all agents inherit from, including core functionality, methods, and extension patterns.
- [Interviewer Agent Reference](interviewer_agent_reference.md): Comprehensive reference for the Interviewer Agent, including responsibilities, methods, workflows, and modification guidelines.
- [Coach Agent Reference](coach_agent_reference.md): Detailed reference for the Coach Agent, including responsibilities, methods, workflows, and modification guidelines.
- [Skill Assessor Agent Reference](skill_assessor_agent_reference.md): Complete reference for the Skill Assessor Agent, including skill identification, proficiency assessment, and resource suggestion functionalities.
- [Orchestrator Agent Reference](orchestrator_agent_reference.md): Reference guide for the Agent Orchestrator, which coordinates all agents and manages agent modes, command handling, and multi-agent responses.

## Agent Documentation Guidelines

When documenting an agent:

1. Provide a clear overview of the agent's purpose and responsibilities
2. Document the file structure and key components
3. Explain the main methods and their roles
4. Describe data flow and dependencies
5. Include guidance for common modifications
6. List best practices specific to the agent
7. Document known issues and their solutions

## Adding New Agent Documentation

When adding documentation for a new agent:

1. Use the existing agent documentation as a template
2. Create a new markdown file with the naming convention `{agent_name}_agent_reference.md`
3. Add a link to the new file in this README
4. Add a link to the new file in the main [documentation index](../index.md) 