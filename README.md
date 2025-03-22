# AI Interviewer Agent

A sophisticated multi-agent system for AI-powered interview preparation and coaching.

## Overview

This project provides a comprehensive interview preparation system using AI agents that work together to create a realistic interview experience, provide coaching, and assess skills. The system leverages modern LLM capabilities through the LangChain framework and Google Gemini models.

## Key Features

- **AI-Driven Interview Simulations**: Realistic interview experiences with adaptive questioning
- **Personalized Coaching**: Detailed feedback on interview responses using frameworks like STAR
- **Skill Assessment**: Identification of strengths and areas for improvement
- **Flexible Architecture**: Modular design with extensible agent system
- **Comprehensive Documentation**: Detailed guides for usage and development

## System Architecture

The system is built around a multi-agent architecture:

1. **Interviewer Agent**: Conducts interviews with state-based flows
2. **Coach Agent**: Provides feedback and guidance using structured frameworks
3. **Skill Assessor Agent**: Identifies skill gaps and recommends resources

These agents communicate through an event-based system, enabling real-time collaboration during interview sessions.

For more details, see the [System Architecture Documentation](docs/architecture/system_architecture.md).

## Getting Started

### Prerequisites

- Python 3.9+
- Google Gemini API key
- 8GB+ RAM recommended

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-interviewer-agent.git
   cd ai-interviewer-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

### Running the Application

Start the backend server:
```bash
cd backend
python main.py
```

Start the frontend (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Access the application at http://localhost:3000

## Documentation

- [System Architecture](docs/architecture/system_architecture.md)
- [Agent Architecture](docs/architecture/agent_architecture.md)
- [Template System](docs/architecture/template_system.md)
- [LLM Utilities](docs/dev/llm_utils.md)
- [Interviewer Agent Reference](docs/agents/interviewer_agent_reference.md)
- [Coach Agent Reference](docs/agents/coach_agent_reference.md)
- [API Contracts](docs/api/api_contracts.md)

## Development

### Project Structure

```
project/
├── backend/
│   ├── agents/
│   │   ├── templates/
│   │   │   ├── coach_templates.py
│   │   │   ├── interviewer_templates.py
│   │   │   └── skill_templates.py
│   │   ├── utils/
│   │   │   └── llm_utils.py
│   │   ├── base.py
│   │   ├── coach.py
│   │   ├── interviewer.py
│   │   └── skill_assessor.py
│   ├── models/
│   ├── utils/
│   │   └── event_bus.py
│   └── main.py
├── frontend/
├── docs/
│   ├── architecture/
│   │   ├── system_architecture.md
│   │   ├── agent_architecture.md
│   │   └── template_system.md
│   ├── agents/
│   │   ├── interviewer_agent_reference.md
│   │   └── coach_agent_reference.md
│   ├── dev/
│   │   └── llm_utils.md
│   └── api/
│       ├── api_contracts.md
│       └── api_docs/ (generated)
└── README.md
```

### Adding New Agents

1. Create a new agent class that inherits from `BaseAgent`
2. Implement required methods: `_get_system_prompt()`, `_initialize_tools()`, etc.
3. Create template file in `agents/templates/`
4. Update `agents/__init__.py` to export the new agent

### Extending Templates

1. Add new templates to the appropriate template file
2. Update the `__init__.py` import list
3. Add the template name to the `__all__` list

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the powerful LLM framework
- [Google Gemini](https://ai.google.dev/) for the underlying AI models
- All contributors who have helped shape this project 