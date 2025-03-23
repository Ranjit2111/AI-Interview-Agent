# API Contracts Documentation

This document outlines the API contracts between the frontend and backend of the AI Interviewer Agent system. It details the available endpoints, request formats, response structures, and expected behaviors.

## Base URL

The API base URL for local development is: `http://localhost:8000`

## Authentication

Currently, the application is designed for single-user local usage, so no authentication is required.

## API Endpoints

### Interview Session Management

#### Start Interview

Starts a new interview session with the specified configuration.

- **Endpoint**: `/api/interview/start`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "job_role": "Software Engineer",
    "job_description": "Building web applications with JavaScript and React",
    "interview_style": "FORMAL",
    "mode": "interview_with_coaching",
    "user_id": "user123"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_role": "Software Engineer",
    "interview_style": "FORMAL",
    "mode": "interview_with_coaching",
    "created_at": "2023-09-15T14:30:20.123Z",
    "active_agent": "interviewer",
    "welcome_message": "Hello, I'll be interviewing you for the Software Engineer position..."
  }
  ```

#### Send Message

Sends a message to the current interview session.

- **Endpoint**: `/api/interview/send`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "message": "I have 5 years of experience with JavaScript and React.",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123"
  }
  ```
- **Response**:
  ```json
  {
    "response": "That's great! Can you tell me about a challenging project you worked on using React?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent": "interviewer",
    "timestamp": "2023-09-15T14:31:05.456Z",
    "metadata": null
  }
  ```

#### End Interview

Ends an interview session and returns metrics.

- **Endpoint**: `/api/interview/end`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "message": "Thank you for the interview.",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Thank you for participating in this interview. I hope you found it helpful.",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2023-09-15T14:40:30.789Z",
    "metrics": {
      "total_messages": 15,
      "user_message_count": 7,
      "assistant_message_count": 8,
      "average_user_message_length": 120.5,
      "average_assistant_message_length": 150.2,
      "average_response_time_seconds": 3.5,
      "conversation_duration_seconds": 600
    }
  }
  ```

#### Get Session Information

Retrieves information about a specific interview session.

- **Endpoint**: `/api/interview/info`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id`: The session identifier
- **Response**:
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_role": "Software Engineer",
    "interview_style": "FORMAL",
    "mode": "interview_with_coaching",
    "created_at": "2023-09-15T14:30:20.123Z",
    "active_agent": "interviewer"
  }
  ```

#### List Sessions

Lists active interview sessions, optionally filtered by user ID.

- **Endpoint**: `/api/interview/sessions`
- **Method**: `GET`
- **Query Parameters**:
  - `user_id` (optional): Filter sessions by user ID
- **Response**:
  ```json
  [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_role": "Software Engineer",
      "interview_style": "FORMAL",
      "mode": "interview_with_coaching",
      "created_at": "2023-09-15T14:30:20.123Z",
      "active_agent": "interviewer"
    },
    {
      "session_id": "660f9511-f30c-52e5-b827-557766551111",
      "job_role": "Data Scientist",
      "interview_style": "TECHNICAL",
      "mode": "interview_only",
      "created_at": "2023-09-15T16:45:10.456Z",
      "active_agent": "interviewer"
    }
  ]
  ```

#### Get Session Metrics

Retrieves performance metrics for a specific interview session.

- **Endpoint**: `/api/interview/metrics`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id`: The session identifier
- **Response**:
  ```json
  {
    "total_messages": 15,
    "user_message_count": 7,
    "assistant_message_count": 8,
    "average_user_message_length": 120.5,
    "average_assistant_message_length": 150.2,
    "average_response_time_seconds": 3.5,
    "conversation_duration_seconds": 600
  }
  ```

#### Get Conversation History

Retrieves the conversation history for a specific interview session.

- **Endpoint**: `/api/interview/history`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id`: The session identifier
- **Response**:
  ```json
  [
    {
      "role": "assistant",
      "agent": "interviewer",
      "content": "Hello, I'll be interviewing you for the Software Engineer position...",
      "timestamp": "2023-09-15T14:30:25.123Z"
    },
    {
      "role": "user",
      "content": "I have 5 years of experience with JavaScript and React.",
      "timestamp": "2023-09-15T14:31:00.456Z"
    },
    {
      "role": "assistant",
      "agent": "interviewer",
      "content": "That's great! Can you tell me about a challenging project you worked on using React?",
      "timestamp": "2023-09-15T14:31:05.789Z"
    }
  ]
  ```

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

### Skill Assessment

#### Start Skill Assessment

Starts a new skill assessment session or switches an existing session to skill assessment mode.

- **Endpoint**: `/api/interview/skill-assessment`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "message": "I want to assess my skills in React development",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123"
  }
  ```
- **Response**:
  ```json
  {
    "response": "I'll help you assess your React development skills. Let's start by discussing your experience with React. How long have you been working with it?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2023-09-15T14:35:20.123Z",
    "mode": "skill_assessment"
  }
  ```

#### Get Skills

Retrieves the skills assessed in an interview session.

- **Endpoint**: `/api/interview/skills`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id`: The session identifier
- **Response**:
  ```json
  [
    {
      "skill_name": "React",
      "category": "framework",
      "proficiency": 4,
      "feedback": "Demonstrates strong understanding of React component architecture and state management",
      "resources": [
        {
          "title": "Advanced React Patterns",
          "url": "https://www.example.com/courses/advanced-react-patterns",
          "description": "Learn advanced React patterns to level up your development skills",
          "resource_type": "online_course",
          "relevance_score": 5
        }
      ]
    },
    {
      "skill_name": "JavaScript",
      "category": "language",
      "proficiency": 3,
      "feedback": "Good grasp of JavaScript fundamentals, could improve on advanced concepts",
      "resources": [
        {
          "title": "JavaScript: The Hard Parts",
          "url": "https://www.example.com/courses/javascript-hard-parts",
          "description": "Deep dive into JavaScript concepts like closures and prototypal inheritance",
          "resource_type": "online_course",
          "relevance_score": 4
        }
      ]
    }
  ]
  ```

#### Get Skill Profile

Retrieves a comprehensive skill profile for an interview session.

- **Endpoint**: `/api/interview/skill-profile`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id`: The session identifier
- **Response**:
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_role": "Frontend Developer",
    "skills": [
      {
        "skill_name": "React",
        "category": "framework",
        "proficiency": 4,
        "feedback": "Demonstrates strong understanding of React component architecture and state management",
        "resources": [...]
      },
      {
        "skill_name": "JavaScript",
        "category": "language",
        "proficiency": 3,
        "feedback": "Good grasp of JavaScript fundamentals, could improve on advanced concepts",
        "resources": [...]
      }
    ],
    "strengths": ["React", "CSS", "UI Design"],
    "improvement_areas": ["TypeScript", "Testing"],
    "overall_match": 75,
    "created_at": "2023-09-15T15:00:00.000Z"
  }
  ```

#### Get Skill Resources

Retrieves resources for improving a specific skill. Uses web search integration to find relevant, up-to-date learning resources.

- **Endpoint**: `/api/interview/skill-resources`
- **Method**: `GET`
- **Query Parameters**:
  - `skill_name`: The skill to get resources for
  - `session_id`: The session identifier
  - `proficiency_level` (optional): Target proficiency level for resources (beginner, basic, intermediate, advanced, expert)
- **Response**:
  ```json
  [
    {
      "title": "Complete React Tutorial",
      "url": "https://www.example.com/courses/react",
      "description": "Comprehensive course covering all aspects of React with practical exercises",
      "resource_type": "online_course",
      "relevance_score": 0.95
    },
    {
      "title": "React Fundamentals",
      "url": "https://www.example.com/books/react-fundamentals",
      "description": "In-depth guide to React theory and practice",
      "resource_type": "book",
      "relevance_score": 0.85
    },
    {
      "title": "Getting Started with React",
      "url": "https://www.example.com/articles/react-guide",
      "description": "Beginner-friendly introduction to React",
      "resource_type": "article",
      "relevance_score": 0.75
    },
    {
      "title": "Interactive React Tutorial",
      "url": "https://www.example.com/tutorials/react",
      "description": "Step-by-step tutorial with interactive examples for learning React",
      "resource_type": "tutorial",
      "relevance_score": 0.8
    }
  ]
  ```

- **Resource Types**:
  - `online_course`: Interactive learning courses (e.g., Coursera, Udemy)
  - `book`: Books and ebooks on the topic
  - `article`: Online articles and blog posts
  - `tutorial`: Step-by-step instructional content
  - `video`: Video-based learning content
  - `documentation`: Official documentation and references
  - `community`: Forums, communities, and Q&A platforms

- **Notes**:
  - If `proficiency_level` is not provided, the system will attempt to determine the appropriate level based on the user's assessed proficiency in the skill
  - Resources are automatically scored for relevance based on matching skill name, proficiency level, and domain quality
  - Resources are categorized by type to help users find the most suitable learning format
  - Web search integration ensures resources are current and relevant

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