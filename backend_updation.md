# Refactoring Plan: Simplify to Single-Session, Local-Only Application

**Goal:** Remove multi-session management, database persistence, user management, vector stores, and related complexities (like transcript/resource persistence). Retain the core interview logic driven by `AgentSessionManager`, including the `SkillAssessorAgent` and `SearchService`, for a single, local session.

**Phase 1: Create Standalone Configuration & Decouple Core Agents**

1.  **Create `backend/agents/config_models.py`:** `[DONE]`
    *   **Action:** Create the file `backend/agents/config_models.py`.
    *   **Action:** Open `backend/models/interview.py`. Copy the full `InterviewStyle` enum definition (lines 15-23 approx).
    *   **Action:** Paste the `InterviewStyle` enum into `backend/agents/config_models.py`.
    *   **Action:** In `backend/agents/config_models.py`, define a Pydantic `BaseModel` or Python `@dataclass` named `SessionConfig`.
    *   **Action:** Add the following fields to `SessionConfig` with type hints and defaults: `job_role: str = "General Role"`, `job_description: Optional[str] = None`, `resume_content: Optional[str] = None`, `style: InterviewStyle = InterviewStyle.FORMAL`, `difficulty: str = "medium"`, `target_question_count: int = 5`, `company_name: Optional[str] = None`. (Ensure `Optional` is imported from `typing`).
    *   **Action:** Add required imports to `config_models.py` (e.g., `enum`, `Optional` from `typing`, potentially `BaseModel` from `pydantic`).
    *   **Action:** Verify `config_models.py` contains *no* imports from `backend.models`, `backend.database`, or `sqlalchemy`.

2.  **Update `AgentContext` (`backend/agents/base.py`):** `[DONE]`
    *   **Action:** Change import: `from backend.models.interview import InterviewSession` -> `from backend.agents.config_models import SessionConfig`.
    *   **Action:** In the `AgentContext.__init__` method definition, change the type hint for the `session_config` parameter from `: InterviewSession` to `: SessionConfig`.
    *   **Action:** In the `AgentContext.to_dict` method, replace the existing `session_config_dict` logic with direct access to `self.session_config` attributes (e.g., `job_role=self.session_config.job_role`, `style=self.session_config.style.value if self.session_config.style else None`, etc.).
    *   **Action:** Remove the `user_id` parameter from `__init__` and the `self.user_id` attribute assignment. Update `to_dict` to remove the `user_id` key.

3.  **Update `InterviewerAgent` (`backend/agents/interviewer.py`):** `[DONE]`
    *   **Action:** Change import: `from backend.models.interview import InterviewStyle` -> `from backend.agents.config_models import InterviewStyle`.
    *   **Action:** Remove the `interview_session_id` attribute definition (`self.interview_session_id = None`) and remove its usage within the class (e.g., in `_handle_session_start`, logging messages).
    *   **Action:** Verify the `_handle_session_start` method extracts necessary config fields (job_role, style, etc.) from the `event.data` dictionary, which should still work correctly as the keys should match the `SessionConfig` attributes.

4.  **Update `AgentSessionManager` (`backend/agents/orchestrator.py`):** `[DONE]`
    *   **Action:** Change import: `from backend.models.interview import InterviewSession` -> `from backend.agents.config_models import SessionConfig`.
    *   **Action:** Update `AgentSessionManager.__init__`:
        *   Change parameter `session_config: InterviewSession` -> `session_config: SessionConfig`.
        *   Store the passed `SessionConfig` instance as `self.session_config`.
        *   Remove `session_id: str` and `user_id: str` parameters and the `self.session_id`, `self.user_id` attribute assignments.
        *   Update the `SESSION_START` event data payload to be created from `self.session_config` (e.g., `self.session_config.dict()` if using Pydantic, otherwise manually create the dict `{"job_role": self.session_config.job_role, ...}`). Remove `session_id` from this event data.
    *   **Action:** Update `_get_agent_context`:
        *   Pass `self.session_config` (the `SessionConfig` instance) to `AgentContext`.
        *   Remove `session_id=self.session_id` and `user_id=self.user_id` arguments from the `AgentContext` constructor call.
    *   **Action:** Update `end_interview` method: Remove `session_id` from the `SESSION_END` event data and the `final_results` dictionary.
    *   **Action:** Update `get_session_stats` method: Remove `session_id` from the returned dictionary.
    *   **Action:** Update `reset_session` method: Remove `session_id` from the `SESSION_RESET` event data.
    *   **Action:** Remove any remaining internal uses of `self.session_id` or `self.user_id` (e.g., in logging).

5.  **Phase 1 Verification:** `[DONE]`
    *   **Check:** Run `grep "InterviewSession" backend/agents/base.py`. Ensure no matches remain (only `SessionConfig` should be used).
    *   **Check:** Run `grep "backend.models.interview" backend/agents/interviewer.py`. Ensure only `InterviewStyle` is *not* imported from here anymore (it should come from `config_models`).
    *   **Check:** Run `grep "backend.models.interview" backend/agents/orchestrator.py`. Ensure `InterviewSession` is *not* imported from here anymore. Verify if `InterviewStyle`/`SessionMode` are still needed/imported.
    *   **Check:** Run `grep "session_id" backend/agents/orchestrator.py`. Ensure it's only present in method signatures being *removed* or variable names related to event data being *removed*, not as an active attribute `self.session_id`.
    *   **Check:** Open `backend/agents/config_models.py`. Confirm no database/model imports.

**Phase 2: Modify Application Initialization & Service Layer**

6.  **Refactor Service Initialization (`backend/services/__init__.py`):** `[DONE]`
    *   **Action:** Remove imports for: `SessionManager as ServiceSessionManager`, `TranscriptService`, `DataManagementService`, `VectorStore`.
    *   **Action:** Remove functions: `get_session_manager`, `get_transcript_service`, `get_data_management_service`.
    *   **Action:** Ensure `get_llm_service()` exists and returns a singleton instance of the existing `LLMService` class (from `backend.services.llm_service`).
    *   **Action:** Ensure `get_event_bus()` exists and returns a singleton instance of the existing `EventBus` class (from `backend.utils.event_bus`).
    *   **Action:** Ensure `get_search_service()` exists and returns a singleton instance of `SearchService`.
    *   **Action:** Define `get_agent_session_manager()`:
        ```python
        # (Inside backend/services/__init__.py)
        from backend.agents.orchestrator import AgentSessionManager
        from backend.agents.config_models import SessionConfig
        from backend.config import get_logger
        # Assuming get_llm_service and get_event_bus are defined above
        # And potentially get_search_service if needed by AgentSessionManager directly (unlikely)

        _agent_session_manager_instance = None

        def get_agent_session_manager() -> AgentSessionManager:
            nonlocal _agent_session_manager_instance
            if _agent_session_manager_instance is None:
                logger = get_logger("AgentSessionManager") # Or pass specific logger
                llm_service = get_llm_service()
                event_bus = get_event_bus()
                default_config = SessionConfig() # Create default config
                _agent_session_manager_instance = AgentSessionManager(
                    llm_service=llm_service,
                    event_bus=event_bus,
                    logger=logger,
                    session_config=default_config
                )
                logger.info("Created singleton AgentSessionManager instance.")
            return _agent_session_manager_instance
        ```
    *   **Action:** Modify/Review the existing `initialize_services` function. Remove setup for deleted services. Ensure it correctly initializes and potentially returns/registers the singletons (`LLMService`, `EventBus`, `SearchService`, `AgentSessionManager`) needed by the application.

7.  **Update Main Application (`backend/main.py`):** `[DONE]`
    *   **Action:** Find the `@app.on_event("startup")` function. Remove the call to `init_db()`.
    *   **Action:** Remove the import `from backend.database.connection import init_db`.
    *   **Action:** Locate where services/managers are obtained (likely using `initialize_services()`). Ensure this mechanism now provides the single `AgentSessionManager`.
    *   **Action:** Add the single `AgentSessionManager` instance to FastAPI's app state during startup: `app.state.agent_manager = get_agent_session_manager()`. Import `get_agent_session_manager` from `backend.services`.
    *   **Action:** Remove API router registrations: `app.include_router(transcript_router, ...)` and `app.include_router(resource_api_router, ...)` (assuming `resource_api.py` is removed). *Keep* registration for `agent_api`.
    *   **Action:** Review `create_agent_api(app)` call - ensure it doesn't implicitly rely on removed services.

8.  **Phase 2 Verification:** `[DONE]`
    *   **Check:** Run `grep "ServiceSessionManager" backend/services/__init__.py`.
    *   **Check:** Run `grep "TranscriptService" backend/services/__init__.py`. No matches.
    *   **Check:** Run `grep "DataManagementService" backend/services/__init__.py`. No matches.
    *   **Check:** Run `grep "VectorStore" backend/services/__init__.py`. No matches.
    *   **Check:** Run `grep "get_session_manager" backend/services/__init__.py`. No non-definition matches.
    *   **Check:** Verify `get_agent_session_manager` function exists and looks correct in `backend/services/__init__.py`.
    *   **Check:** Run `grep "init_db" backend/main.py`. No matches.
    *   **Check:** Verify `app.state.agent_manager` assignment exists in `backend/main.py`.
    *   **Check:** Verify router registrations for `transcript_router` and `resource_api` are removed in `backend/main.py`.

**Phase 3: Remove Unused Services, Models & Database Components**

9.  **Delete Service Files:**
    *   **Action:** Delete `backend/services/session_manager.py`.
    *   **Action:** Delete `backend/services/transcript_service.py`.
    *   **Action:** Delete `backend/services/data_management.py`.

10. **Remove Database Model Files:**
    *   **Action:** Delete `backend/models/user.py`.
    *   **Action:** Delete `backend/models/interview.py`.
    *   **Action:** Delete `backend/models/transcript.py`.
    *   **Action:** Delete `backend/models/__init__.py`.

11. **Remove Database Connection Files:**
    *   **Action:** Delete `backend/database/connection.py`.
    *   **Action:** Check `.env` or `backend/config.py` for `DATABASE_URL` and remove it.
    *   **Action:** Search (`grep`) project-wide for `sqlalchemy` and remove unused imports.

12. **Remove Vector Store File:**
    *   **Action:** Delete `backend/utils/vector_store.py`.
    *   **Action:** Remove the import `from .vector_store import VectorStore` from `backend/utils/__init__.py`.

13. **Phase 3 Verification:** `[DONE]`
    *   **Check:** Verify the specified files and directories (`backend/services/session_manager.py`, `backend/models/`, `backend/database/`, `backend/utils/vector_store.py`, etc.) no longer exist.
    *   **Check:** Run `grep "DATABASE_URL" backend/config.py` (and check `.env`). Ensure definition is removed.
    *   **Check:** Run `grep "sqlalchemy" backend/` - review any remaining imports to ensure they are necessary.
    *   **Check:** Run `grep "VectorStore" backend/` - ensure no imports remain.

**Phase 4: Simplify API Layer**

14. **Delete Unused API Files:**
    *   **Action:** Delete `backend/api/transcript_api.py`.
    *   **Action:** Delete `backend/api/resource_api.py`.

15. **Refactor Agent API (`backend/api/agent_api.py`):**
    *   **Action:** Remove imports: `ServiceSessionManager`, `get_session_manager`, `get_db`, `User`, `backend.database.connection`.
    *   **Action:** For *every* endpoint function:
        *   Remove parameters like `manager_service: ServiceSessionManager = Depends(get_session_manager)` and `db: Session = Depends(get_db)`.
        *   Add `request: Request` as a parameter. (Import `Request` from `fastapi`).
        *   Access the agent manager using `agent_manager = request.app.state.agent_manager`.
    *   **Action:** Change the router prefix: `router = APIRouter(prefix="/sessions", tags=["sessions"])` -> `router = APIRouter(prefix="/interview", tags=["interview"])`. Update `create_agent_api` function or `main.py` registration accordingly.
    *   **Action:** Refactor `POST /sessions` endpoint:
        *   Change path decorator to `@router.post("/start", ...)`
        *   Define a Pydantic model `InterviewStartRequest`

16. **Phase 4 Verification:** `[DONE]`
    *   **Check:** Verify files `backend/api/transcript_api.py` and `backend/api/resource_api.py` are deleted.

17. **Cleanup Code:** `[DONE]`
    *   **Action:** Review files: `main.py`, `agents/*`, `services/__init__.py`, `api/agent_api.py`, `utils/*`, `config.py`.

18. **Phase 5 Verification:** `[DONE (Manual Testing Required)]`
    *   **Check:** Code is formatted and linted without errors.
    *   **Check:** Application runs.