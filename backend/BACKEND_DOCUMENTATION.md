# AI Interviewer Agent - Backend Technical Documentation

## Table of Contents
1. [Project Structure & Backend Overview](#project-structure--backend-overview)
2. [API Endpoints](#api-endpoints)
3. [Database & Schemas](#database--schemas)
4. [Session Management](#session-management)
5. [Multi-Agent Orchestration](#multi-agent-orchestration)
6. [Concurrency & Session Isolation](#concurrency--session-isolation)
7. [Technologies & Dependencies](#technologies--dependencies)
8. [Usage Notes for Frontend Developers](#usage-notes-for-frontend-developers)

---

## Project Structure & Backend Overview

### Framework
The backend is built using **FastAPI** (v0.95.0), a modern, fast Python web framework with automatic API documentation generation and built-in async support.

### Folder Structure
```
backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management and logging
├── requirements.txt           # Python dependencies
├── api/                       # API endpoint definitions
│   ├── agent_api.py          # Interview agent endpoints
│   ├── auth_api.py           # Authentication endpoints
│   ├── speech_api.py         # Speech processing endpoints
│   └── file_processing_api.py # File upload endpoints
├── agents/                    # Multi-agent system
│   ├── orchestrator.py       # Main session orchestrator
│   ├── interviewer.py        # Interviewer agent
│   ├── agentic_coach.py      # Coaching agent
│   ├── config_models.py      # Agent configuration models
│   └── constants.py          # Agent constants
├── database/                  # Data layer
│   ├── db_manager.py         # Database operations manager
│   ├── mock_db_manager.py    # Mock implementation for testing
│   └── schema.sql            # Database schema
├── schemas/                   # Pydantic data models
│   └── session.py            # Session-related schemas
├── services/                  # Business logic services
│   ├── session_manager.py    # Session registry management
│   ├── llm_service.py        # LLM interaction service
│   ├── search_service.py     # Web search service
│   └── rate_limiting.py      # API rate limiting
├── middleware/                # Request/response middleware
│   └── session_middleware.py # Session auto-save middleware
└── utils/                     # Utility functions
    ├── event_bus.py          # Inter-component communication
    └── file_utils.py         # File processing utilities
```

### Key Configurations
- **CORS**: Configured to allow all origins (`allow_origins=["*"]`) for development
- **Middleware**: 
  - CORS middleware for cross-origin requests
  - Custom `SessionSavingMiddleware` for automatic session persistence
- **Exception Handling**: Global exception handler that logs errors and returns 500 responses
- **Logging**: Configurable log levels via `LOG_LEVEL` environment variable

---

## API Endpoints

### Authentication Endpoints
**Base Path**: `/auth`

#### POST `/auth/register`
**Purpose**: Register a new user account
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
  ```
- **Authentication**: None required
- **Associated Function**: `register_user()`

#### POST `/auth/login`
**Purpose**: Authenticate user and get access tokens
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response**: Same as register
- **Authentication**: None required
- **Associated Function**: `login_user()`

#### POST `/auth/refresh`
**Purpose**: Refresh access token using refresh token
- **Request Body**:
  ```json
  {
    "refresh_token": "refresh_token_here"
  }
  ```
- **Response**: Same token structure as login
- **Authentication**: Valid refresh token required
- **Associated Function**: `refresh_token()`

#### GET `/auth/me`
**Purpose**: Get current user profile
- **Response**:
  ```json
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
  ```
- **Authentication**: Bearer token required in `Authorization` header
- **Associated Function**: `get_user_profile()`

#### POST `/auth/logout`
**Purpose**: Logout user (invalidate session)
- **Response**:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```
- **Authentication**: Bearer token required
- **Associated Function**: `logout_user()`

### Interview Agent Endpoints
**Base Path**: `/interview`

#### POST `/interview/session`
**Purpose**: Create a new interview session
- **Request Body**:
  ```json
  {
    "job_role": "Software Engineer",
    "job_description": "Full-stack developer position...",
    "resume_content": "Resume text content...",
    "style": "formal",
    "difficulty": "medium",
    "target_question_count": 5,
    "company_name": "TechCorp",
    "interview_duration_minutes": 30,
    "use_time_based_interview": false
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "uuid",
    "message": "Session created for role: Software Engineer"
  }
  ```
- **Authentication**: Optional (supports anonymous sessions)
- **Associated Function**: `create_session()`

#### POST `/interview/start`
**Purpose**: Configure existing session and get initial interviewer message
- **Headers**: `X-Session-ID: session_uuid`
- **Request Body**: Same as session creation
- **Response**:
  ```json
  {
    "role": "assistant",
    "content": "Hello! I'm excited to conduct your interview...",
    "agent": "interviewer",
    "response_type": "introduction",
    "metadata": {},
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```
- **Authentication**: Optional
- **Associated Function**: `start_interview()`

#### POST `/interview/message`
**Purpose**: Send user message and get interviewer response
- **Headers**: `X-Session-ID: session_uuid`
- **Request Body**:
  ```json
  {
    "message": "I have 5 years of experience in React..."
  }
  ```
- **Response**: Same structure as start endpoint
- **Authentication**: Optional
- **Associated Function**: `post_message()`

#### POST `/interview/end`
**Purpose**: End interview and get final summary
- **Headers**: `X-Session-ID: session_uuid`
- **Response**:
  ```json
  {
    "results": {
      "final_summary": {...},
      "session_stats": {...}
    },
    "per_turn_feedback": [
      {
        "question": "Tell me about yourself",
        "answer": "I am a software engineer...",
        "feedback": "Great introduction, consider mentioning specific technologies..."
      }
    ]
  }
  ```
- **Authentication**: Optional
- **Associated Function**: `end_interview()`

#### GET `/interview/final-summary-status`
**Purpose**: Check status of final summary generation (async operation)
- **Headers**: `X-Session-ID: session_uuid`
- **Response**:
  ```json
  {
    "status": "completed",
    "results": {...},
    "error": null
  }
  ```
- **Status Values**: `generating`, `completed`, `error`
- **Associated Function**: `get_final_summary_status()`

#### GET `/interview/history`
**Purpose**: Get conversation history for session
- **Headers**: `X-Session-ID: session_uuid`
- **Response**:
  ```json
  {
    "history": [
      {
        "role": "user",
        "content": "Hello",
        "timestamp": "2024-01-01T00:00:00Z"
      },
      {
        "role": "assistant",
        "content": "Hi there!",
        "agent": "interviewer",
        "timestamp": "2024-01-01T00:00:01Z"
      }
    ]
  }
  ```
- **Associated Function**: `get_history()`

#### GET `/interview/stats`
**Purpose**: Get session statistics
- **Headers**: `X-Session-ID: session_uuid`
- **Response**:
  ```json
  {
    "stats": {
      "questions_asked": 3,
      "total_response_time": 45.2,
      "api_call_count": 6,
      "session_duration_minutes": 15
    }
  }
  ```
- **Associated Function**: `get_stats()`

#### POST `/interview/reset`
**Purpose**: Reset session state while keeping configuration
- **Headers**: `X-Session-ID: session_uuid`
- **Response**:
  ```json
  {
    "message": "Session reset successfully",
    "session_id": "uuid"
  }
  ```
- **Associated Function**: `reset_interview()`

### Speech Processing Endpoints
**Base Path**: `/api` (legacy) and `/speech`

#### POST `/api/speech-to-text`
**Purpose**: Convert audio file to text
- **Headers**: `X-Session-ID: session_uuid` (optional)
- **Form Data**:
  - `audio_file`: Audio file (multipart/form-data)
  - `language`: Language code (default: "en-US")
- **Response**:
  ```json
  {
    "task_id": "uuid",
    "status": "processing",
    "message": "Transcription started"
  }
  ```
- **Authentication**: Optional
- **Associated Function**: `speech_to_text()`

#### GET `/api/speech-to-text/status/{task_id}`
**Purpose**: Check transcription status
- **Response**:
  ```json
  {
    "task_id": "uuid",
    "status": "completed",
    "result": {
      "text": "Transcribed text here",
      "confidence": 0.95,
      "language": "en",
      "duration": 15.2
    },
    "error": null
  }
  ```
- **Status Values**: `processing`, `completed`, `error`
- **Associated Function**: `check_transcription_status()`

#### WebSocket `/api/speech-to-text/stream`
**Purpose**: Real-time speech-to-text streaming
- **Query Parameters**:
  - `token`: JWT token (optional)
  - `session_id`: Session ID (optional)
- **WebSocket Messages**:
  ```json
  {
    "type": "audio_chunk",
    "data": "base64_audio_data"
  }
  ```
- **Authentication**: Optional via query parameter
- **Associated Function**: `websocket_stream_endpoint()`

#### POST `/api/text-to-speech`
**Purpose**: Convert text to speech
- **Form Data**:
  - `text`: Text to convert
  - `voice_id`: Voice identifier (default: "Matthew")
  - `speed`: Speech speed (0.5-2.0, default: 1.0)
- **Response**: Audio file stream
- **Associated Function**: `text_to_speech()`

### File Processing Endpoints
**Base Path**: `/files`

#### POST `/files/upload-resume`
**Purpose**: Upload and extract text from resume file
- **Form Data**:
  - `file`: Resume file (PDF, DOCX, or TXT)
- **Response**:
  ```json
  {
    "filename": "resume.pdf",
    "resume_text": "Extracted text content...",
    "message": "File processed successfully."
  }
  ```
- **File Types Supported**: PDF, DOCX, TXT
- **Max File Size**: Configured in file validator
- **Associated Function**: `upload_resume()`

---

## Database & Schemas

### Database System
The backend uses **Supabase** (PostgreSQL) as the primary database with the following features:
- Real-time subscriptions
- Row Level Security (RLS)
- Built-in authentication
- RESTful API
- Connection managed via `supabase-py` client library

### Database Connection Setup
Connection is established in `backend/database/db_manager.py`:

```python
def __init__(self):
    self.url = os.environ.get("SUPABASE_URL")
    self.key = os.environ.get("SUPABASE_SERVICE_KEY")
    self.supabase: Client = create_client(self.url, self.key)
```

**Required Environment Variables**:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Service role key for database operations
- `SUPABASE_JWT_SECRET`: JWT secret for token verification

### Database Tables

#### `users` Table
**Purpose**: Store user account information
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Fields**:
- `id` (UUID): Primary key, auto-generated
- `email` (TEXT): Unique user email
- `name` (TEXT): User display name
- `created_at` (TIMESTAMP): Account creation time
- `updated_at` (TIMESTAMP): Last update time (auto-updated via trigger)

#### `interview_sessions` Table
**Purpose**: Store interview session data and state
```sql
CREATE TABLE interview_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_config JSONB NOT NULL DEFAULT '{}',
    conversation_history JSONB NOT NULL DEFAULT '[]',
    per_turn_feedback_log JSONB NOT NULL DEFAULT '[]',
    final_summary JSONB DEFAULT NULL,
    session_stats JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Fields**:
- `session_id` (UUID): Primary key, auto-generated
- `user_id` (UUID): Foreign key to users table (nullable for anonymous sessions)
- `session_config` (JSONB): Interview configuration (job role, style, etc.)
- `conversation_history` (JSONB): Array of conversation messages
- `per_turn_feedback_log` (JSONB): Array of coaching feedback per user response
- `final_summary` (JSONB): Final coaching summary and recommendations
- `session_stats` (JSONB): Session statistics (question count, timing, etc.)
- `status` (TEXT): Session status with constraint
- `created_at` (TIMESTAMP): Session creation time
- `updated_at` (TIMESTAMP): Last update time

#### `speech_tasks` Table
**Purpose**: Track asynchronous speech processing operations
```sql
CREATE TABLE speech_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    task_type TEXT NOT NULL CHECK (task_type IN ('stt_batch', 'tts', 'stt_stream')),
    status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'error')),
    progress_data JSONB DEFAULT '{}',
    result_data JSONB DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Fields**:
- `task_id` (UUID): Primary key, auto-generated
- `session_id` (UUID): Foreign key to interview_sessions (nullable)
- `task_type` (TEXT): Type of speech operation with constraint
- `status` (TEXT): Task status with constraint
- `progress_data` (JSONB): Task progress information
- `result_data` (JSONB): Task results (transcription, audio data, etc.)
- `error_message` (TEXT): Error details if task failed
- `created_at` (TIMESTAMP): Task creation time
- `updated_at` (TIMESTAMP): Last update time

### Table Relationships
- **users** ↔ **interview_sessions**: One-to-Many (users can have multiple sessions)
- **interview_sessions** ↔ **speech_tasks**: One-to-Many (sessions can have multiple speech tasks)

### Database Indexes
Performance indexes are created for common query patterns:
```sql
CREATE INDEX idx_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX idx_sessions_status ON interview_sessions(status);
CREATE INDEX idx_sessions_created_at ON interview_sessions(created_at);
CREATE INDEX idx_speech_tasks_session_id ON speech_tasks(session_id);
CREATE INDEX idx_speech_tasks_status ON speech_tasks(status);
CREATE INDEX idx_speech_tasks_created_at ON speech_tasks(created_at);
```

### Row Level Security (RLS)
All tables have RLS enabled with policies that ensure users can only access their own data:
- Users can only access their own user record
- Users can only access their own interview sessions
- Users can only access speech tasks for their own sessions
- Anonymous sessions (user_id IS NULL) are accessible to anyone

### ORM/Query Builder
The backend uses the **Supabase Python client** for database operations, which provides:
- Automatic connection management
- Type-safe query building
- Real-time subscriptions
- Built-in RLS support
- Automatic serialization/deserialization of JSONB fields

---

## Session Management

### Session Creation and Storage
Sessions are managed through a three-tier architecture:

1. **Database Layer** (`DatabaseManager`): Handles persistence
2. **Session Registry** (`ThreadSafeSessionRegistry`): Manages active sessions in memory
3. **Session Manager** (`AgentSessionManager`): Handles individual session logic

### Session Lifecycle

#### 1. Session Creation
```python
# Create new session in database
session_id = await session_registry.create_new_session(
    user_id=user_id,  # Optional - can be None for anonymous
    initial_config=config
)
```

#### 2. Session Loading
```python
# Load session manager (from memory or database)
session_manager = await session_registry.get_session_manager(session_id)
```

#### 3. Session Updates
Sessions are automatically saved after each operation through:
- **Middleware**: `SessionSavingMiddleware` auto-saves after session-modifying endpoints
- **Explicit Saves**: Manual saves in critical operations
- **Background Saves**: Periodic cleanup and save operations

#### 4. Session Cleanup
```python
# Save and remove from memory
await session_registry.release_session(session_id)
```

### Session/Token Strategy
The backend supports **dual authentication modes**:

#### JWT Token Authentication
- **Token Type**: JWT (JSON Web Tokens)
- **Storage**: Frontend should store in secure location (preferably httpOnly cookies)
- **Headers**: `Authorization: Bearer <token>`
- **Expiration**: Configurable via Supabase settings
- **Refresh**: Refresh tokens provided for token renewal

#### Anonymous Sessions
- **Session ID**: UUID passed via `X-Session-ID` header
- **No Authentication**: No user account required
- **Limitations**: Sessions not persistent across browser sessions
- **Use Case**: Demo mode, quick trials

### Session Data Storage
Session data is stored in the `interview_sessions` table with JSONB fields:

```json
{
  "session_config": {
    "job_role": "Software Engineer",
    "style": "formal",
    "difficulty": "medium"
  },
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "per_turn_feedback_log": [
    {
      "question": "Tell me about yourself",
      "answer": "I am...",
      "feedback": "Great start..."
    }
  ],
  "session_stats": {
    "questions_asked": 3,
    "total_response_time": 45.2
  }
}
```

### Session Timeout and Renewal
- **In-Memory Timeout**: Sessions are kept in memory during active use
- **Auto-Save**: Changes are automatically persisted to database
- **Cleanup**: Inactive sessions are released from memory but remain in database
- **No Explicit Timeout**: Sessions persist until explicitly ended or abandoned

### Session Isolation
Each session maintains:
- **Separate Agent Instances**: Each session gets its own agent instances
- **Isolated State**: Conversation history and feedback are session-specific
- **Thread Safety**: Concurrent access to same session is protected by asyncio locks

---

## Multi-Agent Orchestration

The backend implements a sophisticated multi-agent system with three main components:

### Agent Architecture

#### 1. Orchestrator (`AgentSessionManager`)
**Role**: Central coordinator and session manager
- **Responsibilities**:
  - Route messages between user and agents
  - Maintain conversation history
  - Coordinate agent interactions
  - Manage session state and statistics
  - Handle final summary generation

#### 2. Interviewer Agent (`InterviewerAgent`)
**Role**: Conducts the interview
- **Responsibilities**:
  - Generate contextually appropriate questions
  - Adapt questioning based on responses
  - Determine when interview should end
  - Provide interview flow control
- **Configuration**:
  - Interview style (formal, casual, aggressive, technical)
  - Difficulty level (easy, medium, hard)
  - Question count or time-based limits
  - Job role and company context

#### 3. Coach Agent (`AgenticCoachAgent`)
**Role**: Provides feedback and coaching
- **Responsibilities**:
  - Analyze user responses for quality
  - Generate constructive feedback
  - Provide improvement suggestions
  - Create final coaching summary
  - Search for relevant resources

### Agent Communication Flow

#### Per-Turn Interaction Flow
```
1. User sends message
2. Orchestrator receives and logs message
3. Orchestrator forwards to Interviewer Agent
4. Interviewer generates next question/response
5. Orchestrator forwards user's previous answer to Coach Agent (async)
6. Coach analyzes and generates feedback
7. Orchestrator returns Interviewer response to user
8. Coach feedback is stored for later retrieval
```

#### State Transitions Between Agents
The orchestrator manages the flow through different phases:

1. **Initialization Phase**:
   - Orchestrator creates agent instances
   - Interviewer generates welcome message
   - Session state set to "active"

2. **Interview Phase** (main loop):
   - User provides answer
   - Interviewer decides next question or continuation
   - Coach provides feedback on user's answer
   - Process repeats until end condition

3. **Completion Phase**:
   - Interviewer signals interview end
   - Coach generates comprehensive final summary
   - Session state set to "completed"
   - Final results compiled and returned

### Agent Context and Data Sharing
Agents share information through the `AgentContext` object:

```python
class AgentContext:
    def __init__(self, conversation_history, session_config, metadata=None):
        self.conversation_history = conversation_history
        self.session_config = session_config
        self.metadata = metadata or {}
```

### Event-Driven Communication
The system uses an `EventBus` for loose coupling between components:

```python
# Event types
class EventType(Enum):
    SESSION_START = "session_start"
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    AGENT_LOAD = "agent_load"
    SESSION_END = "session_end"
```

### Async Background Operations
Some operations run asynchronously to avoid blocking:

#### Final Summary Generation
```python
async def _generate_final_summary_background(self):
    """Generate final coaching summary in background thread"""
    # Runs in separate thread to avoid blocking user interaction
    # Results stored in session state for later retrieval
```

### Agent Dependencies and Initialization
Agents are lazily loaded with required dependencies:

```python
def _create_agent(self, agent_type: str) -> Optional[BaseAgent]:
    if agent_type == "interviewer":
        return InterviewerAgent(
            llm_service=self.llm_service,
            event_bus=self.event_bus,
            # ... configuration parameters
        )
    elif agent_type == "coach":
        return AgenticCoachAgent(
            llm_service=self.llm_service,
            search_service=get_search_service(),
            # ... configuration parameters
        )
```

### Error Handling and Fallbacks
The orchestrator includes robust error handling:
- **Agent Load Failures**: Graceful degradation if agents fail to initialize
- **Processing Errors**: Fallback responses if agent processing fails
- **Timeout Handling**: Prevents hanging operations
- **State Recovery**: Can recover from partial failures

---

## Concurrency & Session Isolation

### Concurrency Model
The backend uses **async/await** patterns with FastAPI's built-in concurrency support:

#### Async Request Handling
```python
@router.post("/interview/message")
async def post_message(
    user_input: UserInput,
    session_manager: AgentSessionManager = Depends(get_session_manager)
):
    # Each request runs in its own async context
    response = session_manager.process_message(user_input.message)
    return response
```

#### Background Task Management
**FastAPI BackgroundTasks** are used for non-blocking operations:

```python
@router.post("/api/speech-to-text")
async def speech_to_text(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    # ...
):
    # Start transcription in background
    background_tasks.add_task(
        transcribe_with_assemblyai_rate_limited,
        audio_file_path,
        task_id,
        session_id,
        db_manager
    )
```

### Thread Safety Mechanisms

#### Session-Level Locking
Each session has its own async lock to prevent race conditions:

```python
class ThreadSafeSessionRegistry:
    def __init__(self):
        self._active_sessions: Dict[str, "AgentSessionManager"] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    async def get_session_manager(self, session_id: str):
        # Ensure session-specific lock exists
        async with self._registry_lock:
            if session_id not in self._session_locks:
                self._session_locks[session_id] = asyncio.Lock()
        
        # Use session-specific lock for operations
        async with self._session_locks[session_id]:
            # Session operations here
```

#### Database Connection Safety
- **Supabase Client**: Thread-safe by design
- **Connection Pooling**: Handled automatically by Supabase client
- **Async Operations**: All database operations use async/await

### Session Isolation Strategy

#### Memory Isolation
Each session maintains completely separate state:

```python
class AgentSessionManager:
    def __init__(self, ...):
        # Each session gets its own instances
        self.conversation_history: List[Dict] = []
        self.per_turn_coaching_feedback_log: List[Dict] = []
        self._agents: Dict[str, BaseAgent] = {}
        # No shared mutable state between sessions
```

#### Agent Instance Isolation
- **Separate Agent Instances**: Each session creates its own agent instances
- **No Shared State**: Agents don't share state between sessions
- **Lazy Loading**: Agents are created only when needed for each session

#### Context Preservation
Context is maintained across turns within a session:

```python
def process_message(self, message: str) -> Dict[str, Any]:
    # Add to session-specific history
    self.conversation_history.append(user_message)
    
    # Pass session context to agents
    agent_context = AgentContext(
        conversation_history=self.conversation_history,
        session_config=self.session_config
    )
    
    # Agent processes with full session context
    response = agent.process(agent_context)
```

### Multiple Simultaneous User Sessions

#### Session Registry Management
```python
# Multiple users can have active sessions simultaneously
active_sessions = {
    "session-1": AgentSessionManager(...),  # User A
    "session-2": AgentSessionManager(...),  # User B  
    "session-3": AgentSessionManager(...),  # User C (anonymous)
}
```

#### Resource Management
- **Memory Cleanup**: Inactive sessions are periodically cleaned up
- **Database Persistence**: Session state is saved to database
- **Load Balancing**: Each session runs independently

#### Request Isolation
```python
# Each request is handled independently
async def post_message(
    user_input: UserInput,
    session_manager: AgentSessionManager = Depends(get_session_manager)
):
    # session_manager is specific to the session_id in request headers
    # No interference between concurrent requests to different sessions
```

### Race Condition Prevention

#### Session State Consistency
```python
async def save_session(self, session_id: str) -> bool:
    if session_id in self._active_sessions:
        manager = self._active_sessions[session_id]
        state_data = manager.to_dict()  # Atomic snapshot
        success = await self.db_manager.save_session_state(session_id, state_data)
        return success
```

#### Atomic Operations
- **Database Transactions**: Supabase handles transaction safety
- **State Snapshots**: Session state is captured atomically
- **Rollback Safety**: Failed operations don't corrupt state

### Performance Considerations
- **Memory Usage**: Sessions are released from memory when inactive
- **Database Load**: Bulk operations are batched when possible
- **CPU Usage**: LLM operations are the main bottleneck (external API calls)
- **Scaling**: Architecture supports horizontal scaling with shared database

---

## Technologies & Dependencies

### Core Framework and Libraries

#### Web Framework
- **FastAPI** (v0.95.0) - Modern, fast Python web framework
  - Purpose: API endpoint definition and request handling
  - Features: Automatic OpenAPI docs, async support, dependency injection

#### ASGI Server
- **Uvicorn** (v0.22.0) - Lightning-fast ASGI server
  - Purpose: Production-ready server with hot reloading
  - Features: HTTP/1.1 and WebSocket support, graceful shutdowns

### Language Models and AI

#### LangChain Ecosystem
- **langchain-core** (>=0.1.28) - Core LangChain functionality
- **langchain-community** (>=0.0.10) - Community integrations
- **langchain-google-genai** (>=0.0.3) - Google Gemini integration
- **langgraph** (v0.1.8) - Multi-agent workflow orchestration
- **langchain** - Main LangChain library
  - Purpose: LLM interaction, prompt management, agent coordination

### Database and Storage

#### Primary Database
- **Supabase** (>=2.0.0) - PostgreSQL with real-time features
  - Purpose: Primary data storage, user authentication, real-time subscriptions
  - Features: Row Level Security, automatic REST API, built-in auth

#### Database Migrations
- **Alembic** (>=1.9.0) - Database migration tool
  - Purpose: Schema version control and migrations
  - Features: Automatic migration generation, rollback support

### Data Processing and Validation

#### Data Models
- **Pydantic** - Data validation and serialization
  - Purpose: Request/response validation, configuration management
  - Features: Type hints, automatic validation, JSON schema generation

#### Scientific Computing
- **NumPy** (>=1.26.2) - Numerical computing
- **SciPy** (v1.10.0) - Scientific computing
  - Purpose: Mathematical operations for search and analysis

### Authentication and Security

#### JWT Handling
- **PyJWT** (>=2.6.0) - JSON Web Token implementation
  - Purpose: Token generation, validation, and decoding
  - Features: Multiple algorithms, expiration handling

#### Email Validation
- **email-validator** (>=2.0.0) - Email address validation
  - Purpose: Validate email addresses in user registration

### File Processing

#### Document Processing
- **PyMuPDF** (>=1.21.1) - PDF text extraction
- **python-docx** (>=1.0.0) - Word document processing
  - Purpose: Extract text from uploaded resume files
  - Features: Preserve formatting, handle multiple document types

### Audio Processing

#### Speech Services
- **deepgram-sdk** (>=4.1.0) - Speech-to-text service
  - Purpose: Real-time and batch audio transcription
  - Features: Multiple languages, high accuracy, streaming support

### Cloud Services

#### AWS Integration
- **boto3** - AWS SDK for Python
  - Purpose: S3 file storage, additional cloud services
  - Features: Automatic credential management, retry logic

### Communication and Events

#### Event System
- **pyee** (>=9.0.4) - Event emitter library
  - Purpose: Inter-component communication via events
  - Features: Async event handling, namespace support

#### Message Serialization
- **msgpack** (>=1.0.5) - Binary serialization
  - Purpose: Efficient data serialization for events and caching

### HTTP Client and Networking

#### HTTP Client
- **httpx** - Async HTTP client
  - Purpose: External API calls (AssemblyAI, search services)
  - Features: HTTP/2 support, connection pooling, timeouts

### Utility Libraries

#### Progress and Logging
- **tqdm** (>=4.65.0) - Progress bars
- **loguru** (>=0.7.0) - Advanced logging
  - Purpose: User feedback and debugging

#### Retry and Resilience
- **tenacity** (>=8.2.2) - Retry library
- **backoff** (>=2.2.0) - Backoff strategies
  - Purpose: Robust handling of external service failures

### Development and Testing

#### Environment Management
- **python-dotenv** (>=1.0.0) - Environment variable loading
  - Purpose: Configuration management, secrets handling

#### Testing Framework
- **pytest** (>=7.3.1) - Testing framework
- **pytest-asyncio** (>=0.21.0) - Async testing support
  - Purpose: Unit and integration testing

#### Type Extensions
- **typing-extensions** (>=4.5.0) - Extended type hints
  - Purpose: Enhanced type checking and code clarity

### File Upload Handling
- **python-multipart** (v0.0.7) - Multipart form data parsing
  - Purpose: Handle file uploads in FastAPI endpoints

### Architecture Summary
The technology stack follows modern Python best practices:

- **Async-First**: Built on async/await for high concurrency
- **Type-Safe**: Extensive use of type hints and Pydantic validation  
- **Cloud-Native**: Designed for deployment on cloud platforms
- **Modular**: Clean separation of concerns with dependency injection
- **Resilient**: Comprehensive error handling and retry mechanisms
- **Scalable**: Stateless design with external database persistence

---

## Usage Notes for Frontend Developers

### Authentication Flow

#### 1. User Registration/Login
```javascript
// Register new user
const registerResponse = await fetch('/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
    name: 'John Doe'
  })
});

const authData = await registerResponse.json();
// Store tokens securely
localStorage.setItem('access_token', authData.access_token);
localStorage.setItem('refresh_token', authData.refresh_token);
```

#### 2. Authenticated Requests
```javascript
// Include Bearer token in requests
const response = await fetch('/interview/session', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(sessionConfig)
});
```

#### 3. Token Refresh
```javascript
// Refresh expired tokens
const refreshResponse = await fetch('/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token')
  })
});
```

### Session Management Workflow

#### Complete Interview Session Flow
```javascript
// 1. Create new session
const sessionResponse = await fetch('/interview/session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    job_role: 'Software Engineer',
    style: 'formal',
    difficulty: 'medium',
    target_question_count: 5
  })
});
const { session_id } = await sessionResponse.json();

// 2. Start interview and get initial message
const startResponse = await fetch('/interview/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': session_id
  },
  body: JSON.stringify({
    job_role: 'Software Engineer',
    // ... same config as session creation
  })
});
const initialMessage = await startResponse.json();

// 3. Send user messages and get responses
const messageResponse = await fetch('/interview/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': session_id
  },
  body: JSON.stringify({
    message: 'I have 5 years of experience in React development...'
  })
});
const interviewerResponse = await messageResponse.json();

// 4. End interview and get final results
const endResponse = await fetch('/interview/end', {
  method: 'POST',
  headers: { 'X-Session-ID': session_id }
});
const finalResults = await endResponse.json();
```

### Required Headers

#### Session ID Header (Required for most interview endpoints)
```javascript
headers: {
  'X-Session-ID': 'uuid-session-id-here'
}
```

#### Authentication Header (Optional but recommended)
```javascript
headers: {
  'Authorization': 'Bearer jwt-token-here'
}
```

### Error Handling

#### Standard Error Response Format
```json
{
  "detail": "Error message description"
}
```

#### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (validation errors, missing required fields)
- **401**: Unauthorized (invalid/expired token)
- **404**: Not Found (session not found, user not found)
- **500**: Internal Server Error (server-side errors)

#### Error Handling Example
```javascript
try {
  const response = await fetch('/interview/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-ID': session_id
    },
    body: JSON.stringify({ message: userInput })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`HTTP ${response.status}: ${errorData.detail}`);
  }

  const data = await response.json();
  return data;
} catch (error) {
  console.error('API Error:', error.message);
  // Handle error appropriately in UI
}
```

### File Upload Handling

#### Resume Upload Example
```javascript
const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/files/upload-resume', {
    method: 'POST',
    body: formData // Don't set Content-Type, let browser set it
  });

  if (!response.ok) {
    throw new Error('File upload failed');
  }

  const result = await response.json();
  return result.resume_text; // Extract text for use in session config
};
```

### Speech Processing Integration

#### Audio Upload for Transcription
```javascript
const transcribeAudio = async (audioBlob, sessionId) => {
  const formData = new FormData();
  formData.append('audio_file', audioBlob, 'audio.wav');
  formData.append('language', 'en-US');

  // Start transcription
  const response = await fetch('/api/speech-to-text', {
    method: 'POST',
    headers: { 'X-Session-ID': sessionId },
    body: formData
  });

  const { task_id } = await response.json();

  // Poll for completion
  const pollForResult = async () => {
    const statusResponse = await fetch(`/api/speech-to-text/status/${task_id}`, {
      headers: { 'X-Session-ID': sessionId }
    });
    const status = await statusResponse.json();

    if (status.status === 'completed') {
      return status.result.text;
    } else if (status.status === 'error') {
      throw new Error(status.error);
    } else {
      // Still processing, check again in 1 second
      await new Promise(resolve => setTimeout(resolve, 1000));
      return pollForResult();
    }
  };

  return await pollForResult();
};
```

#### WebSocket Streaming (Real-time Speech)
```javascript
const startStreamingTranscription = (sessionId, onTranscript) => {
  const token = localStorage.getItem('access_token');
  const wsUrl = `ws://localhost:8000/api/speech-to-text/stream?token=${token}&session_id=${sessionId}`;
  
  const websocket = new WebSocket(wsUrl);
  
  websocket.onopen = () => {
    console.log('Streaming transcription started');
  };
  
  websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'transcription') {
      onTranscript(data.text);
    }
  };
  
  // Send audio chunks
  const sendAudioChunk = (audioData) => {
    websocket.send(JSON.stringify({
      type: 'audio_chunk',
      data: btoa(audioData) // Base64 encode audio data
    }));
  };
  
  return { websocket, sendAudioChunk };
};
```

### State Management Recommendations

#### Session State Tracking
```javascript
class InterviewSession {
  constructor() {
    this.sessionId = null;
    this.isActive = false;
    this.conversationHistory = [];
    this.currentConfig = null;
  }

  async createSession(config) {
    const response = await fetch('/interview/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    const data = await response.json();
    this.sessionId = data.session_id;
    this.currentConfig = config;
    return this.sessionId;
  }

  async sendMessage(message) {
    const response = await fetch('/interview/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': this.sessionId
      },
      body: JSON.stringify({ message })
    });
    const data = await response.json();
    this.conversationHistory.push({ role: 'user', content: message });
    this.conversationHistory.push(data);
    return data;
  }
}
```

### Performance Optimization Tips

#### 1. Token Management
- Store tokens securely (consider httpOnly cookies for production)
- Implement automatic token refresh
- Handle token expiration gracefully

#### 2. Session Management
- Create sessions only when needed
- Reuse sessions for multiple interactions
- Properly end sessions to free server resources

#### 3. File Uploads
- Validate file types and sizes on frontend before upload
- Show upload progress for large files
- Handle upload failures gracefully

#### 4. Real-time Features
- Use WebSockets for streaming transcription
- Implement reconnection logic for WebSocket failures
- Buffer audio data during network interruptions

#### 5. Error Recovery
- Implement retry logic for failed requests
- Cache session state locally for offline recovery
- Provide clear error messages to users

### Development vs Production Considerations

#### Development Mode
- Anonymous sessions are supported (no authentication required)
- CORS is open to all origins
- Detailed error messages are returned

#### Production Mode
- Authentication should be enforced
- Implement proper CORS policies
- Use secure token storage mechanisms
- Enable rate limiting
- Monitor session cleanup and resource usage

---

## Appendix: Environment Variables

### Required Environment Variables
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# LLM Service
GOOGLE_API_KEY=your-google-api-key

# Speech Services
ASSEMBLYAI_API_KEY=your-assemblyai-key

# Search Service
SERPER_API_KEY=your-serper-api-key

# Optional Configuration
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
USE_MOCK_AUTH=false  # Set to true for development without Supabase
```

### API Rate Limits
- **Speech-to-text**: Configurable rate limiting per user/session
- **LLM calls**: Limited by external provider (Google Gemini)
- **File uploads**: Size limits configurable in file validator

This documentation provides everything needed for frontend developers to integrate with the AI Interviewer Agent backend successfully. For additional details or clarification, refer to the source code or API documentation at `/docs` when the server is running. 