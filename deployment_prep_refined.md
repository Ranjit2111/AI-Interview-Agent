# AI Interviewer Agent: Comprehensive Deployment Plan (Refined)

## Executive Summary

This refined deployment plan addresses critical concurrency issues discovered through comprehensive codebase analysis. The current architecture uses global singleton patterns that will cause severe data corruption and cross-user interference in production. This plan provides a systematic approach to refactor for true multi-user support while respecting external API rate limits.

## Critical Issues Identified from Codebase Analysis

### 1. **Global Session State Collision** (CRITICAL)
- **Location**: `backend/main.py:85` and `backend/api/agent_api.py:70-75`
- **Issue**: Single `AgentSessionManager` in `app.state.agent_manager` shared by all users
- **Impact**: User A's interview config/history affects User B
- **Evidence**: `agent_manager.session_config = new_config` overwrites global state

### 2. **Shared Speech Task Storage** (HIGH)
- **Location**: `backend/api/speech_api.py:25`
- **Issue**: Global `speech_tasks` dictionary stores all transcription tasks
- **Impact**: Task ID collisions, potential data leakage between users

### 3. **Singleton Service Cache Sharing** (MEDIUM)
- **Location**: `backend/services/search_service.py:142-143`
- **Issue**: Search cache shared across all users
- **Impact**: Cache pollution, incorrect search results for different contexts

### 4. **No External API Rate Limiting** (HIGH)
- **Issue**: No concurrency controls for AssemblyAI (5), Polly (26), Deepgram
- **Impact**: API failures, service degradation under load

## Phase I: Core Architecture Refactoring (Foundation)

### Stage 1: Database Setup & Schema Design

**Task 1.1: Supabase Project Setup**
```bash
# Create Supabase project and obtain credentials
SUPABASE_URL=your_project_url
SUPABASE_SERVICE_KEY=your_service_key
```

**Task 1.2: Database Schema Implementation**
```sql
-- Users table (for authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table (core session management)
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

-- Speech tasks table (separate speech processing state)
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

-- Indexes for performance
CREATE INDEX idx_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX idx_sessions_status ON interview_sessions(status);
CREATE INDEX idx_speech_tasks_session_id ON speech_tasks(session_id);
CREATE INDEX idx_speech_tasks_status ON speech_tasks(status);
```

**Task 1.3: Database Access Layer**
```python
# backend/database/db_manager.py
import os
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        self.supabase: Client = create_client(url, key)
    
    async def create_session(self, user_id: Optional[str] = None, 
                           initial_config: Optional[Dict] = None) -> str:
        """Create new interview session"""
        
    async def load_session_state(self, session_id: str) -> Optional[Dict]:
        """Load complete session state"""
        
    async def save_session_state(self, session_id: str, state_data: Dict):
        """Save session state atomically"""
        
    async def create_speech_task(self, session_id: str, task_type: str) -> str:
        """Create speech processing task"""
        
    async def update_speech_task(self, task_id: str, status: str, 
                               progress_data: Dict = None, result_data: Dict = None):
        """Update speech task progress/results"""
```

### Stage 2: Session Manager Refactoring

**Task 2.1: Thread-Safe Session Management**
```python
# backend/services/session_manager.py
import asyncio
from typing import Dict, Optional
from backend.database.db_manager import DatabaseManager
from backend.agents.orchestrator import AgentSessionManager

class ThreadSafeSessionRegistry:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._session_locks = {}
        self._active_sessions: Dict[str, AgentSessionManager] = {}
        self._lock = asyncio.Lock()
    
    async def get_session_manager(self, session_id: str) -> AgentSessionManager:
        """Get or create session manager for specific session"""
        async with self._lock:
            if session_id not in self._active_sessions:
                # Load from database and create manager
                session_data = await self.db_manager.load_session_state(session_id)
                manager = AgentSessionManager.from_session_data(session_data)
                self._active_sessions[session_id] = manager
            return self._active_sessions[session_id]
    
    async def release_session(self, session_id: str):
        """Save and release session manager"""
        async with self._lock:
            if session_id in self._active_sessions:
                manager = self._active_sessions[session_id]
                await self.db_manager.save_session_state(session_id, manager.to_dict())
                del self._active_sessions[session_id]
```

**Task 2.2: AgentSessionManager Refactoring**
```python
# Modify backend/agents/orchestrator.py
class AgentSessionManager:
    def __init__(self, session_id: str, llm_service: LLMService, 
                 event_bus: EventBus, logger: logging.Logger, 
                 session_config: SessionConfig):
        self.session_id = session_id  # Add session-specific ID
        # ... existing initialization
    
    @classmethod
    def from_session_data(cls, session_data: Dict) -> 'AgentSessionManager':
        """Create manager from database session data"""
        
    def to_dict(self) -> Dict:
        """Serialize manager state for database storage"""
    
    def get_langchain_config(self) -> Dict:
        """Get LangChain configuration with thread_id"""
        return {"configurable": {"thread_id": self.session_id}}
```

### Stage 3: API Layer Modifications

**Task 3.1: Session-Aware API Endpoints**
```python
# backend/api/agent_api.py modifications
from backend.services.session_manager import ThreadSafeSessionRegistry

# Dependency injection
async def get_session_id(request: Request) -> str:
    """Extract or create session ID from request"""
    # Check for session_id in headers, JWT token, or create new
    
async def get_session_manager(session_id: str = Depends(get_session_id)) -> AgentSessionManager:
    """Get session-specific manager"""
    registry = request.app.state.session_registry
    return await registry.get_session_manager(session_id)

@router.post("/start", response_model=ResetResponse)
async def start_interview(
    start_request: InterviewStartRequest,
    session_manager: AgentSessionManager = Depends(get_session_manager)
):
    """Session-specific interview start"""
    # Use session_manager instead of global manager
```

## Phase II: External API Concurrency Management

### Stage 1: AssemblyAI Rate Limiting (5 concurrent)

**Task 1.1: Semaphore-Based Limiting**
```python
# backend/api/speech_api.py modifications
import asyncio

# Global semaphore for AssemblyAI concurrency
ASSEMBLYAI_SEMAPHORE = asyncio.Semaphore(5)

async def transcribe_with_assemblyai(audio_file_path: str, task_id: str):
    async with ASSEMBLYAI_SEMAPHORE:
        # Existing transcription logic
        # This ensures only 5 concurrent AssemblyAI requests
```

**Task 1.2: Database-Backed Task Management**
```python
# Replace global speech_tasks dict with database
async def create_transcription_task(session_id: str, file_path: str) -> str:
    db_manager = get_db_manager()
    task_id = await db_manager.create_speech_task(session_id, 'stt_batch')
    
    # Start background task with semaphore control
    background_tasks.add_task(transcribe_with_semaphore, file_path, task_id)
    return task_id
```

### Stage 2: Amazon Polly Rate Limiting (26 concurrent)

**Task 2.1: Polly Concurrency Control**
```python
# backend/api/speech/tts_service.py modifications
POLLY_SEMAPHORE = asyncio.Semaphore(26)

class TTSService:
    async def synthesize_text(self, text: str, voice_id: str, speed: float):
        async with POLLY_SEMAPHORE:
            # Existing TTS logic with rate limiting
```

**Task 2.2: Retry Logic with Exponential Backoff**
```python
import boto3
from botocore.config import Config

# Configure boto3 client with retry logic
polly_config = Config(
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    }
)
self.polly_client = boto3.client('polly', config=polly_config)
```

### Stage 3: Deepgram Streaming Concurrency

**Task 3.1: Connection Pool Management**
```python
# backend/api/speech/stt_service.py modifications
class STTService:
    def __init__(self):
        self.max_concurrent_streams = 10  # Adjust based on Deepgram tier
        self.active_streams = 0
        self.stream_semaphore = asyncio.Semaphore(self.max_concurrent_streams)
    
    async def handle_websocket_stream(self, websocket: WebSocket):
        try:
            async with self.stream_semaphore:
                self.active_streams += 1
                # Existing WebSocket handling
        finally:
            self.active_streams -= 1
```

## Phase III: Authentication & User Management

### Stage 1: Supabase Authentication Integration

**Task 1.1: Auth API Endpoints**
```python
# backend/api/auth_api.py (new file)
from supabase import create_client
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)) -> Dict:
    """Verify Supabase JWT token"""
    try:
        # Verify with Supabase
        user = supabase.auth.get_user(token.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register")
async def register_user(email: str, password: str):
    """User registration"""
    
@router.post("/login") 
async def login_user(email: str, password: str):
    """User login"""
```

**Task 1.2: Protected Endpoints**
```python
# Modify all /interview/* endpoints
@router.post("/start", response_model=ResetResponse)
async def start_interview(
    start_request: InterviewStartRequest,
    current_user: Dict = Depends(verify_token)
):
    """Protected interview start"""
    user_id = current_user['id']
    # Create session tied to user_id
```

### Stage 2: Frontend Authentication Integration

**Task 2.1: Auth Context Provider**
```typescript
// frontend/src/contexts/AuthContext.tsx
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    
    const login = async (email, password) => {
        // Implement Supabase auth
    };
    
    const logout = async () => {
        // Clear auth state
    };
};
```

**Task 2.2: Protected Routes**
```typescript
// frontend/src/components/ProtectedRoute.tsx
export const ProtectedRoute = ({ children }) => {
    const { user } = useAuth();
    return user ? children : <Navigate to="/login" />;
};
```

## Phase IV: Testing & Validation

### Stage 1: Concurrent Session Testing

**Task 1.1: Load Testing Scripts**
```python
# tests/concurrent_test.py
import asyncio
import aiohttp
import pytest

async def simulate_concurrent_interviews():
    """Test multiple users starting interviews simultaneously"""
    sessions = []
    for i in range(10):
        session = aiohttp.ClientSession()
        sessions.append(session)
    
    # Start concurrent interviews
    tasks = [start_interview(session, f"user_{i}") for i, session in enumerate(sessions)]
    results = await asyncio.gather(*tasks)
    
    # Verify no state collision
    assert all(result['user_id'] != other_result['user_id'] 
               for result in results for other_result in results if result != other_result)
```

**Task 1.2: API Rate Limit Testing**
```python
async def test_assemblyai_rate_limiting():
    """Test AssemblyAI concurrency limiting"""
    # Attempt to start 10 transcriptions simultaneously
    # Verify only 5 are active at once
```

### Stage 2: Integration Testing

**Task 2.1: End-to-End Flow Testing**
```python
async def test_complete_interview_flow():
    """Test complete interview from start to finish"""
    # 1. User registration/login
    # 2. Session creation
    # 3. Interview configuration
    # 4. Message exchange
    # 5. Speech processing
    # 6. Interview completion
    # 7. Data persistence verification
```

## Phase V: Production Deployment

### Stage 1: Environment Configuration

**Task 1.1: Environment Variables**
```bash
# Production environment variables
SUPABASE_URL=your_production_url
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_JWT_SECRET=your_jwt_secret
GOOGLE_API_KEY=your_gemini_key
ASSEMBLYAI_API_KEY=your_assemblyai_key
DEEPGRAM_API_KEY=your_deepgram_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
SERPER_API_KEY=your_serper_key
```

**Task 1.2: Docker Configuration**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY main.py .

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Stage 2: Deployment Platform Setup

**Task 2.1: Render/Railway Deployment**
```yaml
# render.yaml
services:
  - type: web
    name: ai-interviewer-backend
    env: python
    plan: starter
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
```

### Stage 3: Monitoring & Observability

**Task 3.1: Application Monitoring**
```python
# backend/utils/monitoring.py
import logging
from prometheus_client import Counter, Histogram, Gauge

# Metrics
interview_sessions_total = Counter('interview_sessions_total', 'Total interview sessions')
response_time_seconds = Histogram('response_time_seconds', 'Response time in seconds')
active_sessions = Gauge('active_sessions', 'Number of active sessions')

def track_session_metrics(func):
    """Decorator to track session metrics"""
    def wrapper(*args, **kwargs):
        interview_sessions_total.inc()
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            response_time_seconds.observe(time.time() - start_time)
    return wrapper
```

## Phase VI: Additional Considerations & Future Improvements

### Stage 1: Performance Optimization

**Task 1.1: Database Connection Pooling**
```python
# backend/database/connection_pool.py
from sqlalchemy.pool import QueuePool
import asyncpg

class ConnectionPool:
    def __init__(self):
        self.pool = asyncpg.create_pool(
            dsn=database_url,
            min_size=5,
            max_size=20
        )
```

**Task 1.2: Redis Caching Layer**
```python
# backend/services/cache_service.py
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.Redis.from_url(os.environ.get("REDIS_URL"))
    
    async def get_search_cache(self, key: str):
        """Get cached search results"""
    
    async def set_search_cache(self, key: str, value: str, ttl: int = 3600):
        """Cache search results"""
```

### Stage 2: Security Enhancements

**Task 2.1: Rate Limiting by User**
```python
# backend/middleware/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implement per-user rate limiting
```

**Task 2.2: Input Validation & Sanitization**
```python
# Enhanced Pydantic models with strict validation
class InterviewStartRequest(BaseModel):
    job_role: str = Field(..., min_length=1, max_length=100)
    job_description: Optional[str] = Field(None, max_length=5000)
    # Add regex validation, content filtering
```

## Implementation Timeline

### Week 1-2: Foundation (Phase I)
- Database setup and schema
- Session manager refactoring
- Basic API modifications

### Week 3: Concurrency Controls (Phase II)
- External API rate limiting
- Speech task management
- Load testing

### Week 4: Authentication (Phase III)
- Supabase auth integration
- Frontend auth implementation
- Protected endpoints

### Week 5: Testing & Deployment (Phase IV-V)
- Comprehensive testing
- Production deployment
- Monitoring setup

### Week 6: Optimization (Phase VI)
- Performance tuning
- Security hardening
- Documentation

## Success Metrics

1. **Concurrency**: Support 50+ concurrent users without state collision
2. **Performance**: <2s average response time for interview questions
3. **Reliability**: 99.5% uptime with proper error handling
4. **Scalability**: Linear cost scaling with user growth
5. **Security**: Zero data leakage between user sessions

## Risk Mitigation

1. **Database Migration**: Use Supabase migrations for schema changes
2. **API Rate Limits**: Implement circuit breakers for external APIs
3. **State Corruption**: Comprehensive session isolation testing
4. **Performance Degradation**: Redis caching and connection pooling
5. **Security Vulnerabilities**: Regular dependency updates and security scanning

This plan addresses every critical issue identified in the codebase analysis and provides a clear path to production-ready multi-user deployment. 