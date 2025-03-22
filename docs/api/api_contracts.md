# API Contracts

This document describes the API contracts for the AI Interviewer Agent.

## Overview

The AI Interviewer Agent exposes a RESTful API that allows clients to interact with the interview and coaching functionality. This document outlines the available endpoints, request/response formats, and error handling.

## Base URL

All API endpoints are relative to the base URL:

```
http://<host>:<port>/api/v1
```

## Authentication

Authentication is handled via API keys that should be included in the request headers:

```
Authorization: Bearer <api_key>
```

## Common Response Formats

### Success Response

All successful responses follow this format:

  ```json
  {
  "status": "success",
  "data": { ... }
}
```

### Error Response

All error responses follow this format:

  ```json
  {
  "status": "error",
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

## Common Error Codes

| Code | Description |
| ---- | ----------- |
| `invalid_request` | The request is malformed or missing required parameters |
| `unauthorized` | Authentication failed or insufficient permissions |
| `not_found` | The requested resource does not exist |
| `server_error` | An unexpected error occurred on the server |
| `rate_limited` | Too many requests have been made in a short period |

## Endpoints

### Interview

#### Create Interview Session

Creates a new interview session.

**Endpoint:** `POST /interviews`

**Request Body:**

  ```json
  {
  "job_role": "Software Engineer",
  "experience_level": "Senior",
  "skills": ["Python", "JavaScript", "React"],
  "interview_type": "technical",
  "duration": 30
}
```

**Response:**

  ```json
  {
  "status": "success",
  "data": {
    "interview_id": "12345",
    "created_at": "2023-06-01T12:00:00Z",
    "status": "created",
    "config": {
      "job_role": "Software Engineer",
      "experience_level": "Senior",
      "skills": ["Python", "JavaScript", "React"],
      "interview_type": "technical",
      "duration": 30
    }
  }
}
```

#### Get Interview Session

Retrieves information about an existing interview session.

**Endpoint:** `GET /interviews/{interview_id}`

**Response:**

  ```json
  {
  "status": "success",
  "data": {
    "interview_id": "12345",
    "created_at": "2023-06-01T12:00:00Z",
    "status": "in_progress",
    "config": {
      "job_role": "Software Engineer",
      "experience_level": "Senior",
      "skills": ["Python", "JavaScript", "React"],
      "interview_type": "technical",
      "duration": 30
    },
    "current_question": {
      "id": "q1",
      "text": "Explain the difference between synchronous and asynchronous programming."
    }
  }
}
```

#### Submit Answer

Submits a candidate answer to the current question.

**Endpoint:** `POST /interviews/{interview_id}/answers`

**Request Body:**

  ```json
  {
  "question_id": "q1",
  "answer": "Synchronous programming executes tasks sequentially, where each task must complete before the next one starts. Asynchronous programming allows multiple tasks to be processed concurrently without waiting for previous tasks to complete. This is particularly useful for I/O-bound operations where the program would otherwise be idle waiting for external resources."
  }
  ```

**Response:**

  ```json
  {
  "status": "success",
  "data": {
    "answer_id": "a1",
    "evaluation": {
      "score": 8,
      "feedback": "Good explanation of the core concepts. Consider providing a code example to demonstrate the difference."
    },
    "next_question": {
      "id": "q2",
      "text": "Describe a project where you used asynchronous programming and explain the benefits it provided."
    }
  }
}
```

#### End Interview

Ends the interview session and generates a summary.

**Endpoint:** `POST /interviews/{interview_id}/end`

**Response:**

  ```json
  {
  "status": "success",
  "data": {
    "interview_id": "12345",
    "status": "completed",
    "summary": {
      "overall_score": 85,
      "strengths": [
        "Technical knowledge",
        "Communication clarity"
      ],
      "areas_for_improvement": [
        "Providing concrete examples",
        "Discussing experience with specific technologies"
      ],
      "recommendations": "Focus on incorporating specific examples from your experience to support your answers."
    }
  }
}
```

### Coaching

#### Request Feedback

Requests coaching feedback on a specific answer.

**Endpoint:** `POST /coaching/feedback`

**Request Body:**

  ```json
  {
  "question": "Tell me about a time you faced a difficult technical challenge.",
  "answer": "I once had to optimize a database query that was taking several minutes to run. I analyzed the query execution plan, identified bottlenecks, and created appropriate indexes. This reduced the query time to under a second.",
  "framework": "STAR"
  }
  ```

**Response:**

  ```json
  {
  "status": "success",
  "data": {
    "feedback": {
      "overall": "Your answer provides a good overview of the situation but lacks detail in some areas.",
      "framework_analysis": {
        "situation": "Partially addressed. You mentioned a slow database query but didn't provide context about the impact.",
        "task": "Partially addressed. You implied your task was to optimize the query but didn't explain why it was assigned to you.",
        "action": "Well addressed. You described the specific steps you took to solve the problem.",
        "result": "Partially addressed. You provided a quantitative result but didn't mention the impact on the business or users."
      },
      "improvements": [
        "Add context about why the slow query was problematic",
        "Explain your role in addressing the issue",
        "Discuss the impact of your solution on users or the business"
      ]
    }
  }
}
```

#### Generate Practice Question

Generates a practice question for a specific job role and skill.

**Endpoint:** `POST /coaching/practice-questions`

**Request Body:**

  ```json
  {
  "job_role": "Data Scientist",
  "skill": "Machine Learning",
  "difficulty": "intermediate"
}
```

**Response:**

  ```json
  {
  "status": "success",
  "data": {
    "question": {
      "id": "pq1",
      "text": "Explain how you would handle imbalanced data in a classification problem. Provide specific techniques and when you would apply them."
    },
    "guidance": {
      "key_points": [
        "Definition of imbalanced data",
        "Resampling techniques (oversampling, undersampling)",
        "Algorithm-level approaches",
        "Evaluation metrics for imbalanced data"
      ],
      "structure": "Start with a brief explanation of the problem, then discuss multiple approaches, and conclude with how you would evaluate the effectiveness of your solution."
    }
  }
}
```

## Websocket API

The AI Interviewer Agent also provides a WebSocket API for real-time communication during interviews.

### Connection

Connect to the WebSocket endpoint:

```
ws://<host>:<port>/api/v1/ws/interviews/{interview_id}
```

Include the authentication token as a query parameter:

```
ws://<host>:<port>/api/v1/ws/interviews/{interview_id}?token={api_key}
```

### Message Format

All messages follow this format:

```json
{
  "type": "message_type",
  "data": { ... }
}
```

### Message Types

#### From Client

| Type | Description | Data |
| ---- | ----------- | ---- |
| `answer` | Submit an answer to the current question | `{"answer": "Text of the answer"}` |
| `request_next` | Request the next question | `{}` |
| `typing` | Indicate that the user is typing | `{"is_typing": true/false}` |

#### From Server

| Type | Description | Data |
| ---- | ----------- | ---- |
| `question` | A new question from the interviewer | `{"id": "q1", "text": "Question text"}` |
| `feedback` | Feedback on the previous answer | `{"score": 8, "feedback": "Feedback text"}` |
| `thinking` | Indication that the interviewer is thinking | `{"is_thinking": true/false}` |
| `interview_ended` | Notification that the interview has ended | `{"summary": {...}}` |

## Rate Limiting

The API enforces rate limiting to prevent abuse. The current limits are:

- 60 requests per minute per API key
- 10 concurrent WebSocket connections per API key

When rate limited, the API will return a `429 Too Many Requests` status code with a `Retry-After` header indicating when the client can try again.

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: The request was successful
- `201 Created`: A new resource was created
- `400 Bad Request`: The request is malformed or missing required parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: The authenticated user does not have permission to access the resource
- `404 Not Found`: The requested resource does not exist
- `429 Too Many Requests`: The client has sent too many requests in a given time period
- `500 Internal Server Error`: An unexpected error occurred on the server

## Versioning

The API uses versioning in the URL path (`/api/v1/`) to ensure backward compatibility as new features are added. When breaking changes are necessary, a new version will be introduced (e.g., `/api/v2/`). 