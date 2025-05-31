# AI Interviewer Agent - Database, Authentication & Session Management Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Authentication System](#authentication-system)
5. [Session Management](#session-management)
6. [File Structure &amp; Organization](#file-structure--organization)
7. [API Endpoints](#api-endpoints)
8. [Frontend Integration](#frontend-integration)
9. [Configuration &amp; Environment](#configuration--environment)
10. [Adding New Features](#adding-new-features)
11. [Troubleshooting](#troubleshooting)

## Overview

This project evolved from a single-instance local application to a multi-user, database-backed system with Supabase authentication and comprehensive session management. The system now supports:

- **Multi-user authentication** with Supabase Auth
- **Persistent session storage** with PostgreSQL
- **Thread-safe session management** for concurrent users
- **Speech task tracking** for async audio processing
- **Row-level security (RLS)** for data isolation
- **JWT-based authentication** with token refresh

## Architecture

```
Frontend (React/TypeScript)
    ↓ HTTP/REST API
Backend (FastAPI/Python)
    ↓ Service Layer
Database Manager (Supabase Client)
    ↓ PostgreSQL with RLS
Supabase (Auth + Database)
```

### Core Components

1. **Database Layer**: Supabase PostgreSQL with RLS policies
2. **Authentication Layer**: Supabase Auth with JWT tokens
3. **Service Layer**: Singleton services with dependency injection
4. **Session Management**: Thread-safe session registry
5. **API Layer**: FastAPI REST endpoints

## Database Schema

### Tables Overview

The database consists of three main tables:

#### 1. `users` Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Purpose**: Stores user profile information
**Key Features**:

- Links to Supabase Auth users via `id` field
- Email uniqueness constraint
- Auto-generated timestamps
- RLS policy restricts access to own data

#### 2. `interview_sessions` Table

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

**Purpose**: Core session persistence
**Key Features**:

- Flexible JSONB fields for dynamic data
- Status tracking for session lifecycle
- Foreign key to users with cascade delete
- Supports anonymous sessions (`user_id` can be NULL)

#### 3. `speech_tasks` Table

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

**Purpose**: Async speech processing state tracking
**Key Features**:

- Links to sessions for context
- Task type enumeration
- Progress tracking with JSONB
- Error handling with message storage

### Indexes

Performance indexes are created for common query patterns:

```sql
-- Session queries
CREATE INDEX idx_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX idx_sessions_status ON interview_sessions(status);
CREATE INDEX idx_sessions_created_at ON interview_sessions(created_at);

-- Speech task queries
CREATE INDEX idx_speech_tasks_session_id ON speech_tasks(session_id);
CREATE INDEX idx_speech_tasks_status ON speech_tasks(status);
CREATE INDEX idx_speech_tasks_created_at ON speech_tasks(created_at);
```

### Row Level Security (RLS)

RLS policies ensure data isolation between users:

```sql
-- Users can only access their own data
CREATE POLICY users_policy ON users 
    FOR ALL USING (id = auth.uid() OR auth.role() = 'service_role');

-- Sessions policy - supports anonymous sessions
CREATE POLICY sessions_policy ON interview_sessions 
    FOR ALL USING (user_id = auth.uid() OR user_id IS NULL);

-- Speech tasks inherit session access control
CREATE POLICY speech_tasks_policy ON speech_tasks 
    FOR ALL USING (
        session_id IN (
            SELECT session_id FROM interview_sessions 
            WHERE user_id = auth.uid() OR user_id IS NULL
        )
    );
```

**Important**: The `auth.role() = 'service_role'` clause allows backend operations during user registration.

### Triggers

Automatic timestamp updates:

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Applied to all tables
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Authentication System

### Supabase Auth Integration

#### Backend Authentication (`backend/api/auth_api.py`)

**Key Functions**:

1. **User Registration**

```python
async def register_user(register_data: UserRegisterRequest, db_manager: DatabaseManager)
```

- Creates Supabase Auth account
- Stores user profile in local `users` table
- Returns JWT tokens and user data

2. **User Login**

```python
async def login_user(login_data: UserLoginRequest, db_manager: DatabaseManager)
```

- Authenticates with Supabase Auth
- Retrieves user profile from local database
- Returns JWT tokens and user data

3. **Token Verification**

```python
async def get_current_user(credentials: HTTPAuthorizationCredentials, db_manager: DatabaseManager)
```

- Validates JWT tokens
- Handles both production and mock authentication
- Returns user data for authenticated requests

4. **Optional Authentication**

```python
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials], db_manager: DatabaseManager)
```

- Non-blocking authentication check
- Returns `None` if not authenticated
- Used for endpoints that support both authenticated and anonymous access

#### Authentication Models

```python
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str  # min 8 characters
    name: str      # max 100 characters

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse
```

### Frontend Authentication (`frontend/src/contexts/AuthContext.tsx`)

**AuthContext Structure**:

```typescript
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  getToken: () => string | null;
}
```

**Token Storage**:

- `ai_interviewer_access_token`: JWT access token
- `ai_interviewer_refresh_token`: Refresh token
- `ai_interviewer_user`: User profile data

**Automatic Token Management**:

- Loads tokens from localStorage on app start
- Configures axios interceptors for API calls
- Validates tokens with backend on app load
- Clears storage on authentication errors

## Session Management

### Thread-Safe Session Registry (`backend/services/session_manager.py`)

The `ThreadSafeSessionRegistry` manages concurrent user sessions with database persistence:

**Key Features**:

- **Thread Safety**: Uses asyncio locks for concurrent access
- **Memory Management**: Loads sessions on-demand, releases inactive sessions
- **Database Persistence**: Automatically saves/loads session state
- **Session Lifecycle**: Handles creation, configuration, and cleanup

**Core Methods**:

1. **Get Session Manager**

```python
async def get_session_manager(self, session_id: str) -> "AgentSessionManager"
```

- Loads session from database if not in memory
- Creates session-specific locks for thread safety
- Returns configured AgentSessionManager instance

2. **Create New Session**

```python
async def create_new_session(self, user_id: Optional[str] = None, 
                           initial_config: Optional[SessionConfig] = None) -> str
```

- Creates database record
- Handles enum serialization for SessionConfig
- Returns unique session ID

3. **Session Persistence**

```python
async def save_session(self, session_id: str) -> bool
async def release_session(self, session_id: str) -> bool
```

- Saves session state to database
- Manages memory cleanup
- Ensures data consistency

### Database Manager (`backend/database/db_manager.py`)

**Comprehensive Database Operations**:

#### User Management

```python
async def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]
async def login_user(self, email: str, password: str) -> Dict[str, Any]
async def refresh_token(self, refresh_token: str) -> Dict[str, Any]
async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]
```

#### Session Management

```python
async def create_session(self, user_id: Optional[str] = None, 
                       initial_config: Optional[Dict] = None) -> str
async def load_session_state(self, session_id: str) -> Optional[Dict]
async def save_session_state(self, session_id: str, state_data: Dict) -> bool
async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict]
```

#### Speech Task Management

```python
async def create_speech_task(self, session_id: str, task_type: str) -> str
async def update_speech_task(self, task_id: str, status: str, ...) -> bool
async def get_speech_task(self, task_id: str) -> Optional[Dict]
async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int
```

### Service Initialization (`backend/services/__init__.py`)

**Singleton Pattern with Dependency Injection**:

```python
class ServiceRegistry:
    def get_session_registry(self) -> "ThreadSafeSessionRegistry":
        if self._session_registry is None:
            # Inject required dependencies
            db_manager = self.get_database_manager()
            llm_service = self.get_llm_service()
            event_bus = self.get_event_bus()
          
            self._session_registry = ThreadSafeSessionRegistry(
                db_manager=db_manager,
                llm_service=llm_service,
                event_bus=event_bus
            )
        return self._session_registry
```

**Service Dependencies**:

- **DatabaseManager**: Supabase client for persistence
- **LLMService**: OpenAI/Anthropic API client
- **EventBus**: Inter-service communication
- **SearchService**: Web search capabilities
- **APIRateLimiter**: Request rate limiting

## File Structure & Organization

### Backend Database Files

```
backend/database/
├── __init__.py              # Module initialization
├── schema.sql               # Complete database schema
├── db_manager.py           # Supabase database operations
└── mock_db_manager.py      # Development mock database
```

**File Purposes**:

- **`schema.sql`**: Complete PostgreSQL schema with tables, indexes, RLS policies, and triggers
- **`db_manager.py`**: Production database manager with Supabase client integration
- **`mock_db_manager.py`**: Development database manager with in-memory storage

### Backend Service Files

```
backend/services/
├── __init__.py              # Service registry and initialization
├── session_manager.py       # Thread-safe session management
├── llm_service.py          # LLM API integration
├── rate_limiting.py        # API rate limiting
├── search_service.py       # Web search integration
├── search_helpers.py       # Search utility functions
└── search_config.py        # Search configuration
```

### Backend API Files

```
backend/api/
├── __init__.py              # API module initialization
├── auth_api.py             # Authentication endpoints
├── agent_api.py            # Session and interview endpoints
├── speech_api.py           # Speech processing endpoints
└── file_processing_api.py  # File upload/processing
```

### Frontend Authentication Files

```
frontend/src/
├── contexts/
│   └── AuthContext.tsx      # Authentication context and provider
├── hooks/
│   └── useInterviewSession.ts # Session state management hook
├── services/
│   └── api.ts              # API client functions
└── components/
    ├── AuthModal.tsx        # Login/register modal
    ├── LoginForm.tsx        # Login form component
    └── RegisterForm.tsx     # Registration form component
```

## API Endpoints

### Authentication Endpoints (`/auth`)

| Method | Endpoint           | Purpose           | Auth Required |
| ------ | ------------------ | ----------------- | ------------- |
| POST   | `/auth/register` | Register new user | No            |
| POST   | `/auth/login`    | User login        | No            |
| POST   | `/auth/refresh`  | Refresh token     | No            |
| GET    | `/auth/me`       | Get user profile  | Yes           |
| POST   | `/auth/logout`   | User logout       | Yes           |

### Session Endpoints (`/agent`)

| Method | Endpoint                   | Purpose            | Auth Required |
| ------ | -------------------------- | ------------------ | ------------- |
| POST   | `/agent/create_session`  | Create new session | Optional      |
| POST   | `/agent/start_interview` | Start interview    | Optional      |
| POST   | `/agent/send_message`    | Send message to AI | Optional      |
| POST   | `/agent/end_interview`   | End interview      | Optional      |
| POST   | `/agent/reset_interview` | Reset session      | Optional      |

### Speech Endpoints (`/speech`)

| Method | Endpoint                          | Purpose               | Auth Required |
| ------ | --------------------------------- | --------------------- | ------------- |
| POST   | `/speech/text_to_speech`        | Convert text to audio | Optional      |
| POST   | `/speech/speech_to_text_batch`  | Convert audio to text | Optional      |
| GET    | `/speech/task_status/{task_id}` | Get task status       | Optional      |

## Frontend Integration

### Session State Management (`useInterviewSession.ts`)

**State Structure**:

```typescript
type InterviewState = 'idle' | 'configuring' | 'interviewing' | 'reviewing_feedback' | 'completed';

interface InterviewResults {
  coachingSummary: any;
  perTurnFeedback?: PerTurnFeedbackItem[];
}
```

**API Integration Flow**:

1. **Create Session**: `createSession(config)` → Returns session ID
2. **Start Interview**: `startInterview(sessionId, config)` → Returns intro message
3. **Send Messages**: `sendMessage(sessionId, {message})` → Returns AI response
4. **End Interview**: `endInterview(sessionId)` → Returns feedback and summary

**State Transitions**:

```
configuring → interviewing → reviewing_feedback → completed
     ↑                                               ↓
     ←←←←←←←←←←← resetInterview ←←←←←←←←←←←←←←←←←←←←←
```

### Authentication Integration

**Token Management**:

```typescript
// Automatic token injection
axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

// Token validation
useEffect(() => {
  // Validate stored token on app load
  axios.get(`${API_URL}/auth/me`);
}, []);
```

**Error Handling**:

- **401 Unauthorized**: Clear tokens, redirect to login
- **403 Forbidden**: Show authentication error
- **JWT Errors**: Handle token expiration

## Configuration & Environment

### Backend Environment Variables

**Required for Production**:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# LLM Configuration
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Search Configuration
SERPER_API_KEY=your-serper-key
```

**Development Options**:

```bash
# Enable mock authentication for development
USE_MOCK_AUTH=true

# Development JWT secret (not for production)
JWT_SECRET=development_secret_key_not_for_production
```

### Frontend Environment Variables

```bash
# API base URL
VITE_API_URL=http://localhost:8000
```

### Service Configuration

**Database Manager Selection**:

```python
# Automatic selection based on environment
use_mock_auth = os.environ.get("USE_MOCK_AUTH", "false").lower() == "true"

if use_mock_auth:
    _database_manager = MockDatabaseManager()
else:
    _database_manager = DatabaseManager()
```

## Adding New Features

### Adding a New Table

1. **Update Schema** (`backend/database/schema.sql`):

```sql
CREATE TABLE your_new_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_your_table_user_id ON your_new_table(user_id);

-- Add RLS policy
ALTER TABLE your_new_table ENABLE ROW LEVEL SECURITY;
CREATE POLICY your_table_policy ON your_new_table 
    FOR ALL USING (user_id = auth.uid());

-- Add trigger
CREATE TRIGGER update_your_table_updated_at 
    BEFORE UPDATE ON your_new_table 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

2. **Add Database Methods** (`backend/database/db_manager.py`):

```python
async def create_your_record(self, user_id: str, data: Dict) -> str:
    """Create a new record in your_new_table."""
    # Implementation here

async def get_your_records(self, user_id: str) -> List[Dict]:
    """Get records for a user."""
    # Implementation here
```

3. **Add API Endpoints** (`backend/api/your_api.py`):

```python
@router.post("/create")
async def create_record(
    data: YourDataModel,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    # Implementation here
```

4. **Add Frontend Integration**:

```typescript
// Add to api.ts
export const createYourRecord = async (data: YourData): Promise<YourResponse> => {
  const response = await axios.post('/your-endpoint', data);
  return response.data;
};

// Add to component or hook
const { data, isLoading } = useQuery(['your-data'], fetchYourData);
```

### Adding Authentication to Existing Endpoints

1. **Make Authentication Optional**:

```python
async def your_endpoint(
    data: YourModel,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    user_id = current_user["id"] if current_user else None
    # Handle both authenticated and anonymous users
```

2. **Require Authentication**:

```python
async def your_endpoint(
    data: YourModel,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    user_id = current_user["id"]
    # Authenticated users only
```

### Adding New Session Data Fields

1. **Update Session Config** (`backend/agents/config_models.py`):

```python
class SessionConfig(BaseModel):
    # Existing fields...
    your_new_field: Optional[str] = None
```

2. **Handle in Session Manager** (`backend/services/session_manager.py`):

```python
# The session manager automatically handles new fields via JSONB storage
# No code changes needed for simple additions
```

3. **Update Frontend Types**:

```typescript
interface InterviewStartRequest {
  // Existing fields...
  yourNewField?: string;
}
```

## Troubleshooting

### Common Issues

#### 1. **ThreadSafeSessionRegistry Initialization Error**

```
ThreadSafeSessionRegistry.__init__() missing 3 required positional arguments
```

**Solution**: Ensure dependency injection in `backend/services/__init__.py`:

```python
self._session_registry = ThreadSafeSessionRegistry(
    db_manager=self.get_database_manager(),
    llm_service=self.get_llm_service(),
    event_bus=self.get_event_bus()
)
```

#### 2. **RLS Policy Blocking Service Operations**

```
User registration failing with permissions error
```

**Solution**: Update RLS policy to allow service role:

```sql
CREATE POLICY users_policy ON users 
    FOR ALL USING (id = auth.uid() OR auth.role() = 'service_role');
```

#### 3. **JWT Token Errors**

```
Invalid audience or JWT verification failed
```

**Solution**: Configure JWT verification:

```python
payload = jwt.decode(
    token, 
    jwt_secret,
    algorithms=["HS256"],
    options={
        "verify_signature": True,
        "verify_aud": False  # Disable audience verification for Supabase
    }
)
```

#### 4. **Session State Not Persisting**

```
Session data lost between requests
```

**Solution**: Ensure session saving in critical paths:

```python
# Always save after state changes
await session_registry.save_session(session_id)
```

#### 5. **Frontend Authentication Errors**

```
401 Unauthorized or token refresh failures
```

**Solution**: Check token storage and axios configuration:

```typescript
// Ensure token is set in axios headers
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Handle token expiration
if (error.response?.status === 401) {
  // Clear tokens and redirect to login
}
```

### Development vs Production

**Development Mode**:

- Set `USE_MOCK_AUTH=true`
- Uses `MockDatabaseManager` with in-memory storage
- Simplified JWT validation
- No Supabase dependency

**Production Mode**:

- Requires Supabase credentials
- Full JWT validation with Supabase secrets
- Database persistence with RLS
- Complete authentication flow

### Monitoring and Logging

**Database Operations**:

```python
logger.info(f"Created session: {session_id}")
logger.debug(f"Loaded session state for: {session_id}")
logger.error(f"Failed to save session: {session_id}")
```

**Authentication Events**:

```python
logger.info("User registered successfully")
logger.error(f"User login failed: {e}")
logger.debug(f"JWT verification failed: {e}")
```

**Session Management**:

```python
logger.info(f"Loaded session manager for: {session_id}")
logger.warning(f"Session {session_id} not found in database")
logger.info(f"Released session: {session_id}")
```

---

This guide provides comprehensive coverage of all database, authentication, and session management aspects of the AI Interviewer Agent. Use it as a reference for understanding the current implementation, troubleshooting issues, and adding new features.
