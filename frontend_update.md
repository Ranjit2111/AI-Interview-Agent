# Frontend Refactoring Plan for AI Interview Coach

**Goal:** Refactor the frontend codebase to properly integrate with the backend API, enable core interview functionality, and improve maintainability, while ensuring the project remains startable using the existing `run_venv.bat` script.

**Constraint:** The startup process defined in `run_venv.bat` (including backend startup and the `npm run dev` command for the frontend) must not be altered. All changes will be internal to the frontend application code served by `next dev`.

---

## Phase 1: Setup and Configuration

*   [x] **1.1 Create API Service Module:**
    *   [x] Create a new file: `frontend/src/services/api.js`.
    *   [x] Define a `BACKEND_URL` constant inside, reading from `process.env.NEXT_PUBLIC_BACKEND_URL` or defaulting to `http://localhost:8000`.
    *   [x] Update `frontend/.env.local` to include `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`.
    *   [x] Implement helper functions within `api.js` for common API requests (e.g., `postJson`, `postFormData`, `getJson`). These should handle setting headers (like `Content-Type: application/json`), using the `BACKEND_URL`, and basic error handling (checking `res.ok` and potentially throwing errors).
*   [x] **1.2 Set up Global State Management (React Context):**
    *   [x] Create a new directory: `frontend/src/context`.
    *   [x] Create a new file: `frontend/src/context/AppContext.js`.
    *   [x] Define `AppContext` using `createContext`.
    *   [x] Create an `AppProvider` component within `AppContext.js`.
    *   [x] Define initial state within `AppProvider` using `useState` or `useReducer`. Include placeholders for:
        *   `sessionId` (null initially)
        *   `conversationHistory` ([])
        *   `isLoading` (false)
        *   `error` (null)
        *   `jobContext` ({ role: '', description: '', resume: null })
        *   `feedbackData` (null)
        *   `isSessionActive` (false)
    *   [x] Provide state values and update functions (e.g., `setSessionId`, `addMessageToHistory`, `setLoading`) through the `AppContext.Provider` value.
    *   [x] Create a custom hook `useAppContext` in `AppContext.js` for easy consumption (`return useContext(AppContext)`).
*   [x] **1.3 Integrate Context Provider:**
    *   [x] Modify `frontend/pages/_app.js`.
    *   [x] Import `AppProvider` from `frontend/src/context/AppContext.js`.
    *   [x] Wrap the `<Component {...pageProps} />` inside `<AppProvider>`.

## Phase 2: Component Refactoring

*   [x] **2.1 Refactor `index.js`:**
    *   [x] Modify `frontend/pages/index.js`.
    *   [x] Remove most state management (`useState`) related to session, conversation, job context, loading, errors. Keep local UI state (like scroll behavior, navbar visibility).
    *   [x] Import `useAppContext` hook.
    *   [x] Access global state and updater functions from the context where needed (e.g., `const { isLoading, error } = useAppContext();`).
*   [x] **2.2 Create `SetupForm` Component:**
    *   [x] Create a new file: `frontend/components/SetupForm.js`.
    *   [x] Move the JSX and logic for the "Setup Section" from `index.js` into `SetupForm.js`.
    *   [x] Manage local form input state (`jobRole`, `jobDescription`, `resumeFile`) within `SetupForm.js`.
    *   [x] Import and use `useAppContext` to access `setJobContext`, `setSessionId`, `setLoading`, `setError`, `setIsSessionActive`.
    *   [x] Import the API service functions from `frontend/src/services/api.js`.
    *   [x] Modify the `handleSubmitContext` function (now inside `SetupForm.js`):
        *   [x] Use the API service function to call the *correct* backend endpoint for initiating a session (e.g., `/api/agents/session/start`). This endpoint should accept job role, description, and resume, and return a `session_id`.
        *   [x] On successful response:
            *   [x] Update the global context with the received `session_id`, `jobContext`, and set `isSessionActive` to true.
            *   [x] Clear any previous errors.
            *   [x] Handle navigation/scrolling to the interview section. (Note: Scrolling handled in index.js for now)
        *   [x] On error:
            *   [x] Update the global context with the error message.
        *   [x] Manage `isLoading` state via context.
    *   [x] Replace the setup section JSX in `index.js` with `<SetupForm />`.
*   [x] **2.3 Create `InterviewChatWindow` Component:**
    *   [x] Create a new file: `frontend/components/InterviewChatWindow.js`.
    *   [x] Move the JSX and logic for the "Interview Section" from `index.js` into `InterviewChatWindow.js`.
    *   [x] Manage local input state (`userInput`) within `InterviewChatWindow.js`.
    *   [x] Import and use `useAppContext` to access `sessionId`, `conversationHistory`, `isLoading`, `error`, `addMessageToHistory`, `setLoading`, `setError`, `isSessionActive`.
    *   [x] Import the API service functions.
    *   [x] Display messages from `conversationHistory` (mapping over the array).
    *   [x] Modify the `handleSubmitInterview` function (now inside `InterviewChatWindow.js`):
        *   [x] Check if `isSessionActive` and `sessionId` exist in context. If not, show an error/message.
        *   [x] Add the user's message to `conversationHistory` via context.
        *   [x] Set `isLoading` to true via context.
        *   [x] Use the API service function to call the backend endpoint for sending a message within a session (e.g., `/api/agents/session/{sessionId}/chat`). Send the `userInput`.
        *   [x] On successful response:
            *   [x] Add the agent's response message to `conversationHistory` via context.
            *   [x] Handle potential audio output (`SpeechOutput` component) if enabled.
        *   [x] On error:
            *   [x] Update the global context with the error message.
        *   [x] Set `isLoading` to false via context.
    *   [x] Integrate `SpeechInput` and `SpeechOutput` components, connecting them to the message handling logic and context state.
    *   [x] Replace the interview section JSX in `index.js` with `<InterviewChatWindow />`.
*   [x] **2.4 Create `FeedbackDisplay` Component:**
    *   [x] Create a new file: `frontend/components/FeedbackDisplay.js`.
    *   [x] Move the JSX and logic for the "Feedback Section" from `index.js` into `FeedbackDisplay.js`.
    *   [x] Import and use `useAppContext` to access `sessionId`, `feedbackData`, `isLoading`, `error`, `setFeedbackData`, `setLoading`, `setError`, `isSessionActive`.
    *   [x] Import the API service functions.
    *   [x] Add logic (e.g., a "Get Feedback" button or trigger it automatically when `isSessionActive` becomes false) to call a backend endpoint to fetch feedback for the current `sessionId` (e.g., `/api/agents/session/{sessionId}/feedback`).
    *   [x] On successful response:
        *   [x] Update `feedbackData` in the global context.
    *   [x] Modify the component to display the actual data from `feedbackData` instead of hardcoded values. Handle the case where `feedbackData` is null.
    *   [x] Replace the feedback section JSX in `index.js` with `<FeedbackDisplay />`.

## Phase 3: Refinement and Testing

*   [x] **3.1 Update UI/UX:**
    *   [x] Replace all `alert()` calls with user-friendly inline messages or a notification system, using the `error` state from the context.
    *   [x] Ensure `isLoading` state from context is used consistently to disable buttons and show loading indicators in all relevant components (`SetupForm`, `InterviewChatWindow`, `FeedbackDisplay`).
    *   [x] Review transitions between sections and ensure smooth user flow.
*   [x] **3.2 Testing:** (Manual step for USER)
    *   [x] Thoroughly test the end-to-end flow: Setup -> Interview (multiple turns) -> Feedback.
    *   [x] Test error handling (e.g., backend down, invalid input).
    *   [x] Test with and without speech input/output enabled.
    *   [x] Test resume upload.
    *   [x] Verify the application still starts correctly using `run_venv.bat`.

--- 