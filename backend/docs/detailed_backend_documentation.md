# 📚 Detailed Backend Documentation

## Table of Contents

1. [High-Level Architecture Overview](#high-level-architecture-overview)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [API Documentation](#api-documentation)
5. [Agent System](#agent-system)
6. [Service Layer](#service-layer)
7. [Utility Modules](#utility-modules)
8. [Configuration System](#configuration-system)
9. [Event System](#event-system)
10. [Speech Processing](#speech-processing)
11. [Class Hierarchy](#class-hierarchy)
12. [Data Flow Diagrams](#data-flow-diagrams)
13. [Dependencies](#dependencies)

## High-Level Architecture Overview

The AI Interviewer Agent backend is built on a modular, event-driven architecture using FastAPI. The system follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   File Upload   │    │   Speech I/O    │
│   (External)    │    │   (External)    │    │   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Layer                           │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │ Agent API     │ │ File Proc API │ │ Speech API            │ │
│  │ /interview/*  │ │ /api/file/*   │ │ /api/speech-to-text/* │ │
│  └───────────────┘ └───────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │ LLM Service   │ │ Search Service│ │ Speech Services       │ │
│  │ (Gemini)      │ │ (Web Search)  │ │ (Deepgram/Polly)      │ │
│  └───────────────┘ └───────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Agent System                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │ AgentSession  │ │ Interviewer   │ │ Coach Agent           │ │
│  │ Manager       │ │ Agent         │ │                       │ │
│  └───────────────┘ └───────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Utility Layer                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │ Event Bus     │ │ LLM Utils     │ │ File Validation       │ │
│  │ (Pub/Sub)     │ │ (Chain Proc)  │ │ (Security)            │ │
│  └───────────────┘ └───────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Modularity**: Each component has a single responsibility and clear interfaces
2. **Event-Driven**: Components communicate through a publish/subscribe event system
3. **Dependency Injection**: Services are injected through constructor parameters
4. **Layered Architecture**: Clear separation between API, service, agent, and utility layers
5. **Singleton Pattern**: Core services use improved singleton pattern for resource management

## Directory Structure

```
backend/
├── main.py                     # Application entry point
├── config.py                   # Core configuration and logging
├── requirements.txt            # Project dependencies
├── __init__.py                 # Package initialization
│
├── api/                        # REST API layer
│   ├── __init__.py             # API package initialization
│   ├── agent_api.py            # Interview agent endpoints
│   ├── file_processing_api.py  # File upload/processing endpoints
│   ├── speech_api.py           # Speech processing endpoints (refactored)
│   ├── speech_api_original.py  # Original monolithic speech API (backup)
│   └── speech/                 # Modular speech services
│       ├── __init__.py         # Speech module exports
│       ├── connection_manager.py   # WebSocket connection management
│       ├── deepgram_handlers.py    # Deepgram event handling
│       ├── websocket_processor.py  # WebSocket message processing
│       ├── stt_service.py          # Speech-to-Text service
│       └── tts_service.py          # Text-to-Speech service
│
├── agents/                     # AI agent system
│   ├── __init__.py             # Agent package initialization
│   ├── base.py                 # Base agent class and context
│   ├── orchestrator.py         # Agent session manager/orchestrator
│   ├── interviewer.py          # Interview conducting agent
│   ├── coach.py                # Interview coaching/feedback agent
│   ├── config_models.py        # Agent configuration models
│   ├── constants.py            # Agent constants and messages
│   ├── interview_state.py      # Interview state management
│   ├── question_templates.py   # Question generation templates
│   └── templates/              # Agent prompt templates
│       ├── __init__.py         # Template package initialization
│       ├── interviewer_templates.py  # Interviewer prompts
│       └── coach_templates.py       # Coach prompts
│
├── services/                   # Business logic services
│   ├── __init__.py             # Service registry and initialization
│   ├── llm_service.py          # Language model service (Gemini)
│   ├── search_service.py       # Web search service
│   ├── search_helpers.py       # Search utility classes
│   └── search_config.py        # Search configuration data
│
├── utils/                      # Utility modules
│   ├── __init__.py             # Utility package exports
│   ├── event_bus.py            # Event system implementation
│   ├── llm_utils.py            # LLM utility functions
│   ├── llm_chain_processor.py  # LangChain processing utilities
│   ├── common.py               # Common utility functions
│   ├── file_utils.py           # File handling utilities
│   └── file_validator.py       # File security validation
│
├── config/                     # Configuration modules
│   ├── __init__.py             # Configuration package
│   └── file_processing_config.py  # File processing settings
│
├── schemas/                    # Pydantic schemas/models
│   ├── __init__.py             # Schema package initialization
│   └── session.py              # Session and API schemas
│
├── tests/                      # Test suite (organized)
│   ├── __init__.py             # Test package initialization
│   ├── run_refactoring_tests.py    # Main test runner
│   ├── test_interviewer_fix.py     # Interviewer testing
│   ├── test_websocket_endpoint.py  # WebSocket testing
│   ├── test_deepgram.py            # Deepgram connectivity testing
│   ├── api/                        # API tests
│   ├── agents/                     # Agent tests
│   ├── services/                   # Service tests
│   ├── utils/                      # Utility tests
│   └── config/                     # Configuration tests
│
└── docs/                       # Documentation (organized)
    ├── COMPREHENSIVE_REFACTORING_SUMMARY.md
    ├── detailed_backend_documentation.md
    ├── ENVIRONMENT_SETUP.md
    ├── AUDIO_FORMAT_COMPATIBILITY_FIX.md
    ├── DEEPGRAM_ASYNC_FIX_SUMMARY.md
    ├── DEEPGRAM_TIMEOUT_FIX.md
    ├── DEEPGRAM_TRANSCRIPTION_FIX_SUMMARY.md
    ├── TRANSCRIPTION_ACCUMULATION_FEATURE.md
    ├── DEEPGRAM_FILLER_WORDS_FEATURE.md
    ├── FINAL_FEATURE_IMPLEMENTATION_SUMMARY.md
    ├── TTS_VOICE_SIMPLIFICATION.md
    └── STREAMING_STT_SETUP.md
```

## Core Components

### 1. Application Entry Point (`main.py`)

**Purpose**: FastAPI application initialization and configuration

**Key Functions**:

- `root()`: Health check endpoint
- `startup_event()`: Application startup handler
- `global_exception_handler()`: Global error handling

**Dependencies**: FastAPI, CORS middleware, logging configuration

**Configuration**:

- Environment-based logging levels
- CORS settings for cross-origin requests
- Service initialization on startup

### 2. Configuration System (`config.py`)

**Purpose**: Centralized configuration and logging management

**Key Functions**:

- `get_logger(name: str) -> logging.Logger`: Creates configured loggers

**Features**:

- Environment-based configuration
- Structured logging format
- Module-specific logger creation

## API Documentation

### Agent API (`/interview/*`)

Base URL: `/interview`

#### Endpoints

##### POST `/interview/start`

**Purpose**: Initialize or reconfigure an interview session

**Request Body** (`InterviewStartRequest`):

```json
{
  "job_role": "AI Engineer",                    // Target job role
  "job_description": "AI/ML engineer role...",  // Optional job description
  "resume_content": "John Doe resume...",       // Optional resume text
  "style": "formal",                            // Interview style (formal|casual|aggressive|technical)
  "difficulty": "medium",                       // Difficulty level (easy|medium|hard)
  "target_question_count": 5,                   // Number of questions
  "company_name": "TechCorp"                    // Optional company name
}
```

**Response** (`ResetResponse`):

```json
{
  "message": "Interview session configured and reset for role: AI Engineer"
}
```

**Functionality**:

1. Validates and parses request parameters
2. Creates `SessionConfig` object
3. Updates singleton `AgentSessionManager`
4. Resets session state and publishes `SESSION_RESET` event
5. Returns confirmation message

##### POST `/interview/message`

**Purpose**: Send user message/answer to the interview system

**Request Body** (`UserInput`):

```json
{
  "message": "I have 5 years of experience in machine learning..."
}
```

**Response** (`AgentResponse`):

```json
{
  "role": "assistant",
  "agent": "interviewer",
  "content": "Can you tell me about a specific ML project you've worked on?",
  "response_type": "question",
  "timestamp": "2025-05-24T16:49:13.924533",
  "processing_time": 0.45266,
  "metadata": {
    "question_number": 2,
    "justification": "Following up on experience with specific examples"
  }
}
```

**Processing Flow**:

1. Receives user message
2. Adds message to conversation history
3. Publishes `USER_MESSAGE` event
4. Gets interviewer agent response
5. Generates coaching feedback (internal)
6. Returns interviewer response

##### POST `/interview/end`

**Purpose**: Manually end interview and get final results

**Response** (`EndResponse`):

```json
{
  "results": {
    "patterns_tendencies": "Candidate shows strong technical knowledge...",
    "strengths": "Clear communication, specific examples...",
    "weaknesses": "Could improve on system design questions...",
    "improvement_focus_areas": ["System design", "Behavioral questions"],
    "resource_search_topics": ["System design", "STAR method"],
    "recommended_resources": [...]
  },
  "per_turn_feedback": [
    {
      "question": "Tell me about yourself",
      "answer": "I am a software engineer...",
      "feedback": "Good structure, consider adding more specific examples"
    }
  ]
}
```

##### GET `/interview/history`

**Purpose**: Retrieve conversation history

**Response** (`HistoryResponse`):

```json
{
  "history": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-05-24T16:49:13.924533"
    },
    {
      "role": "assistant",
      "agent": "interviewer",
      "content": "Welcome to the interview...",
      "response_type": "introduction",
      "timestamp": "2025-05-24T16:49:14.124533"
    }
  ]
}
```

##### GET `/interview/stats`

**Purpose**: Get session performance statistics

**Response** (`StatsResponse`):

```json
{
  "stats": {
    "total_messages": 10,
    "user_messages": 5,
    "assistant_messages": 5,
    "system_messages": 0,
    "total_response_time_seconds": 2.35,
    "average_response_time_seconds": 0.47,
    "total_api_calls": 5,
    "total_tokens_used": 0
  }
}
```

##### POST `/interview/reset`

**Purpose**: Reset interview session state

### Speech API (`/api/speech-to-text/*`, `/api/text-to-speech/*`)

#### Speech-to-Text Endpoints

##### POST `/api/speech-to-text`

**Purpose**: Upload audio file for transcription (AssemblyAI)

**Request**:

- `audio_file`: File upload (multipart/form-data)
- `language`: Language code (default: "en-US")

**Response**:

```json
{
  "task_id": "uuid-1234-5678",
  "status": "processing",
  "message": "Transcription started. Use the task_id to check status."
}
```

##### GET `/api/speech-to-text/status/{task_id}`

**Purpose**: Check transcription status

**Response**:

```json
{
  "status": "completed",
  "transcription": "Hello, this is the transcribed text.",
  "confidence": 0.95,
  "language": "en"
}
```

##### WebSocket `/api/speech-to-text/stream`

**Purpose**: Real-time speech-to-text streaming (Deepgram)

**Connection Flow**:

1. Client connects to WebSocket
2. Server validates Deepgram API key
3. Establishes Deepgram connection
4. Client sends binary audio data
5. Server forwards transcription results

**Message Types**:

```json
// Connection status
{"type": "connecting", "message": "Connecting to Deepgram..."}
{"type": "connected", "message": "Ready to receive audio"}

// Transcription results
{"type": "transcript", "text": "Hello world", "is_final": false}
{"type": "transcript", "text": "Hello world!", "is_final": true}

// Speech events
{"type": "speech_started"}
{"type": "utterance_end"}

// Errors
{"type": "error", "error": "Connection failed"}
```

#### Text-to-Speech Endpoints

##### POST `/api/text-to-speech`

**Purpose**: Convert text to speech (Amazon Polly)

**Request**:

- `text`: Text to synthesize
- `voice_id`: Voice name (default: "Matthew")
- `speed`: Speech speed 0.5-2.0 (default: 1.0)

**Response**: MP3 audio data (binary)

##### POST `/api/text-to-speech/stream`

**Purpose**: Streaming text-to-speech

**Request**: Same as above
**Response**: Streaming MP3 audio data

### File Processing API (`/api/file/*`)

Handles file upload and processing for resume content extraction.

## Agent System

### Agent Architecture

The agent system follows a hierarchical structure with clear separation of concerns:

```
AgentSessionManager (Orchestrator)
├── InterviewerAgent
│   ├── InterviewState
│   ├── QuestionTemplates
│   └── LLMChains
└── CoachAgent
    ├── FeedbackTemplates
    └── LLMChains
```

### Base Classes

#### `BaseAgent` (Abstract)

**Purpose**: Foundation for all specialized agents

**Constructor Parameters**:

- `llm_service: LLMService`: Language model service
- `event_bus: Optional[EventBus]`: Event communication system
- `logger: Optional[logging.Logger]`: Logging instance

**Key Methods**:

- `process(context: AgentContext) -> Any`: Main processing method (abstract)
- `publish_event(event_type: EventType, data: Dict[str, Any])`: Event publishing
- `subscribe(event_type: EventType, callback: Callable)`: Event subscription
- `_get_system_prompt() -> str`: System prompt generation

#### `AgentContext`

**Purpose**: Context object passed to agents during processing

**Attributes**:

- `session_id: str`: Unique session identifier
- `conversation_history: List[Dict[str, Any]]`: Full conversation log
- `session_config: SessionConfig`: Interview configuration
- `event_bus: EventBus`: Communication system
- `logger: logging.Logger`: Logging instance
- `metadata: Dict[str, Any]`: Additional context data

**Key Methods**:

- `get_last_user_message() -> Optional[str]`: Retrieve last user input
- `get_history_as_text() -> str`: Format history as text
- `get_langchain_messages() -> List[Any]`: Convert to LangChain format
- `to_dict() -> Dict[str, Any]`: Serialize context

### AgentSessionManager (Orchestrator)

**Purpose**: Coordinates agent interactions and manages session state

**Key Responsibilities**:

1. Route messages between user and agents
2. Maintain conversation history
3. Generate coaching feedback
4. Manage agent lifecycle
5. Collect performance statistics

**Key Methods**:

#### `process_message(message: str) -> Dict[str, Any]`

**Purpose**: Main message processing pipeline

**Flow**:

1. Create user message data structure
2. Add to conversation history
3. Publish `USER_MESSAGE` event
4. Get interviewer agent response
5. Generate coaching feedback (background)
6. Return interviewer response

**Parameters**:

- `message: str`: User's input text

**Returns**: Agent response dictionary

#### `_get_agent(agent_type: str) -> Optional[BaseAgent]`

**Purpose**: Lazy-load agents with dependency injection

**Supported Types**:

- `"interviewer"`: Returns `InterviewerAgent` instance
- `"coach"`: Returns `CoachAgent` instance

#### `end_interview() -> Dict[str, Any]`

**Purpose**: Finalize interview and generate comprehensive results

**Returns**:

- Final coaching summary
- Per-turn feedback log
- Recommended resources

### InterviewerAgent

**Purpose**: Conducts interview sessions using LLM-driven decision making

**Key Components**:

#### State Management

- `InterviewState`: Tracks interview phases and progress
- Phases: `INITIALIZING` → `INTRODUCING` → `QUESTIONING` → `COMPLETED`

#### Question Generation

- Template-based generic questions
- LLM-generated job-specific questions
- Fallback question mechanisms

#### LLM Chains

- `job_specific_question_chain`: Generates targeted questions
- `next_action_chain`: Determines interview flow decisions

**Key Methods**:

#### `process(context: AgentContext) -> Dict[str, Any]`

**Purpose**: Main interview processing logic

**Phase Handling**:

1. **INITIALIZING**: Setup questions and move to INTRODUCING
2. **INTRODUCING**: Generate welcome message and move to QUESTIONING
3. **QUESTIONING**: Use LLM to determine next action (ask question/end interview)
4. **COMPLETED**: Return interview concluded message

#### `_determine_next_action(context: AgentContext) -> Dict[str, Any]`

**Purpose**: LLM-driven decision making for interview flow

**Process**:

1. Build context inputs (history, candidate answer, interview config)
2. Invoke LLM chain for decision
3. Parse response for action type and content
4. Handle fallbacks for errors

**Action Types**:

- `ask_new_question`: Continue with new question
- `ask_follow_up`: Follow up on previous answer
- `end_interview`: Conclude the interview

#### `_generate_questions() -> None`

**Purpose**: Create initial question bank

**Strategy**:

1. Start with default opening question
2. Generate job-specific questions (if data available)
3. Fill remaining with template-based questions
4. Ensure question count meets target

### CoachAgent

**Purpose**: Provides feedback on candidate answers and generates improvement suggestions

**Key Features**:

- Answer evaluation using structured criteria
- Final summary generation
- Resource recommendation
- STAR method assessment

## Service Layer

### ServiceRegistry Pattern

**Purpose**: Improved singleton management for core services

**Implementation**:

```python
class ServiceRegistry:
    def __init__(self):
        self._llm_service: Optional[LLMService] = None
        self._event_bus: Optional[EventBus] = None
        # ... other services
  
    def get_llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service
```

**Benefits**:

- Lazy initialization
- Better encapsulation than global variables
- Easier testing and mocking
- Centralized service management

### LLMService

**Purpose**: Centralized language model management

**Configuration**:

- Model: Google Gemini 2.0 Flash
- Temperature: 0.7 (configurable)
- API Key: From `GOOGLE_API_KEY` environment variable

**Key Methods**:

#### `get_llm() -> BaseChatModel`

**Purpose**: Returns configured LangChain model instance

**Features**:

- Lazy initialization
- Connection pooling
- Error handling and retries
- Logging integration

### SearchService

**Purpose**: Web search functionality for resource recommendations

**Features**:

- Multiple search providers (Serper API)
- Domain-specific search optimization
- Resource quality evaluation
- Relevance scoring

### Speech Services

#### STTService (Speech-to-Text)

**Purpose**: Real-time speech transcription using Deepgram

**Key Components**:

- `ConnectionManager`: WebSocket connection handling
- `DeepgramEventHandlers`: Event callback management
- `WebSocketMessageProcessor`: Message routing

**Key Methods**:

#### `handle_websocket_stream(websocket: WebSocket)`

**Purpose**: Complete WebSocket speech transcription pipeline

**Flow**:

1. Validate Deepgram API availability
2. Create connection manager and event handlers
3. Establish Deepgram WebSocket connection
4. Process audio streams and return transcriptions
5. Handle cleanup and error scenarios

#### TTSService (Text-to-Speech)

**Purpose**: Speech synthesis using Amazon Polly

**Features**:

- SSML support for speech control
- Streaming and non-streaming synthesis
- Voice selection and speed control
- Error handling and fallbacks

## Utility Modules

### Event System (`event_bus.py`)

**Purpose**: Publish/subscribe communication between components

#### `EventBus`

**Key Methods**:

- `publish(event: Event)`: Broadcast event to subscribers
- `subscribe(event_type: str, callback: Callable)`: Register event handler
- `get_history(event_type: str, limit: int)`: Retrieve event history

**Event Types**:

- `SESSION_START`: Interview session begins
- `SESSION_END`: Interview session ends
- `SESSION_RESET`: Session state reset
- `USER_MESSAGE`: User input received
- `ASSISTANT_RESPONSE`: Agent response generated
- `AGENT_LOAD`: Agent instance created
- `ERROR`: Error occurred

#### `Event` (Dataclass)

**Attributes**:

- `event_type: str`: Type of event
- `source: str`: Component that generated event
- `data: Dict[str, Any]`: Event payload
- `id: str`: Unique event identifier
- `timestamp: str`: ISO format timestamp

### LLM Utilities (`llm_utils.py`)

#### `invoke_chain_with_error_handling()`

**Purpose**: Robust LLM chain invocation with error handling

**Parameters**:

- `chain`: LangChain chain instance
- `inputs: Dict[str, Any]`: Input parameters
- `logger`: Logging instance
- `chain_name: str`: Name for logging
- `output_key: str`: Expected output key
- `default_creator: Callable`: Fallback function

**Features**:

- Automatic retry logic
- Error logging and reporting
- Fallback value generation
- Performance monitoring

### File Processing (`file_validator.py`)

#### `FileValidator`

**Purpose**: Security validation for uploaded files

**Security Checks**:

- File size limits
- MIME type validation
- Content scanning
- Malicious file detection
- Extension validation

## Configuration System

### SessionConfig

**Purpose**: Interview session configuration

**Attributes**:

- `job_role: str`: Target position
- `job_description: Optional[str]`: Role details
- `resume_content: Optional[str]`: Candidate resume
- `style: InterviewStyle`: Interview approach
- `difficulty: str`: Question complexity
- `target_question_count: int`: Number of questions
- `company_name: Optional[str]`: Organization name

### InterviewStyle (Enum)

**Values**:

- `FORMAL`: Professional, structured approach
- `CASUAL`: Relaxed, conversational style
- `AGGRESSIVE`: Challenging, pressure-testing
- `TECHNICAL`: Deep technical focus

## Class Hierarchy

```
BaseAgent (Abstract)
├── InterviewerAgent
│   ├── InterviewState
│   │   └── InterviewPhase (Enum)
│   └── LLMChains
│       ├── job_specific_question_chain
│       └── next_action_chain
└── CoachAgent
    └── LLMChains
        ├── answer_evaluation_chain
        └── final_summary_chain

ServiceRegistry
├── LLMService
│   └── ChatGoogleGenerativeAI
├── SearchService
│   ├── ResourceClassifier
│   ├── RelevanceScorer
│   └── DomainQualityEvaluator
└── AgentSessionManager
    ├── conversation_history: List[Dict]
    ├── per_turn_coaching_feedback_log: List[Dict]
    └── agents: Dict[str, BaseAgent]

EventBus
├── subscribers: Dict[str, List[Callable]]
├── event_history: List[Event]
└── Event (Dataclass)

Speech Services
├── STTService
│   ├── ConnectionManager
│   ├── DeepgramEventHandlers
│   └── WebSocketMessageProcessor
└── TTSService
    └── AWS Polly Client

API Layer
├── FastAPI Application
├── Agent API Router
├── Speech API Router
└── File Processing Router

Configuration Models
├── SessionConfig (Pydantic)
├── InterviewStyle (Enum)
└── Various Request/Response Models
```

## Data Flow Diagrams

### Interview Session Flow

```
User Request → FastAPI → Agent API → AgentSessionManager
                                         ├── InterviewerAgent
                                         │   ├── LLM Service
                                         │   ├── Question Templates
                                         │   └── Interview State
                                         └── CoachAgent
                                             ├── LLM Service
                                             └── Feedback Templates
                                                     ↓
Event Bus ← Agent Responses ← Session History ← Processing Results
    ↓
Log & Monitor → Response → FastAPI → User
```

### Speech Processing Flow

```
Audio Input → WebSocket → STTService → Deepgram API
                              ├── ConnectionManager
                              ├── EventHandlers
                              └── MessageProcessor
                                      ↓
Real-time Transcription → WebSocket → Client

Text Input → TTS API → TTSService → Amazon Polly
                           ├── SSML Processing
                           ├── Voice Selection
                           └── Stream Generation
                                   ↓
Audio Output → HTTP Response → Client
```

### Event System Flow

```
Component Action → Event Creation → EventBus.publish()
                                        ├── Event History
                                        └── Subscriber Notification
                                                ↓
                    Callback Execution ← Registered Subscribers
                              ↓
                    Component Reactions → State Updates
```

## Dependencies

### Core Dependencies

**Web Framework**:

- `fastapi==0.95.0`: Modern web framework
- `uvicorn[standard]==0.22.0`: ASGI server
- `python-multipart==0.0.7`: File upload support

**AI/ML**:

- `langchain-core>=0.1.28`: LLM framework core
- `langchain-community>=0.0.10`: LLM integrations
- `langchain-google-genai>=0.0.3`: Google Gemini integration

**Data Processing**:

- `pydantic>=1.10.0,<2.0.0`: Data validation
- `numpy==1.23.5`: Numerical computations
- `sentence-transformers>=2.2.2`: Text embeddings

**External Services**:

- `boto3`: AWS services (Polly TTS)
- `deepgram-sdk>=4.1.0`: Speech-to-text
- `httpx`: HTTP client for external APIs

**Utilities**:

- `python-dotenv>=1.0.0`: Environment variables
- `tenacity>=8.2.2`: Retry logic
- `tqdm>=4.65.0`: Progress bars

### Development Dependencies

**Testing**:

- `pytest>=7.3.1`: Testing framework
- `pytest-asyncio>=0.21.0`: Async testing

**Documentation**:

- `pymupdf>=1.21.1`: PDF processing
- `python-docx>=1.0.0`: Word document processing

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Services initialized only when needed
2. **Connection Pooling**: Reuse HTTP connections
3. **Caching**: LLM responses and search results
4. **Async Processing**: Non-blocking I/O operations
5. **Resource Management**: Proper cleanup of connections

### Monitoring Points

1. **Response Times**: API endpoint latency
2. **Memory Usage**: Service instance lifecycle
3. **Event Processing**: Event bus throughput
4. **External API Calls**: Rate limiting and errors
5. **WebSocket Connections**: Active connection count

## Security Considerations

### File Upload Security

- Size limits and type validation
- Content scanning for malicious files
- Temporary file cleanup

### API Security

- Input validation with Pydantic
- Error message sanitization
- Rate limiting considerations

### External Service Security

- API key management through environment variables
- Secure credential storage
- Connection encryption

## Error Handling Strategy

### Layered Error Handling

1. **Global Exception Handler**: Catches unhandled exceptions
2. **Service Level**: Individual service error handling
3. **Agent Level**: LLM chain error handling with fallbacks
4. **API Level**: HTTP status code mapping

### Fallback Mechanisms

1. **Default Responses**: When LLM fails
2. **Offline Mode**: When external services unavailable
3. **Graceful Degradation**: Reduced functionality vs. failure

## Future Enhancement Opportunities

### Short-Term Improvements

1. Comprehensive unit test coverage
2. Performance monitoring dashboard
3. Configuration validation system
4. Health check endpoints

### Medium-Term Features

1. Multi-tenant support
2. Interview analytics and insights
3. Advanced coaching algorithms
4. Integration with HR systems

### Long-Term Architecture

1. Microservices decomposition
2. Event sourcing implementation
3. Machine learning model pipeline
4. Real-time collaboration features

---

**Documentation Version**: 1.0
**Last Updated**: 2025-05-24
**Maintainers**: AI Interviewer Agent Development Team
