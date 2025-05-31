# AI Interviewer Agent

A sophisticated multi-agent system for AI-powered interview preparation and coaching with real-time speech processing, database persistence, and authentication.

## 🏗️ System Architecture

### Technology Stack

**Backend (Python/FastAPI)**
- **Framework**: FastAPI with uvicorn for high-performance async API
- **Database**: Supabase (PostgreSQL) with Row Level Security (RLS)
- **Authentication**: JWT-based auth with Supabase integration
- **AI/LLM**: LangChain + Google Gemini for intelligent agents
- **Speech Processing**: Deepgram for STT, built-in TTS
- **File Processing**: PyMuPDF, python-docx for document parsing
- **Search**: Serper API for web search capabilities

**Frontend (React/TypeScript)**
- **Framework**: React 18 + TypeScript with Vite build system
- **UI Components**: Radix UI + ShadCN/UI component library
- **Styling**: Tailwind CSS with animations
- **State Management**: React Query for server state, Context API for auth
- **Routing**: React Router DOM
- **Forms**: React Hook Form with Zod validation

### Project Structure

```
AI Interviewer Agent/
├── backend/                         # Python FastAPI backend
│   ├── agents/                      # AI agent system
│   │   ├── base.py                  # Base agent class with event system
│   │   ├── config_models.py         # Pydantic models for agent config
│   │   ├── interviewer.py           # Interview conductor agent
│   │   ├── coach.py                 # Coaching and feedback agent
│   │   ├── interview_state.py       # Interview State Management for Interview Agent
│   │   └── orchestrator.py          # Multi-agent orchestration
│   │
│   ├── api/                         # FastAPI route handlers
│   │   ├── auth_api.py              # Authentication endpoints
│   │   ├── agent_api.py             # Interview session endpoints
│   │   ├── speech_api.py            # Speech processing endpoints
│   │   └── file_processing_api.py   # File upload/processing
│   │
│   ├── api/speech/                  # Speech processing modules
│   │   ├── connection_manager.py    # WebSocket connection management
│   │   ├── deepgram_handlers.py     # Deepgram event handling
│   │   ├── websocket_processor.py   # WebSocket message processing
│   │   ├── tts_service.py           # Text-to-Speech service
│   │   └── stt_service.py           # Speech-to-Text service
│   │
│   ├── config/                      # Configuration files
│   │   └── file_processing_config.py # File processing settings
│   │
│   ├── database/                    # Database management
│   │   ├── db_manager.py            # Supabase database manager
│   │   ├── mock_db_manager.py       # Mock database for development
│   │   └── schema.sql               # Database schema definitions
│   │
│   ├── services/                    # Business logic services
│   │   ├── session_manager.py       # Interview session management
│   │   ├── llm_service.py           # LLM integration service
│   │   ├── rate_limiting.py         # API rate limiting
│   │   ├── search_service.py        # Web search integration
│   │   ├── search_helpers.py        # Search utility functions
│   │   └── search_config.py         # Search configuration
│   │
│   ├── utils/                       # Utility functions
│   │   ├── auth_utils.py            # JWT authentication utilities
│   │   ├── security.py              # Security and validation utilities
│   │   └── file_utils.py            # File processing utilities
│   │
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Application configuration
│   └── requirements.txt             # Python dependencies
│
├── frontend/                        # React TypeScript frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   │   ├── ui/                  # Reusable UI components (ShadCN)
│   │   │   ├── AuthModal.tsx        # Authentication modal
│   │   │   ├── LoginForm.tsx        # Login form component
│   │   │   ├── RegisterForm.tsx     # Registration form component
│   │   │   ├── InterviewSession.tsx # Main interview interface
│   │   │   ├── InterviewConfig.tsx  # Interview configuration
│   │   │   ├── ChatInterface.tsx    # Chat UI component
│   │   │   ├── SpeechControls.tsx   # Speech control buttons
│   │   │   ├── SessionList.tsx      # Interview session history
│   │   │   └── FileUpload.tsx       # File upload component
│   │   │
│   │   ├── contexts/                # React contexts
│   │   │   └── AuthContext.tsx      # Authentication state management
│   │   │
│   │   ├── hooks/                   # Custom React hooks
│   │   │   └── useInterviewSession.ts # Session state management
│   │   │
│   │   ├── services/                # API and external services
│   │   │   └── api.ts               # API client functions
│   │   │
│   │   ├── types/                   # TypeScript type definitions
│   │   │   └── index.ts             # Shared type definitions
│   │   │
│   │   ├── App.tsx                  # Main app component
│   │   └── main.tsx                 # Application entry point
│   │
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.ts              # Vite build configuration
│   ├── tailwind.config.ts          # Tailwind CSS configuration
│   └── tsconfig.json               # TypeScript configuration
│
├── docs/                           # Documentation
├── run_venv.bat                    # Windows setup script
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore patterns
└── README.md                       # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** with npm
- **Supabase account** (for production database)
- **Google AI Studio API key** (for Gemini models)
- **Deepgram API key** (for speech processing)

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "AI Interviewer Agent"
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables** (`.env`):
   ```env
   # Supabase Configuration (Production)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-key
   SUPABASE_JWT_SECRET=your-jwt-secret
   
   # Development Mode (Alternative)
   USE_MOCK_AUTH=true
   JWT_SECRET=development_secret_key_not_for_production
   
   # AI/LLM Configuration
   GOOGLE_API_KEY=your-gemini-api-key
   
   # Speech Processing
   DEEPGRAM_API_KEY=your-deepgram-key
   
   # Search Integration
   SERPER_API_KEY=your-serper-key
   
   # Application Settings
   LOG_LEVEL=INFO
   PYTHONPATH=.
   ```

### Quick Setup (Windows)

Run the automated setup script:
```bash
run_venv.bat
```

This script will:
- Create Python virtual environment
- Install backend dependencies
- Install frontend dependencies
- Start both backend and frontend servers

### Manual Setup

**Backend Setup**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cd ..
```

**Frontend Setup**:
```bash
cd frontend
npm install
cd ..
```

**Start Development Servers**:

Backend (Terminal 1):
```bash
cd backend
venv\Scripts\activate
set PYTHONPATH=%CD%\..
uvicorn main:app --reload --port 8000
```

Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 Core Features

### 1. Multi-Agent Interview System

**Interviewer Agent** (`backend/agents/interviewer_agent.py`):
- Conducts realistic interviews with adaptive questioning
- Maintains conversation context and flow
- Supports multiple interview types (technical, behavioral, etc.)

**Coach Agent** (`backend/agents/coach_agent.py`):
- Provides real-time feedback using STAR method
- Analyzes response quality and structure
- Offers improvement suggestions

**Skill Assessor Agent** (`backend/agents/skill_assessor.py`):
- Evaluates technical and soft skills
- Identifies knowledge gaps
- Recommends learning resources

**Agent Coordinator** (`backend/agents/agent_coordinator.py`):
- Orchestrates multi-agent interactions
- Manages event-driven communication
- Ensures coherent interview experience

### 2. Speech Processing

**Text-to-Speech (TTS)**:
- Built-in TTS for interview questions
- Real-time audio generation
- Support for streaming and non-streaming modes

**Speech-to-Text (STT)**:
- Deepgram integration for accurate transcription
- Real-time WebSocket streaming
- Audio preprocessing and enhancement

### 3. Authentication & Database

**Authentication System**:
- JWT-based authentication with Supabase
- Secure user registration and login
- Token refresh and session management
- Row Level Security (RLS) for data isolation

**Database Features**:
- PostgreSQL with Supabase hosting
- Interview session persistence
- User profile and progress tracking
- File upload and document processing

### 4. File Processing

**Supported Formats**:
- PDF documents (PyMuPDF)
- Word documents (python-docx)
- Plain text files

**Processing Features**:
- Resume parsing and analysis
- Job description extraction
- Content validation and security
- File size and type restrictions

## 🔧 API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/refresh` | Refresh JWT token | No |
| GET | `/auth/me` | Get user profile | Yes |
| POST | `/auth/logout` | User logout | Yes |

### Interview Sessions (`/sessions`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/sessions/` | Create new session | Yes |
| GET | `/sessions/` | List user sessions | Yes |
| GET | `/sessions/{session_id}` | Get session details | Yes |
| POST | `/sessions/{session_id}/message` | Send message to session | Yes |
| DELETE | `/sessions/{session_id}` | Delete session | Yes |

### Speech Processing (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/text-to-speech` | Convert text to speech | Yes |
| POST | `/api/text-to-speech/stream` | Streaming TTS | Yes |
| POST | `/api/speech-to-text` | Convert speech to text | Yes |
| WebSocket | `/api/speech-to-text/stream` | Real-time STT | Yes |

### File Processing (`/files`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/files/upload` | Upload and process file | Yes |
| GET | `/files/{file_id}` | Get processed file data | Yes |
| DELETE | `/files/{file_id}` | Delete uploaded file | Yes |

## 🧪 Development Workflow

### Running Tests

**Backend Tests**:
```bash
cd backend
python -m pytest tests/ -v
```

**Frontend Tests**:
```bash
cd frontend
npm test
```

### Code Quality

**Backend Linting**:
```bash
cd backend
python -m flake8 .
python -m black .
```

**Frontend Linting**:
```bash
cd frontend
npm run lint
```

### Database Management

**Development Database**:
- Set `USE_MOCK_AUTH=true` for in-memory database
- No external dependencies required
- Automatic data reset between sessions

**Production Database**:
- Supabase PostgreSQL instance
- Automatic migrations and schema management
- Row Level Security for data isolation

### Adding New Features

1. **Backend API Endpoint**:
   - Add route handler in appropriate `api/` file
   - Update service layer in `services/`
   - Add database operations in `database/`
   - Write tests in `tests/`

2. **Frontend Component**:
   - Create component in `components/`
   - Add types in `types/`
   - Update API client in `services/api.ts`
   - Add routing if needed

3. **Agent Enhancement**:
   - Modify agent in `agents/`
   - Update agent coordination logic
   - Test multi-agent interactions

## 🔐 Security Features

### Authentication Security
- JWT tokens with secure signing
- Token expiration and refresh
- Password hashing with bcrypt
- CORS protection

### Data Security
- Row Level Security (RLS) in database
- Input validation and sanitization
- File upload restrictions
- Rate limiting on API endpoints

### Development Security
- Environment variable management
- Mock authentication for development
- Secure defaults in configuration

## 📊 Monitoring & Logging

### Application Logging
- Structured logging with timestamps
- Configurable log levels
- Request/response logging
- Error tracking and debugging

### Performance Monitoring
- Response time tracking
- WebSocket connection monitoring
- Speech processing metrics
- Database query performance

## 🚢 Deployment

### Environment Configuration

**Production Environment Variables**:
```env
# Required for production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-production-service-key
SUPABASE_JWT_SECRET=your-production-jwt-secret
GOOGLE_API_KEY=your-production-gemini-key
DEEPGRAM_API_KEY=your-production-deepgram-key
SERPER_API_KEY=your-production-serper-key

# Optional performance settings
LOG_LEVEL=INFO
WORKERS=4
```

### Docker Deployment

**Dockerfile** (create in project root):
```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/
COPY main.py .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Platform Deployment

**Recommended Platforms**:
- **Backend**: Railway, Render, or Fly.io
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Database**: Supabase (managed PostgreSQL)

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test thoroughly
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript strict mode for frontend
- Write comprehensive tests for new features
- Document API changes in this README

### Issue Reporting
- Use GitHub Issues for bug reports
- Include steps to reproduce
- Provide environment information
- Add relevant logs or screenshots

## 📚 Additional Resources

### Documentation
- [System Architecture](docs/architecture/system_architecture.md)
- [Agent Development Guide](docs/agents/agent_development.md)
- [API Reference](docs/api/api_reference.md)
- [Deployment Guide](docs/deployment/deployment_guide.md)

### Dependencies
- **Backend**: See `backend/requirements.txt`
- **Frontend**: See `frontend/package.json`

### License
This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Troubleshooting

### Common Issues

**Backend Issues**:
- **Import Errors**: Ensure `PYTHONPATH` is set correctly
- **Database Connection**: Check Supabase credentials
- **Speech API Errors**: Verify Deepgram API key

**Frontend Issues**:
- **API Connection**: Verify backend is running on port 8000
- **Build Errors**: Clear node_modules and reinstall
- **TypeScript Errors**: Check tsconfig.json configuration

**Speech Processing Issues**:
- **WebSocket Errors**: Check authentication token
- **Audio Issues**: Verify microphone permissions
- **TTS Failures**: Check Google API key and quotas

### Getting Help

1. Check the [Issues](https://github.com/your-repo/issues) for similar problems
2. Review the documentation in the `docs/` folder
3. Check the application logs for specific error messages
4. Verify environment variables are correctly set

### Support

For additional support or questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**Happy Coding! 🎉** 