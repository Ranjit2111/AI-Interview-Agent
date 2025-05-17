# Comprehensive Codebase Documentation: AI Interviewer Agent (Backend)

## 1. High-Level Architecture Overview

The AI Interviewer Agent backend is a Python-based application built using the FastAPI framework. It employs a multi-agent architecture to simulate job interviews, provide coaching, and assess skills.

**Core Components:**

*   **FastAPI Application (`backend.main:app`)**: The main web server instance that handles HTTP requests. It's configured in `backend/main.py` and run by the root `main.py` using Uvicorn.
*   **API Endpoints**:
    *   **Interview API (`backend.api.agent_api`)**: Manages interview sessions (start, send message, end, history, stats, reset) under the `/interview` prefix.
    *   **Speech API (`backend.api.speech_api`)**: Provides speech-to-text (STT) and text-to-speech (TTS) functionalities under `/api/speech-to-text` and `/api/text-to-speech` prefixes. It uses AssemblyAI for STT and an external/configurable Kokoro TTS service for TTS.
*   **Agent Orchestrator (`AgentSessionManager` in `backend.agents.orchestrator`)**:
    *   Manages the state and flow of a single interview session.
    *   Coordinates interactions between the user and various AI agents.
    *   Lazily loads and utilizes `InterviewerAgent`, `CoachAgent`, and `SkillAssessorAgent`.
*   **AI Agents (`backend.agents/`)**:
    *   **`BaseAgent`**: Abstract base class for all agents, providing common functionality (LLM access, event bus subscription).
    *   **`InterviewerAgent`**: Conducts the interview by generating questions, processing user answers, and deciding next actions using LLM chains and predefined prompts/templates.
    *   **`CoachAgent`**: (Assumed) Analyzes user responses and provides coaching feedback (e.g., using STAR method).
    *   **`SkillAssessorAgent`**: (Assumed) Evaluates the user's skills based on the interview interaction and provides a skill profile.
*   **Services (`backend.services/`)**: Provide shared functionalities as singletons:
    *   **`LLMService`**: Manages and provides access to the Language Model (Google Gemini via `langchain_google_genai`).
    *   **`EventBus`**: A simple publish-subscribe system for inter-component communication, especially between agents and the orchestrator.
    *   **`SearchService`**: (Assumed) Provides search capabilities, potentially for enriching context with web search or document search (e.g., resumes, job descriptions). Uses providers like SerpAPI.
*   **Configuration**:
    *   Environment variables (loaded via `python-dotenv` from a `.env` file) are crucial for API keys (`GOOGLE_API_KEY`, `ASSEMBLYAI_API_KEY`, `KOKORO_API_URL`, `SEARCH_PROVIDER`, etc.) and other settings.
    *   `SessionConfig` (`backend.agents.config_models`): Pydantic model defining the configuration for an interview session (job role, style, difficulty, etc.).
*   **Data Handling**:
    *   Pydantic models are used extensively for API request/response validation and internal data structuring.
    *   Conversation history is maintained by `AgentSessionManager`.
    *   The root `main.py` mentions `init_db()` from `backend.database.connection`, and an `interview_app.db` (SQLite) file exists, suggesting database interaction, though its current usage in the refactored single-session model needs clarification (the `AgentSessionManager` interactions didn't explicitly show database saving for session data).
*   **Logging**: Centralized logging is configured in `backend/main.py` (and also mentioned in root `main.py`), outputting to console and daily log files (`logs/app-YYYYMMDD.log`).

**Component Relationships (Simplified Text Diagram):**

```
[User] <--> [Frontend (Web UI)] <--> [FastAPI Backend]
                                         |
                                         +-- [API Endpoints]
                                         |   |
                                         |   +-- /interview/* (Agent API) --> [AgentSessionManager]
                                         |   |     |
                                         |   |     +-- Manages [InterviewerAgent] (+ Coach, SkillAssessor)
                                         |   |     |     |
                                         |   |     |     +--> Uses [LLMService] --> [Google Gemini]
                                         |   |     |     +--> Uses [EventBus]
                                         |   |     |     +--> Uses [SearchService] (potentially)
                                         |   |     |
                                         |   |     |
                                         |   |     +-- Manages [SessionConfig], History
                                         |   |
                                         |   +-- /api/speech/* (Speech API)
                                         |       |
                                         |       +--> [AssemblyAI] (STT)
                                         |       +--> [Kokoro TTS] (TTS)
                                         |
                                         +-- [Services (Singletons)]
                                             +-- LLMService
                                             +-- EventBus
                                             +-- SearchService
```

The system relies heavily on an event-driven approach via the `EventBus` for decoupling components, particularly how agents might react to messages or session events without direct calls from the `InterviewerAgent`.

## 2. Function-Level Documentation

This section details key functions and their roles. For brevity, it focuses on major functions identified during the analysis. Detailed docstrings are present in the source code for many functions.

---
**File: `main.py` (root)**
---

*   **`main()`**:
    *   **Description**: Main entry point to run the backend server. Initializes logging, database (via `init_db`), creates the FastAPI app instance (by importing `app` from `backend.main` - note: the original code shows `create_app()` from `backend.api` which appears to be a slight indirection/refactor artifact, as `backend.main.app` is the actual FastAPI instance), sets up CORS, and starts the Uvicorn server.
    *   **Parameters**: None
    *   **Returns**: None

*   **`setup_cors(app: FastAPI)`**:
    *   **Description**: Configures CORS middleware for the FastAPI application, allowing requests from specified origins.
    *   **Parameters**:
        *   `app` (FastAPI): The FastAPI application instance.
    *   **Returns**: None

---
**File: `backend/main.py`**
---

*   **`app = FastAPI(...)`**:
    *   **Description**: The global FastAPI application instance for the backend. Title, description, and version are set here.
*   **`global_exception_handler(request: Request, exc: Exception)`**:
    *   **Description**: A global exception handler that catches unhandled exceptions, logs them, and returns a standardized JSON 500 error response.
    *   **Parameters**:
        *   `request` (Request): The incoming request.
        *   `exc` (Exception): The caught exception.
    *   **Returns**: `JSONResponse`
*   **`startup_event()`**:
    *   **Description**: An asynchronous function executed during FastAPI application startup. It initializes services by calling `initialize_services()` and stores the `AgentSessionManager` instance in `app.state.agent_manager`. It previously handled database initialization, which is now noted as removed/handled elsewhere (likely in root `main.py`'s `init_db` call).
    *   **Parameters**: None
    *   **Returns**: `async None`

---
**File: `backend/api/agent_api.py`**
---

*   **`create_agent_api(app)`**:
    *   **Description**: Creates an `APIRouter` for interview-related endpoints and includes it in the main FastAPI `app`.
    *   **Parameters**:
        *   `app` (FastAPI): The main FastAPI application instance.
    *   **Returns**: None

*   **`start_interview(start_request: InterviewStartRequest, request: Request)`**:
    *   **Endpoint**: `POST /interview/start`
    *   **Description**: Starts a new interview or configures the existing single session by updating the `AgentSessionManager`'s configuration and resetting its state.
    *   **Parameters**:
        *   `start_request` (InterviewStartRequest): Pydantic model containing job role, description, resume, style, difficulty, etc.
        *   `request` (Request): FastAPI request object to access `app.state.agent_manager`.
    *   **Returns**: `ResetResponse` (JSON) with a confirmation message.

*   **`post_message(user_input: UserInput, request: Request)`**:
    *   **Endpoint**: `POST /interview/message`
    *   **Description**: Sends a user's message (e.g., an answer to a question) to the `AgentSessionManager` for processing by the active agent (primarily `InterviewerAgent`).
    *   **Parameters**:
        *   `user_input` (UserInput): Pydantic model containing the user's message.
        *   `request` (Request): FastAPI request object.
    *   **Returns**: `AgentResponse` (JSON) containing the agent's reply (e.g., next question, feedback).

*   **`end_interview(request: Request)`**:
    *   **Endpoint**: `POST /interview/end`
    *   **Description**: Manually ends the current interview session via the `AgentSessionManager`, which may trigger final summaries from `CoachAgent` or `SkillAssessorAgent`.
    *   **Parameters**:
        *   `request` (Request): FastAPI request object.
    *   **Returns**: `EndResponse` (JSON) containing final results/summaries.

*   **`get_history(request: Request)`**:
    *   **Endpoint**: `GET /interview/history`
    *   **Description**: Retrieves the conversation history for the current session from `AgentSessionManager`.
    *   **Parameters**:
        *   `request` (Request): FastAPI request object.
    *   **Returns**: `HistoryResponse` (JSON).

*   **`get_stats(request: Request)`**:
    *   **Endpoint**: `GET /interview/stats`
    *   **Description**: Retrieves performance statistics for the current session from `AgentSessionManager`.
    *   **Parameters**:
        *   `request` (Request): FastAPI request object.
    *   **Returns**: `StatsResponse` (JSON).

*   **`reset_interview(request: Request)`**:
    *   **Endpoint**: `POST /interview/reset`
    *   **Description**: Resets the state of the `AgentSessionManager`, clearing history and current progress.
    *   **Parameters**:
        *   `request` (Request): FastAPI request object.
    *   **Returns**: `ResetResponse` (JSON) with a confirmation message.

---
**File: `backend/api/speech_api.py`**
---

*   **`create_speech_api(app)`**:
    *   **Description**: Creates an `APIRouter` for speech-related endpoints and includes it in the main FastAPI `app`.
    *   **Parameters**:
        *   `app` (FastAPI): The main FastAPI application instance.
    *   **Returns**: None

*   **`speech_to_text(background_tasks: BackgroundTasks, audio_file: UploadFile, language: str)`**:
    *   **Endpoint**: `POST /api/speech-to-text`
    *   **Description**: Receives an audio file, saves it temporarily, and initiates a background task (`transcribe_with_assemblyai`) for transcription using AssemblyAI.
    *   **Parameters**:
        *   `background_tasks` (BackgroundTasks): FastAPI's background task runner.
        *   `audio_file` (UploadFile): The uploaded audio data.
        *   `language` (str): Language code for transcription (form data).
    *   **Returns**: `JSONResponse` with `task_id` and `status: "processing"`.

*   **`check_transcription_status(task_id: str)`**:
    *   **Endpoint**: `GET /api/speech-to-text/status/{task_id}`
    *   **Description**: Polls the status of an ongoing AssemblyAI transcription task.
    *   **Parameters**:
        *   `task_id` (str): The ID of the transcription task.
    *   **Returns**: `JSONResponse` with current status; if "completed", includes the transcript.

*   **`get_available_voices()`**:
    *   **Endpoint**: `GET /api/text-to-speech/voices`
    *   **Description**: Fetches and returns a list of available TTS voices from the configured Kokoro TTS service.
    *   **Parameters**: None
    *   **Returns**: `JSONResponse` with voice list or error.

*   **`text_to_speech(text: str, voice_id: str, speed: float)`**:
    *   **Endpoint**: `POST /api/text-to-speech`
    *   **Description**: Generates speech audio from text using the Kokoro TTS service.
    *   **Parameters (form data)**:
        *   `text` (str): Text to synthesize.
        *   `voice_id` (str): Voice ID for TTS.
        *   `speed` (float): Speech speed.
    *   **Returns**: Audio response (e.g., `FileResponse` or `StreamingResponse` if server streams directly, format depends on Kokoro).

*   **`stream_text_to_speech(text: str, voice_id: str, speed: float)`**:
    *   **Endpoint**: `POST /api/text-to-speech/stream`
    *   **Description**: Generates and streams speech audio from text using the Kokoro TTS service.
    *   **Parameters (form data)**: (Same as `text_to_speech`)
    *   **Returns**: `StreamingResponse` with audio chunks.

---
**File: `backend/services/__init__.py`**
---

*   **`initialize_services()`**:
    *   **Description**: Eagerly initializes all singleton service instances (`LLMService`, `EventBus`, `SearchService`, `AgentSessionManager`) by calling their respective `get_...()` functions. Called on application startup.
    *   **Parameters**: None
    *   **Returns**: None

*   **`get_llm_service() -> LLMService`**:
    *   **Description**: Returns the singleton `LLMService` instance, creating it if it doesn't exist.
    *   **Parameters**: None
    *   **Returns**: `LLMService` instance.

*   **`get_event_bus() -> EventBus`**:
    *   **Description**: Returns the singleton `EventBus` instance, creating it if it doesn't exist.
    *   **Parameters**: None
    *   **Returns**: `EventBus` instance.

*   **`get_search_service() -> SearchService`**:
    *   **Description**: Returns the singleton `SearchService` instance, creating it if it doesn't exist.
    *   **Parameters**: None
    *   **Returns**: `SearchService` instance.

*   **`get_agent_session_manager() -> AgentSessionManager`**:
    *   **Description**: Returns the singleton `AgentSessionManager` instance, creating it if it doesn't exist. Depends on `LLMService` and `EventBus`.
    *   **Parameters**: None
    *   **Returns**: `AgentSessionManager` instance.

---
**File: `backend/services/llm_service.py`**
---

*   **`LLMService.__init__(api_key: Optional[str], model_name: str, temperature: float)`**:
    *   **Description**: Constructor for `LLMService`. Initializes API key (from param or `GOOGLE_API_KEY` env var), model name, and temperature. Does not create the LLM instance itself yet.
    *   **Parameters**:
        *   `api_key` (Optional[str]): Google API Key.
        *   `model_name` (str): Gemini model name (e.g., "gemini-2.0-flash").
        *   `temperature` (float): LLM sampling temperature.
    *   **Returns**: None

*   **`LLMService.get_llm() -> BaseChatModel`**:
    *   **Description**: Lazily initializes and returns the LangChain `BaseChatModel` instance (specifically `ChatGoogleGenerativeAI`).
    *   **Parameters**: None
    *   **Returns**: `ChatGoogleGenerativeAI` instance.

---
**File: `backend/agents/orchestrator.py` (`AgentSessionManager` class)**
---

*   **`AgentSessionManager.__init__(llm_service: LLMService, event_bus: EventBus, logger: logging.Logger, session_config: SessionConfig)`**:
    *   **Description**: Constructor for the session manager. Initializes with dependencies and a starting session configuration.
    *   **Parameters**: `llm_service`, `event_bus`, `logger`, `session_config`.
    *   **Returns**: None

*   **`AgentSessionManager.process_message(message: str) -> Dict[str, Any]`**:
    *   **Description**: Core method for handling user input. It appends the user message to history, publishes a `USER_MESSAGE` event, retrieves/uses the `InterviewerAgent` to generate a response via its `process` method, updates history with the agent's response, publishes an `ASSISTANT_RESPONSE` event, and returns the agent's response.
    *   **Parameters**:
        *   `message` (str): The user's input message.
    *   **Returns**: `Dict[str, Any]` representing the agent's response.

*   **`AgentSessionManager.end_interview() -> Dict[str, Any]`**:
    *   **Description**: Finalizes the interview. Publishes `SESSION_END` event. Attempts to get a skill profile from `SkillAssessorAgent` and a coaching summary from `CoachAgent`.
    *   **Parameters**: None
    *   **Returns**: `Dict[str, Any]` containing consolidated final results.

*   **`AgentSessionManager.reset_session()`**:
    *   **Description**: Resets the current session state: clears conversation history, resets statistics, re-initializes agent configurations based on the current `self.session_config`, and publishes a `SESSION_RESET` event.
    *   **Parameters**: None
    *   **Returns**: None

*   **`AgentSessionManager._get_agent(agent_type: str) -> Optional[BaseAgent]`**:
    *   **Description**: Lazily loads and returns an agent instance (`InterviewerAgent`, `CoachAgent`, `SkillAssessorAgent`) by type, injecting necessary dependencies (LLM service, event bus, logger).
    *   **Parameters**:
        *   `agent_type` (str): "interviewer", "coach", or "skill_assessor".
    *   **Returns**: `Optional[BaseAgent]` instance or None if type is unknown or loading fails.

*   **`AgentSessionManager._get_agent_context() -> AgentContext`**:
    *   **Description**: Constructs and returns an `AgentContext` object containing current session information (ID, history, config, event bus, logger) to be passed to agent methods.
    *   **Parameters**: None
    *   **Returns**: `AgentContext` instance.

---
**File: `backend/agents/interviewer.py` (`InterviewerAgent` class)**
---

*   **`InterviewerAgent.__init__(...)`**:
    *   **Description**: Constructor. Initializes with `LLMService`, `EventBus`, logger, and interview parameters (style, role, etc., which are updated by `_handle_session_start`). Sets up LLM chains and subscribes to session events.
    *   **Parameters**: `llm_service`, `event_bus`, `logger`, and various interview config parameters.
    *   **Returns**: None

*   **`InterviewerAgent.process(context: AgentContext) -> Dict[str, Any]`**:
    *   **Description**: Main processing method for the interviewer. Based on the current `InterviewState`, it either generates an introduction, calls `_determine_and_generate_next_action` for the next question/feedback, or provides a closing message. Publishes events like `QUESTION_ASKED`.
    *   **Parameters**:
        *   `context` (AgentContext): The current interview context.
    *   **Returns**: `Dict[str, Any]` containing the agent's response (content, type, metadata).

*   **`InterviewerAgent._determine_and_generate_next_action(context: AgentContext) -> Dict[str, Any]`**:
    *   **Description**: This is a key LLM interaction point. It constructs a prompt including the system message, conversation history, and specific instructions (from `NEXT_ACTION_TEMPLATE`). It then invokes the `next_action_chain` (an `LLMChain`) to get a structured JSON response from the LLM, indicating the next action (e.g., ask_question, give_feedback, end_interview) and the content for that action.
    *   **Parameters**:
        *   `context` (AgentContext): The current interview context.
    *   **Returns**: `Dict[str, Any]` parsed from the LLM's JSON output, guiding the next step.

*   **`InterviewerAgent._handle_session_start(event: Event)`**:
    *   **Description**: Event handler for `SESSION_START`. Updates the agent's internal configuration (job role, description, style, etc.) from the event data (originating from `InterviewStartRequest`), resets its state (e.g., question count), and generates the initial set of interview questions.
    *   **Parameters**:
        *   `event` (Event): The session start event object.
    *   **Returns**: None

*   **`InterviewerAgent._setup_llm_chains()`**:
    *   **Description**: Initializes various LangChain `LLMChain` instances used by the agent:
        *   `job_specific_question_chain`: For generating initial job-specific questions.
        *   `next_action_chain`: For deciding the next conversational turn (ReAct-style).
        *   `response_formatter_chain`: For styling the LLM's output.
    *   **Parameters**: None
    *   **Returns**: None

## 3. Class Hierarchy and Relationship Diagrams (Text Form)

**Primary Class Relationships:**

```
[FastAPI App (backend.main:app)]
 |
 +-- Registers Routers from:
 |   |
 |   +-- [Agent API Router (backend.api.agent_api)]
 |   |   |  (Defines endpoints like /interview/start, /message)
 |   |   |
 |   |   +--> Interacts with [AgentSessionManager (singleton)]
 |   |        |   (Instance of backend.agents.orchestrator.AgentSessionManager)
 |   |        |
 |   |        +-- (Constructor Args: LLMService, EventBus, Logger, SessionConfig)
 |   |        +-- Manages and uses:
 |   |        |   +-- [SessionConfig] (backend.agents.config_models.SessionConfig) - Data
 |   |        |   +-- Conversation History (List[Dict]) - Data
 |   |        |   +-- Agents (lazily loaded via _get_agent):
 |   |        |       +-- [InterviewerAgent] (backend.agents.interviewer.InterviewerAgent)
 |   |        |       |   |  (Extends backend.agents.base.BaseAgent)
 |   |        |       |   |
 |   |        |       |   +-- (Constructor Args: LLMService, EventBus, Logger, interview_params...)
 |   |        |       |   +--> Uses self.llm (from LLMService via BaseAgent)
 |   |        |       |   +--> Uses self.event_bus (from EventBus via BaseAgent)
 |   |        |       |   +--> Uses LLMChains (LangChain) with prompts from .templates
 |   |        |       |
 |   |        |       +-- [CoachAgent] (backend.agents.coach.CoachAgent) - (Structure similar to InterviewerAgent)
 |   |        |       |   |  (Extends backend.agents.base.BaseAgent)
 |   |        |       |
 |   |        |       +-- [SkillAssessorAgent] (backend.agents.skill_assessor.SkillAssessorAgent) - (Structure similar to InterviewerAgent)
 |   |        |           |  (Extends backend.agents.base.BaseAgent)
 |   |        |
 |   |        +-- Passes [AgentContext] to agent methods
 |   |            (backend.agents.base.AgentContext) - Data (session_id, history, config, event_bus, logger)
 |   |
 |   +-- [Speech API Router (backend.api.speech_api)]
 |       |  (Defines endpoints like /api/speech-to-text, /api/text-to-speech)
 |       |
 |       +--> Uses AssemblyAI client (external, via httpx)
 |       +--> Uses Kokoro TTS client (external, via httpx)

[Singleton Services (managed by backend.services)]
 |
 +-- [LLMService (backend.services.llm_service.LLMService)]
 |   |  (Provides get_llm() -> ChatGoogleGenerativeAI)
 |   +--> Manages [ChatGoogleGenerativeAI (LangChain)]
 |
 +-- [EventBus (backend.utils.event_bus.EventBus)]
 |   (Pub/Sub mechanism)
 |
 +-- [SearchService (backend.services.search_service.SearchService)]
     (Provides search capabilities, e.g., web search)
```

**Base Agent Inheritance:**

```
[BaseAgent (backend.agents.base.BaseAgent)]
  ^
  |-- [InterviewerAgent]
  |-- [CoachAgent]
  |-- [SkillAssessorAgent]

Properties of BaseAgent:
  - self.llm_service: LLMService
  - self.llm: BaseChatModel (from llm_service.get_llm())
  - self.event_bus: EventBus
  - self.logger: logging.Logger
  - Methods for event subscription (subscribe, publish - though publish is often direct on event_bus)
```

**Key Pydantic Models (Data Transfer Objects / Configuration):**

*   `backend.api.agent_api`:
    *   `InterviewStartRequest`: Config for starting/updating an interview.
    *   `UserInput`: User's text message.
    *   `AgentResponse`: Agent's response (role, content, type, metadata).
    *   `HistoryResponse`: Conversation history.
    *   `StatsResponse`: Session statistics.
    *   `ResetResponse`, `EndResponse`: Simple confirmation/result messages.
*   `backend.agents.config_models`:
    *   `SessionConfig`: Detailed configuration for an interview session (job_role, style, resume, etc.). Used by `AgentSessionManager` and passed to agents.
    *   `InterviewStyle` (Enum), `DifficultyLevel` (Enum), etc.
*   `backend.agents.base`:
    *   `AgentContext`: Context object passed to agent processing methods, bundling session state.

## 4. API Endpoint Documentation

The backend exposes RESTful APIs for interview management and speech services.

---
**Base URL**: `http://<host>:<port>` (e.g., `http://localhost:8000` by default)
---

### 4.1 Interview Endpoints

**Router Prefix**: `/interview`
**Module**: `backend.api.agent_api.py`

1.  **Start/Configure Interview Session**
    *   **Endpoint**: `POST /interview/start`
    *   **Description**: Initializes or reconfigures the single interview session with new parameters. This resets any existing session state.
    *   **Request Body** (`application/json`): `InterviewStartRequest` schema
        ```json
        {
          "job_role": "Software Engineer", // Optional, defaults to "General Role"
          "job_description": "Develop and maintain web applications...", // Optional
          "resume_content": "Experienced software engineer...", // Optional
          "style": "formal", // Optional, e.g., "formal", "casual", "technical"
          "difficulty": "medium", // Optional, e.g., "easy", "medium", "hard"
          "target_question_count": 5, // Optional, default 5
          "company_name": "Tech Solutions Inc." // Optional
        }
        ```
    *   **Response Body** (`application/json`): `ResetResponse` schema
        ```json
        {
          "message": "Interview session configured and reset for role: Software Engineer"
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `500 Internal Server Error`: If Agent Manager is not initialized or other errors.

2.  **Send User Message**
    *   **Endpoint**: `POST /interview/message`
    *   **Description**: Submits the user's response or message to the ongoing interview. The agent processes it and returns its next turn (e.g., a question or feedback).
    *   **Request Body** (`application/json`): `UserInput` schema
        ```json
        {
          "message": "My biggest strength is problem-solving."
        }
        ```
    *   **Response Body** (`application/json`): `AgentResponse` schema
        ```json
        {
          "role": "assistant", // "assistant" or "system"
          "content": "That's interesting. Can you give me an example of a complex problem you solved?",
          "response_type": "question", // e.g., "question", "feedback", "closing_statement"
          "metadata": { /* Additional agent-specific metadata */ }
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `500 Internal Server Error`: If an error occurs during message processing.

3.  **End Interview**
    *   **Endpoint**: `POST /interview/end`
    *   **Description**: Manually terminates the current interview session. May trigger final analysis and summary generation by coach/assessor agents.
    *   **Request Body**: None
    *   **Response Body** (`application/json`): `EndResponse` schema
        ```json
        {
          "results": {
            "status": "Interview Ended",
            "coaching_summary": { /* CoachAgent output */ },
            "skill_profile": { /* SkillAssessorAgent output */ }
          }
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `500 Internal Server Error`: If an error occurs.

4.  **Get Conversation History**
    *   **Endpoint**: `GET /interview/history`
    *   **Description**: Retrieves the full conversation history for the current session.
    *   **Request Body**: None
    *   **Response Body** (`application/json`): `HistoryResponse` schema
        ```json
        {
          "history": [
            {"role": "user", "content": "Hello", "timestamp": "..."},
            {"role": "assistant", "agent": "interviewer", "content": "Hi there! Let's begin...", "response_type": "introduction", "timestamp": "...", "processing_time": 0.5, "metadata": {}},
            // ... more messages
          ]
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `500 Internal Server Error`.

5.  **Get Session Statistics**
    *   **Endpoint**: `GET /interview/stats`
    *   **Description**: Retrieves performance and usage statistics for the current session.
    *   **Request Body**: None
    *   **Response Body** (`application/json`): `StatsResponse` schema
        ```json
        {
          "stats": {
            "total_messages": 10,
            "user_messages": 5,
            "assistant_messages": 5,
            "system_messages": 0,
            "total_response_time_seconds": 15.2,
            "average_response_time_seconds": 3.04,
            "total_api_calls": 5, // to interviewer agent
            "total_tokens_used": 0 // Placeholder, needs actual tracking if implemented
          }
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `500 Internal Server Error`.

6.  **Reset Interview Session**
    *   **Endpoint**: `POST /interview/reset`
    *   **Description**: Resets the state of the interview session manager, clearing history and progress. Does not change the configuration set by `/start`.
    *   **Request Body**: None
    *   **Response Body** (`application/json`): `ResetResponse` schema
        ```json
        {
          "message": "Interview session state has been reset."
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `500 Internal Server Error`.

### 4.2 Speech Service Endpoints

**Router Prefix**: `/api` (Note: specific paths are `/api/speech-to-text` and `/api/text-to-speech`)
**Module**: `backend.api.speech_api.py`

1.  **Speech-to-Text (STT)**
    *   **Endpoint**: `POST /api/speech-to-text`
    *   **Description**: Uploads an audio file for asynchronous transcription using AssemblyAI.
    *   **Request Body** (`multipart/form-data`):
        *   `audio_file`: The audio file (e.g., .wav, .mp3).
        *   `language` (string, form field, optional): Language code (e.g., "en-US").
    *   **Response Body** (`application/json`):
        ```json
        {
          "task_id": "unique_task_identifier_string",
          "status": "processing"
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Task accepted for processing.
        *   `422 Unprocessable Entity`: Invalid input.
        *   `503 Service Unavailable`: If AssemblyAI API key is not configured.

2.  **Check STT Status**
    *   **Endpoint**: `GET /api/speech-to-text/status/{task_id}`
    *   **Description**: Polls for the result of an STT task.
    *   **Path Parameters**:
        *   `task_id` (string): The ID returned by the POST request.
    *   **Response Body** (`application/json`):
        *   If processing: `{"status": "uploading"}` or `{"status": "transcribing"}` or `{"status": "processing"}`
        *   If completed:
            ```json
            {
              "status": "completed",
              "transcript": "This is the transcribed text."
            }
            ```
        *   If error: `{"status": "error", "error": "Error message"}`
    *   **Status Codes**:
        *   `200 OK`: Status returned.
        *   `404 Not Found`: Task ID not found.

3.  **Get Available TTS Voices**
    *   **Endpoint**: `GET /api/text-to-speech/voices`
    *   **Description**: Retrieves a list of available voices from the configured Kokoro TTS service.
    *   **Request Body**: None
    *   **Response Body** (`application/json`): (Format depends on Kokoro API, typically a list of voice objects/names)
        ```json
        // Example structure
        {
          "voices": [
            {"id": "am_michael", "name": "Michael (American English)", "language": "en-US"},
            // ... other voices
          ]
        }
        ```
    *   **Status Codes**:
        *   `200 OK`: Success.
        *   `503 Service Unavailable`: If KOKORO_API_URL is not set or service is unreachable.

4.  **Text-to-Speech (TTS) - Standard**
    *   **Endpoint**: `POST /api/text-to-speech`
    *   **Description**: Converts text to speech audio using the Kokoro TTS service.
    *   **Request Body** (`application/x-www-form-urlencoded` or `multipart/form-data`):
        *   `text` (string): The text to synthesize.
        *   `voice_id` (string, optional): The ID of the voice to use (e.g., "am_michael"). Defaults to server's default.
        *   `speed` (float, optional): Speech speed (e.g., 0.5 to 2.0). Defaults to 1.0.
    *   **Response Body**: Audio data (e.g., `audio/wav`, `audio/mpeg`). The content type will reflect the audio format returned by Kokoro.
    *   **Status Codes**:
        *   `200 OK`: Audio data returned.
        *   `422 Unprocessable Entity`: Invalid parameters.
        *   `503 Service Unavailable`: TTS service issues.

5.  **Text-to-Speech (TTS) - Streaming**
    *   **Endpoint**: `POST /api/text-to-speech/stream`
    *   **Description**: Converts text to speech and streams the audio output.
    *   **Request Body**: Same as standard TTS (`POST /api/text-to-speech`).
    *   **Response Body**: Streaming audio data (chunked). Content type reflects audio format.
    *   **Status Codes**:
        *   `200 OK`: Streaming audio started.
        *   `422 Unprocessable Entity`.
        *   `503 Service Unavailable`.

### 4.3 Root Health Check Endpoint

*   **Endpoint**: `GET /` (defined in `backend/main.py`)
*   **Description**: A simple health check endpoint.
*   **Request Body**: None
*   **Response Body** (`application/json`):
    ```json
    {
      "status": "ok",
      "message": "AI Interviewer Agent is running"
    }
    ```
*   **Status Codes**:
    *   `200 OK`.

## 5. Setup and Installation Instructions

These instructions are based on the `README.md` and observed project structure.

**Prerequisites:**

*   Python 3.9+
*   `pip` (Python package installer)
*   Node.js and `npm` (for the frontend, if setting up the full application)
*   Git

**Environment Variables (Essential):**

Create a `.env` file in the `backend/` directory with the following (at a minimum):

```env
GOOGLE_API_KEY="your_google_gemini_api_key"

# For Speech-to-Text (STT) via AssemblyAI:
ASSEMBLYAI_API_KEY="your_assemblyai_api_key"

# For Text-to-Speech (TTS) via Kokoro TTS:
KOKORO_API_URL="http://localhost:8008" # Or the URL of your Kokoro TTS instance

# For SearchService (if used by agents, e.g., SkillAssessorAgent):
SEARCH_PROVIDER="serpapi" # or "serper", "google_custom_search", etc.
SERPAPI_API_KEY="your_serpapi_key" # if using serpapi
# SERPER_API_KEY="your_serper_key" # if using serper, etc.
```

**Installation Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory_name> # e.g., ai-interviewer-agent
    ```

2.  **Set up Python Virtual Environment (Recommended):**
    ```bash
    # In the root project directory
    python -m venv venv
    # Activate the virtual environment
    # Windows:
    # venv\\Scripts\\activate
    # macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install Backend Dependencies:**
    Navigate to the `backend` directory and install the required Python packages:
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

4.  **Database Setup (if applicable):**
    The root `main.py` mentions `init_db()`. If this creates database tables (e.g., using Alembic or SQLAlchemy), ensure it runs correctly the first time. The presence of `interview_app.db` suggests SQLite is used, which might be created automatically.
    (Further details on database migrations or specific setup steps would typically be in a `docs/database_setup.md` or similar, if complex).

5.  **Install Frontend Dependencies (Optional, for full system):**
    If you intend to run the frontend:
    ```bash
    cd ../frontend # from backend/ or cd frontend from project root
    npm install
    ```

**Running the Application:**

1.  **Start the Backend Server:**
    Ensure your `.env` file is correctly configured in the `backend/` directory.
    From the root project directory:
    ```bash
    # Ensure virtual environment is active
    python main.py
    ```
    Alternatively, from the `backend/` directory (if `backend/main.py` is runnable directly with uvicorn, as its `if __name__ == "__main__"` block suggests):
    ```bash
    # cd backend
    # python main.py # This uses uvicorn.run("backend.main:app", ...)
    ```
    The server should start, typically on `http://localhost:8000`. Check the console output for the exact address.

2.  **Start the Frontend Server (Optional):**
    In a new terminal, from the `frontend/` directory:
    ```bash
    # Ensure virtual environment is NOT needed here if it's a pure Node.js frontend
    npm run dev
    ```
    The frontend will usually be available on `http://localhost:3000` (or as specified in its configuration).

## 6. Common Usage Examples

This section describes typical interactions with the backend API, usually performed by a frontend client.

**Example 1: Starting an Interview and Asking the First Question**

1.  **Client (Frontend) sends a POST request to `/interview/start`:**
    *   Payload:
        ```json
        {
          "job_role": "UX Designer",
          "job_description": "Designing intuitive user interfaces for mobile apps.",
          "resume_content": "3 years experience in UX design, proficient in Figma.",
          "style": "casual"
        }
        ```
    *   Server configures `AgentSessionManager`, resets state, generates initial questions for the UX Designer role.
    *   Server responds with: `{"message": "Interview session configured and reset for role: UX Designer"}`

2.  **Client then needs to initiate the first "message" to get the first question.** Often, the first agent response after `/start` might be an introduction. To get the actual first question, the client might send an initial "greeting" or an empty message if the agent is designed to provide the first question automatically after an introduction.
    Alternatively, the `InterviewerAgent`'s `process()` method, when in `INTRODUCING` state after a reset/start, directly returns the introduction. The client would display this.

3.  **To get the first actual question after the introduction, Client sends a POST request to `/interview/message`:**
    (Assuming the agent gives an intro, and the user is prompted to say "Ready" or similar)
    *   Payload:
        ```json
        {
          "message": "I'm ready to start."
        }
        ```
    *   `AgentSessionManager` routes this to `InterviewerAgent`.
    *   `InterviewerAgent` transitions to `QUESTIONING` state (if not already) and provides the first question from its generated list or via `_determine_and_generate_next_action`.
    *   Server responds with:
        ```json
        {
          "role": "assistant",
          "content": "Great! To begin, can you tell me about your design philosophy as a UX Designer?",
          "response_type": "question",
          "metadata": {}
        }
        ```

**Example 2: Answering a Question and Getting the Next One**

1.  **Client displays the question:** "Great! To begin, can you tell me about your design philosophy as a UX Designer?"
2.  **User provides an answer through the frontend.**
3.  **Client sends a POST request to `/interview/message`:**
    *   Payload:
        ```json
        {
          "message": "My design philosophy centers around user empathy and iterative prototyping. I believe in deeply understanding user needs before diving into solutions."
        }
        ```
    *   `AgentSessionManager` and `InterviewerAgent` process this answer. The `InterviewerAgent` (via `_determine_and_generate_next_action`) might decide to ask a follow-up, a new question, or provide brief feedback before the next question.
    *   Server responds (e.g., with the next question):
        ```json
        {
          "role": "assistant",
          "content": "That's a solid approach. Could you share an example of a project where user empathy significantly shaped your design decisions?",
          "response_type": "question",
          "metadata": {}
        }
        ```

**Example 3: Using Speech-to-Text for User Input**

1.  **User clicks a "record audio" button in the frontend.**
2.  **Frontend captures audio and sends it as a file to `POST /api/speech-to-text`**.
    *   Request: `multipart/form-data` with `audio_file` (e.g., `audio.wav`) and `language="en-US"`.
    *   Server responds: `{"task_id": "xyz789", "status": "processing"}`.

3.  **Frontend polls `GET /api/speech-to-text/status/xyz789` periodically.**
    *   Server might respond: `{"status": "transcribing"}`.
    *   Eventually, server responds: `{"status": "completed", "transcript": "My design philosophy centers around user empathy..."}`.

4.  **Frontend takes the `transcript` and uses it as the `message` payload for `POST /interview/message`** (as in Example 2, step 3).

**Example 4: Using Text-to-Speech for Agent Output**

1.  **Agent responds with a question (as in Example 1, step 3 response):**
    ```json
    {
      "role": "assistant",
      "content": "Great! To begin, can you tell me about your design philosophy as a UX Designer?",
      "response_type": "question",
      "metadata": {}
    }
    ```
2.  **Frontend displays the text `content`. Additionally, it can send this text to the TTS service.**
3.  **Client sends a `POST /api/text-to-speech/stream` (or `/api/text-to-speech`):**
    *   Payload (form data): `text="Great! To begin, can you tell me about your design philosophy as a UX Designer?"`, `voice_id="am_michael"` (optional).
    *   Server streams audio data (or returns full audio file).

4.  **Frontend plays the received audio stream.**

**Example 5: Ending the Interview**

1.  **User indicates they want to end the interview (e.g., clicks "End Interview" button).**
2.  **Client sends a `POST /interview/end`:**
    *   Request Body: None.
    *   Server invokes `AgentSessionManager.end_interview()`. `CoachAgent` and `SkillAssessorAgent` might perform final analyses.
    *   Server responds with:
        ```json
        {
          "results": {
            "status": "Interview Ended",
            "coaching_summary": {
              "overall_feedback": "Good performance, remember to use more specific examples for behavioral questions.",
              "strengths": ["Clear communication"],
              "areas_for_improvement": ["STAR method for examples"]
            },
            "skill_profile": {
              "technical_skills": {"UX Design Principles": "Proficient", "Figma": "Experienced"},
              "soft_skills": {"Communication": "Strong", "Problem Solving": "Demonstrated"}
            }
          }
        }
        ```
3.  **Client displays the summary results to the user.**

---
This documentation provides a comprehensive overview based on the codebase analysis. For more specific details on agent prompts, LLM interaction nuances, or frontend implementation, the source code and any existing detailed design documents (like those mentioned in `README.md` under `docs/`) should be consulted. 