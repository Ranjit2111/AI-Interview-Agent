# AI Interview Preparation System

An intelligent interview preparation platform that uses multiple specialized AI agents to simulate realistic job interviews and provide personalized feedback.

## Features

- **Multi-Agent Architecture**: Different specialized AI agents work together to provide a comprehensive interview experience
- **Realistic Interview Simulation**: Conducts interviews tailored to specific job roles and industries
- **Real-Time Feedback**: Provides immediate coaching and feedback on responses
- **Skill Assessment**: Identifies and evaluates technical skills mentioned in answers
- **Personalized Improvement**: Offers targeted advice and resources for improvement

## Agent System

The system uses multiple specialized agents that collaborate:

1. **Interviewer Agent**: Asks relevant questions based on job role and evaluates answers
2. **Coach Agent**: Provides feedback on interview performance and suggests improvements
3. **Skill Assessor Agent**: Identifies and evaluates technical skills mentioned in responses
4. **Orchestrator**: Coordinates all agents and manages the overall interview flow

## Technical Architecture

- **Backend**: FastAPI application with SQLite database using SQLAlchemy ORM
- **Agent System**: Specialized AI agents with event-based communication
- **LLM Integration**: Uses large language models to power agent functionality

## Getting Started

### Prerequisites

- Python 3.9+
- API key for OpenAI or Anthropic (Claude)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/ai-interview-agent.git
cd ai-interview-agent
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys
```
OPENAI_API_KEY=your_openai_api_key
# or
ANTHROPIC_API_KEY=your_anthropic_api_key
```

4. Initialize the database
```bash
python -c "from backend.database.connection import init_db; init_db()"
```

### Running the Application

Start the FastAPI server:
```bash
python main.py
```

The API will be available at http://localhost:8000

## API Endpoints

- `POST /api/interview/start`: Start a new interview session
- `POST /api/interview/message`: Send a message to the interview system
- `POST /api/interview/end`: End an interview session
- `GET /api/interview/sessions`: List active interview sessions
- `GET /api/interview/info`: Get information about a session
- `POST /api/interview/switch-agent`: Switch the active agent
- `POST /api/interview/switch-mode`: Change the orchestrator mode
- `POST /api/interview/reset`: Reset a session

## Future Improvements

- Voice interaction support
- Video interview capability with body language analysis
- Integration with job posting sites to automatically tailor interviews
- Expanded industry-specific question databases
- Extended memory across sessions for personalized improvement tracking

## License

This project is licensed under the MIT License - see the LICENSE file for details. 