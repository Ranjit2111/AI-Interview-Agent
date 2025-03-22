# API Contracts Documentation

This document outlines the API contracts between the frontend and backend of the AI Interviewer Agent system. It details the available endpoints, request formats, response structures, and expected behaviors.

## Base URL

The API base URL for local development is: `http://localhost:8000`

## Authentication

Currently, the application is designed for single-user local usage, so no authentication is required.

## API Endpoints

### Interview Session Management

#### Start a New Interview Session

- **Endpoint**: `/api/interview/start`
- **Method**: `POST`
- **Description**: Initializes a new interview session with the specified parameters.
- **Request Body**:
  ```json
  {
    "job_role": "Software Engineer",
    "job_description": "We're looking for a full-stack developer with 3+ years experience in React and Node.js...",
    "interview_style": "formal",
    "user_id": "local_user"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "e7c3a8d6-5e44-4c9a-b65e-f9c3a8d65e44",
    "message": "Interview session started successfully"
  }
  ```
- **Status Codes**:
  - `201 Created`: Session successfully created
  - `400 Bad Request`: Invalid parameters
  - `500 Internal Server Error`: Server error

#### Send Message to Interview System

- **Endpoint**: `/api/interview/message`
- **Method**: `POST`
- **Description**: Sends a user message to the interview system and receives a response.
- **Request Body**:
  ```json
  {
    "session_id": "e7c3a8d6-5e44-4c9a-b65e-f9c3a8d65e44",
    "message": "I have 5 years of experience working with React in a fintech environment...",
    "message_type": "text"
  }
  ```
- **Response**:
  ```json
  {
    "message_id": "m123456",
    "response": "That's impressive experience. Can you tell me about a specific challenge you faced in your fintech work and how you solved it?",
    "feedback": "Good detail on your experience. Consider using the STAR method to structure your answers.",
    "additional_data": {
      "response_type": "question",
      "difficulty": 3,
      "feedback_type": "structural"
    }
  }
  ```
- **Status Codes**:
  - `200 OK`: Message processed successfully
  - `400 Bad Request`: Invalid parameters or session not found
  - `500 Internal Server Error`: Server error

#### End Interview Session

- **Endpoint**: `/api/interview/end`
- **Method**: `POST`
- **Description**: Ends an active interview session and returns summary information.
- **Request Body**:
  ```json
  {
    "session_id": "e7c3a8d6-5e44-4c9a-b65e-f9c3a8d65e44"
  }
  ```
- **Response**:
  ```json
  {
    "session_summary": {
      "duration_minutes": 15,
      "questions_count": 8,
      "overall_rating": 4.2,
      "top_strengths": ["Technical knowledge", "Problem-solving approach"],
      "improvement_areas": ["Conciseness", "STAR structure"]
    },
    "message": "Interview session ended successfully"
  }
  ```
- **Status Codes**:
  - `200 OK`: Session ended successfully
  - `404 Not Found`: Session not found
  - `500 Internal Server Error`: Server error

### Agent Control

#### Switch Active Agent

- **Endpoint**: `/api/interview/switch-agent`
- **Method**: `POST`
- **Description**: Changes which agent is actively responding.
- **Request Body**:
  ```json
  {
    "session_id": "e7c3a8d6-5e44-4c9a-b65e-f9c3a8d65e44",
    "agent_type": "coach"
  }
  ```
- **Response**:
  ```json
  {
    "active_agent": "coach",
    "message": "Active agent switched successfully"
  }
  ```
- **Status Codes**:
  - `200 OK`: Agent switched successfully
  - `400 Bad Request`: Invalid agent type
  - `404 Not Found`: Session not found
  - `500 Internal Server Error`: Server error

#### Switch Orchestrator Mode

- **Endpoint**: `/api/interview/switch-mode`
- **Method**: `POST`
- **Description**: Changes the orchestrator mode to adjust how multiple agents respond.
- **Request Body**:
  ```json
  {
    "session_id": "e7c3a8d6-5e44-4c9a-b65e-f9c3a8d65e44",
    "mode": "full_feedback"
  }
  ```
- **Response**:
  ```json
  {
    "mode": "full_feedback",
    "active_agents": ["interviewer", "coach", "skill_assessor"],
    "message": "Mode switched successfully"
  }
  ```
- **Status Codes**:
  - `200 OK`: Mode switched successfully
  - `400 Bad Request`: Invalid mode
  - `404 Not Found`: Session not found
  - `500 Internal Server Error`: Server error

### Context Management

#### Submit Job Context

- **Endpoint**: `/submit-context`
- **Method**: `POST`
- **Description**: Uploads job role, description, and resume for context setting.
- **Request Format**: `multipart/form-data`
- **Form Fields**:
  - `job_role` (string, required): The job role being interviewed for
  - `job_description` (string, optional): The job description
  - `resume_file` (file, optional): PDF or DOCX resume file
- **Response**:
  ```json
  {
    "message": "Successfully processed context. Job Role: Software Engineer, Resume length: 2500 characters"
  }
  ```
- **Status Codes**:
  - `200 OK`: Context submitted successfully
  - `400 Bad Request`: Invalid parameters or file format
  - `500 Internal Server Error`: Server error

### Interview Generation

#### Generate Interview Question

- **Endpoint**: `/generate-interview`
- **Method**: `POST`
- **Description**: Generates an adaptive interview question based on context.
- **Request Body**:
  ```json
  {
    "user_input": "I have worked with React, Angular, and Vue.js in the past 5 years.",
    "job_role": "Frontend Developer",
    "job_description": "Looking for someone experienced in modern JavaScript frameworks."
  }
  ```
- **Response**:
  ```json
  {
    "generated_text": "That's a good range of framework experience. Can you describe a specific project where you had to choose between these frameworks and what factors influenced your decision?"
  }
  ```
- **Status Codes**:
  - `200 OK`: Question generated successfully
  - `400 Bad Request`: Invalid parameters
  - `500 Internal Server Error`: Server error or API key missing

### Audio Processing

#### Process Audio Input

- **Endpoint**: `/process-audio`
- **Method**: `POST`
- **Description**: Transcribes an audio file and returns a response.
- **Request Format**: `multipart/form-data`
- **Form Fields**:
  - `audio_file` (file, required): Audio file in WAV format
- **Response**:
  ```json
  {
    "audio_url": "/audio/output_a1b2c3.wav",
    "transcription": "I believe my experience with distributed systems makes me a strong candidate for this position."
  }
  ```
- **Status Codes**:
  - `200 OK`: Audio processed successfully
  - `400 Bad Request`: No audio file provided or invalid format
  - `500 Internal Server Error`: Server error

#### Get Audio File

- **Endpoint**: `/audio/{filename}`
- **Method**: `GET`
- **Description**: Retrieves a generated audio file.
- **Path Parameters**:
  - `filename` (string, required): Name of the audio file
- **Response**: Audio file (WAV)
- **Status Codes**:
  - `200 OK`: File returned successfully
  - `404 Not Found`: Audio file not found
  - `500 Internal Server Error`: Server error

## Data Models

### Interview Style Enum

- `formal`: Professional, structured interview style
- `casual`: Conversational, relaxed interview style
- `aggressive`: Challenging, pressure-testing interview style
- `technical`: Focused on technical knowledge and problem-solving

### Orchestrator Modes

- `interview_only`: Only the interviewer agent responds
- `interview_with_coaching`: Interviewer asks questions with real-time coaching feedback
- `coaching_only`: Only the coach provides feedback on responses
- `skill_assessment`: Focused on assessing specific skills
- `full_feedback`: All agents respond with comprehensive feedback

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

Common error scenarios:
- Missing required fields
- Invalid session ID
- API key not configured
- File processing errors
- Server execution errors

## WebSocket Support (Future)

Real-time feedback and notifications will be implemented via WebSockets in a future update.

---

This API contract documentation will evolve as new features are implemented. All endpoints and data models are subject to change during development. 