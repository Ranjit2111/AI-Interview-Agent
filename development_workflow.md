# AI Interviewer Agent - Development Workflow Guide

This guide outlines the development workflow for the AI Interviewer Agent project, providing step-by-step instructions for common development tasks.

## Table of Contents
- [Setting Up Development Environment](#setting-up-development-environment)
- [Code Structure and Organization](#code-structure-and-organization)
- [Development Workflow](#development-workflow)
- [Testing Procedures](#testing-procedures)
- [Deployment Process](#deployment-process)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Setting Up Development Environment

### Prerequisites
- Python 3.10+ for backend development
- Node.js 16+ for frontend development
- Docker for containerized components
- Git for version control

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone [repository-url]
   cd AI-Interviewer-Agent
   ```

2. **Create and activate Python virtual environment**:
   ```bash
   cd backend
   python -m venv .venv
   # On Windows
   .\.venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy the `.env.example` file to `.env`
   - Update values as needed for your environment

5. **Setup Kokoro TTS (if needed)**:
   ```bash
   python setup_kokoro_tts.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

## Code Structure and Organization

The project follows a modular structure:

### Backend Structure

- **Agents**: Core intelligent agents 
  - Each agent has its own module
  - Base agent defines shared functionality
  - Templates contain prompt templates

- **API**: FastAPI endpoints
  - Organized by domain area (agent, resources, speech)
  - Uses Pydantic schemas for validation

- **Services**: Business logic layer
  - Isolates external integrations
  - Provides functionality to agents and APIs

- **Models/Schemas**: Data representations
  - Models represent database structures
  - Schemas define API contracts

### Frontend Structure

- **Pages**: Next.js page components
  - Each page corresponds to a route
  - Uses components for UI elements

- **Components**: Reusable UI elements
  - Organized by functionality
  - Uses React hooks for state management

- **API Client**: Backend communication
  - Handles fetch requests
  - Manages WebSocket connections

## Development Workflow

### Creating a New Feature

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/feature-name
   ```

2. **For backend features**:
   - Implement the feature in relevant modules
   - Add appropriate tests
   - Update API documentation

3. **For frontend features**:
   - Implement the UI component or page
   - Add styling using Tailwind CSS
   - Connect to backend API if needed

4. **Run tests to verify implementation**

5. **Submit a pull request for review**

### Working with Agents

1. **Understanding the agent architecture**:
   - Each agent inherits from the `BaseAgent` class
   - Agents process requests through their main methods
   - Templates control agent behavior and output

2. **Modifying agent behavior**:
   - Start by editing prompt templates in `agents/templates/`
   - Update processing logic in the agent class
   - Test with sample inputs

3. **Agent integration**:
   - Agents communicate through the orchestrator
   - Use the event bus for asynchronous communication

### API Development

1. **Creating a new endpoint**:
   - Add the endpoint function to the appropriate API module
   - Define request and response schemas
   - Add validation and error handling

2. **Testing endpoints**:
   ```bash
   # Start the backend server
   cd backend
   python -m main
   ```

3. **Access Swagger documentation**:
   - Open `http://localhost:8000/docs` in your browser
   - Test endpoints directly through the Swagger UI

### Frontend Development

1. **Start the development server**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Access the application**:
   - Open `http://localhost:3000` in your browser

3. **Component development workflow**:
   - Create or modify components in `components/` directory
   - Import and use in page components
   - Use hot-reloading to see changes in real-time

## Testing Procedures

### Backend Testing

1. **Run unit tests**:
   ```bash
   cd backend
   pytest tests/
   ```

2. **Run specific test categories**:
   ```bash
   # Test agents
   pytest tests/test_agents.py
   
   # Test APIs
   pytest tests/test_api.py
   ```

3. **Run with coverage report**:
   ```bash
   pytest --cov=backend tests/
   ```

### Frontend Testing

1. **Run Jest tests**:
   ```bash
   cd frontend
   npm test
   ```

2. **Component testing**:
   ```bash
   npm test -- -t "ComponentName"
   ```

## Deployment Process

### Local Deployment

1. **Build the frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Run both services**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m main
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

### Docker Deployment

1. **Build Docker images**:
   ```bash
   docker-compose build
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## Troubleshooting Common Issues

### Backend Issues

1. **Missing dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Database connection errors**:
   - Check `.env` configuration
   - Verify database service is running

3. **LLM-related errors**:
   - Verify API keys in environment variables
   - Check model availability
   - Check for rate limiting issues

### Frontend Issues

1. **Node module errors**:
   ```bash
   rm -rf node_modules
   npm install
   ```

2. **API connection issues**:
   - Verify backend is running
   - Check API URL configuration in `.env.local`

3. **Build errors**:
   - Check for TypeScript errors
   - Verify import paths
   - Check for missing dependencies

### Speech Processing Issues

1. **Kokoro TTS issues**:
   - Run `python setup_kokoro_tts.py` again
   - Check Docker container status
   
2. **WebRTC connection issues**:
   - Use Chrome for best compatibility
   - Grant microphone permissions
   - Check for network conflicts 