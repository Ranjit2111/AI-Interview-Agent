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
│   │   │   ├── useInterviewSession.ts # Session state management
│   │   │   └── useVoiceFirstInterview.ts # Voice-first interview experience
│   │   │
│   │   ├── services/                # API and external services
│   │   │   └── api.ts               # API client functions
│   │   │
│   │   ├── pages/                   # Page components
│   │   │   ├── Index.tsx            # Main landing/dashboard page
│   │   │   └── NotFound.tsx         # 404 error page
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
├── start.sh                       # Docker startup script
├── Dockerfile                     # Docker container configuration
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore patterns
└── README.md                      # This file
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
./run_venv.bat
```

This script will:
- Create Python virtual environment in `backend/venv/`
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
```

**Frontend Setup**:
```bash
cd frontend
npm install
```

**Start Development Servers**:

Backend (Terminal 1):
```bash
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
python -m uvicorn main:app --reload --port 8000
```

Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the Docker image
docker build -t ai-interviewer-agent .

# Run the container
docker run -p 8000:8000 --env-file .env ai-interviewer-agent
```

### Docker Compose (Optional)

Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  ai-interviewer:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
```

Run with:
```bash
docker-compose up --build
```

## 🎯 Core Features

### 🤖 Multi-Agent Interview System
- **Interviewer Agent**: Conducts structured interviews with adaptive questioning
- **Coach Agent**: Provides real-time feedback and improvement suggestions
- **Orchestrator**: Manages agent coordination and session flow

### 🎤 Voice-First Experience
- **Real-time Speech-to-Text**: Powered by Deepgram for accurate transcription
- **Text-to-Speech**: Natural-sounding AI responses with multiple voice options
- **Voice Activity Detection**: Smart microphone management and turn-taking
- **Streaming Audio**: Low-latency audio processing for seamless conversations

### 💾 Session Management
- **Persistent Sessions**: Interview history with detailed transcripts
- **Session Recovery**: Resume interrupted interviews
- **Export Options**: Download transcripts and feedback reports
- **Analytics**: Performance tracking and improvement metrics

### 📁 Document Processing
- **Resume Upload**: PDF, DOCX support with intelligent parsing
- **Job Description Analysis**: Automatic extraction of requirements
- **Content Integration**: Context-aware questioning based on documents

### 🔒 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Row Level Security**: Database-level access control via Supabase
- **Data Encryption**: Secure handling of sensitive interview data
- **Mock Mode**: Development-friendly authentication bypass

## 🛠️ Development

### Backend Development

The backend uses FastAPI with a modular architecture:

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Key Development Commands**:
```bash
# Run tests
python -m pytest tests/

# Install new dependencies
pip install package-name
pip freeze > requirements.txt

# Database migrations (if using Supabase migrations)
# Run through Supabase CLI or dashboard
```

### Frontend Development

The frontend uses React + TypeScript with Vite:

```bash
cd frontend
npm run dev
```

**Key Development Commands**:
```bash
# Build for production
npm run build

# Run linter
npm run lint

# Preview production build
npm run preview

# Install new dependencies
npm install package-name
```

### Environment Variables

**Required for Backend**:
- `GOOGLE_API_KEY`: Google AI Studio API key for Gemini models
- `DEEPGRAM_API_KEY`: Deepgram API key for speech processing
- `SUPABASE_URL` & `SUPABASE_SERVICE_KEY`: Database configuration
- `JWT_SECRET`: Secret key for JWT token generation

**Optional Development Settings**:
- `USE_MOCK_AUTH=true`: Enable mock authentication for development
- `LOG_LEVEL=DEBUG`: Enable detailed logging
- `SERPER_API_KEY`: Web search capabilities

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key API Endpoints

- `POST /api/sessions/start`: Start new interview session
- `GET/POST /api/sessions/{session_id}/messages`: Chat interface
- `WS /api/speech/ws`: WebSocket for real-time speech processing
- `POST /api/auth/login`: User authentication
- `POST /api/files/upload`: Resume/document upload

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📈 Performance

### Backend Optimizations
- **Async FastAPI**: Non-blocking request handling
- **Connection Pooling**: Efficient database connections
- **Rate Limiting**: API protection and fair usage
- **Caching**: Redis-based caching for LLM responses (if configured)

### Frontend Optimizations
- **Code Splitting**: Lazy loading for reduced bundle size
- **React Query**: Intelligent caching and background updates
- **Vite Build**: Fast development and optimized production builds

## 🚀 Production Deployment

### Environment Setup
1. Set up Supabase project with proper RLS policies
2. Configure environment variables for production
3. Set up CI/CD pipeline (GitHub Actions example provided)
4. Deploy to platform of choice (Azure, AWS, Google Cloud, etc.)

### Security Checklist
- [ ] Change all default secrets and keys
- [ ] Enable HTTPS/TLS in production
- [ ] Configure proper CORS settings
- [ ] Set up monitoring and logging
- [ ] Enable rate limiting
- [ ] Configure backup strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For support, please:
1. Check the documentation in the `/docs` folder
2. Review existing GitHub issues
3. Create a new issue with detailed information about your problem

## 📝 Recent Updates

- ✅ Removed stagewise toolbar integration
- ✅ Simplified main.tsx entry point
- ✅ Streamlined development setup
- ✅ Updated project documentation
- ✅ Enhanced voice-first interview experience
- ✅ Improved session management and persistence 