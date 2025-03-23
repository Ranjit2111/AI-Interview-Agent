# AI Interviewer Agent - Component Relationships Guide

This document outlines the key relationships and interactions between different components of the AI Interviewer Agent system.

## Core Component Relationships

```
                            ┌──────────────────┐
                            │   Frontend UI    │
                            └─────────┬────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │      API         │
                            └─────────┬────────┘
                                      │
                                      ▼
┌──────────────┐           ┌──────────────────┐           ┌──────────────┐
│  Web Search  │◄──────────┤   Orchestrator   ├──────────►│ Speech I/O   │
└──────────────┘           └─────────┬────────┘           └──────────────┘
                                     │
                 ┌─────────────┬─────┴──────┬─────────────┐
                 │             │            │             │
                 ▼             ▼            ▼             ▼
        ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐
        │ Interviewer  │ │  Coach   │ │  Skill   │ │    Data     │
        │    Agent     │ │  Agent   │ │ Assessor │ │  Management │
        └──────────────┘ └──────────┘ └──────────┘ └─────────────┘
```

## Agent Interactions

### 1. Orchestrator & Agent Interactions

The Orchestrator manages the flow of information between agents:

- **Orchestrator → Interviewer Agent**
  - Sends interview context and configuration
  - Requests question generation
  - Forwards user responses for processing

- **Interviewer Agent → Orchestrator**
  - Returns generated questions
  - Provides response analysis
  - Indicates interview progress

- **Orchestrator → Coach Agent**
  - Forwards user responses with context
  - Requests feedback generation
  - Specifies feedback frameworks to use

- **Coach Agent → Orchestrator**
  - Returns structured feedback
  - Provides improvement suggestions
  - Identifies communication patterns

- **Orchestrator → Skill Assessor Agent**
  - Sends interview transcript for analysis
  - Requests skill identification
  - Asks for resource recommendations

- **Skill Assessor → Orchestrator**
  - Returns identified skills and proficiency levels
  - Provides resource recommendations
  - Indicates skill gaps

### 2. Event Bus Communication

The Event Bus enables asynchronous communication between components:

```
┌────────────┐                                      ┌────────────┐
│ Interviewer│                                      │   Coach    │
│   Agent    │                                      │   Agent    │
└─────┬──────┘                                      └──────┬─────┘
      │                                                    │
      │ Publish                                      Subscribe
      │ (InterviewQuestionEvent)                    (UserResponseEvent)
      ▼                                                    │
┌─────────────────────────────────────────────────────────┴─────┐
│                         Event Bus                             │
└─────────────┬───────────────────────────────┬────────────────┘
              │                               │
     Subscribe│                               │Publish
(UserResponseEvent)                           │(SkillAssessmentEvent)
              │                               │
              ▼                               ▼
      ┌──────────────┐                ┌──────────────┐
      │ Skill        │                │ Frontend     │
      │ Assessor     │                │ Components   │
      └──────────────┘                └──────────────┘
```

## Frontend-Backend Integration

### 1. Frontend to API Communication

- **Frontend Pages → API Endpoints**
  - Interview page → Agent API
  - Skills page → Resource API
  - Speech components → Speech API

- **API Response Flow**
  - API endpoints format data for frontend consumption
  - Structured JSON responses with typed schemas
  - Real-time updates via WebSockets when applicable

### 2. Component Communication

```
┌──────────────────────────────────────┐
│            Frontend                  │
│  ┌────────────┐      ┌────────────┐  │
│  │ SpeechInput├─────►│ Interview  │  │
│  └────────────┘      │ Component  │  │
│                      └──────┬─────┘  │
│  ┌────────────┐             │        │
│  │SpeechOutput│◄────────────┘        │
│  └────────────┘                      │
└──────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────┐
│            Backend API               │
│                                      │
│  ┌────────────┐      ┌────────────┐  │
│  │ Speech API ├─────►│  Agent API │  │
│  └────────────┘      └──────┬─────┘  │
│                             │        │
│  ┌────────────┐             │        │
│  │ResourceAPI │◄────────────┘        │
│  └────────────┘                      │
└──────────────────────────────────────┘
```

## Web Search Integration

### 1. Skill Assessor to Search Service Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Skill Assessor │    │  Search Service │    │  Search APIs    │
│                 │    │                 │    │                 │
│ 1. Identify     │───►│ 3. Formulate    │───►│ 5. Execute      │
│    skill gaps   │    │    search query │    │    search query │
│                 │    │                 │    │                 │
│ 2. Determine    │    │ 4. Select       │    │ 6. Return       │
│    proficiency  │    │    provider     │    │    results      │
│                 │    │                 │    │                 │
│ 8. Process      │◄───│ 7. Process &    │◄───│                 │
│    resources    │    │    filter results    │                 │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Search Service to Frontend Flow

- **Search Service → Resource API → Frontend**
  - Resources are categorized and ranked
  - User interactions tracked for feedback
  - Results categorized by resource type (articles, videos, courses)

## Data Management Flow

### 1. Session Data Flow

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│   Agents    │        │   Session   │        │  Database   │
│             │        │   Manager   │        │             │
│ 1. Generate │───────►│ 3. Update   │───────►│ 5. Store    │
│    content  │        │    session  │        │    data     │
│             │        │    state    │        │             │
│ 2. Process  │        │ 4. Track    │        │ 6. Index    │
│    responses│        │    context  │        │    content  │
│             │        │             │        │             │
│ 8. Use      │◄───────│ 7. Retrieve │◄───────│             │
│    context  │        │    context  │        │             │
└─────────────┘        └─────────────┘        └─────────────┘
```

### 2. Vector Storage Integration

- **Content → Vector Store**
  - Interview content converted to embeddings
  - Stored in FAISS vector database
  - Used for similarity search and retrieval

## Speech Processing Integration

### 1. Speech Input/Output Flow

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Frontend   │      │  Speech API │      │  Backend    │
│ Components  │      │             │      │  Agents     │
│             │      │             │      │             │
│ 1. Capture  │─────►│ 3. Process  │─────►│ 5. Process  │
│    audio    │      │    audio    │      │    text     │
│             │      │             │      │             │
│ 2. Record   │      │ 4. Convert  │      │ 6. Generate │
│    speech   │      │    to text  │      │    response │
│             │      │             │      │             │
│ 8. Play     │◄─────│ 7. Convert  │◄─────│             │
│    audio    │      │    to speech│      │             │
└─────────────┘      └─────────────┘      └─────────────┘
```

### 2. TTS Integration

- **Kokoro TTS Integration**
  - Local deployment via Docker
  - Voice selection from available models
  - Streaming support for real-time responses

## Cross-Cutting Concerns

### 1. Logging and Telemetry

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Components │      │  Logging    │      │  Storage    │
│             │      │  System     │      │             │
│ 1. Generate │─────►│ 2. Format   │─────►│ 3. Store    │
│    logs     │      │    logs     │      │    logs     │
│             │      │             │      │             │
│ 4. Emit     │─────►│ 5. Aggregate│─────►│ 6. Index    │
│    telemetry│      │    metrics  │      │    metrics  │
└─────────────┘      └─────────────┘      └─────────────┘
```

### 2. Error Handling

- **Centralized Error Management**
  - API endpoints implement consistent error handling
  - Error propagation through event bus
  - Error logging and reporting

## Development Workflow Integration

### 1. Testing Integration

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Unit Tests │      │ Integration │      │ Performance │
│             │      │   Tests     │      │   Tests     │
│ Test        │─────►│ Test API    │─────►│ Test under  │
│ components  │      │ endpoints   │      │ load        │
│             │      │             │      │             │
│ Test        │      │ Test agent  │      │ Measure     │
│ functions   │      │ interactions│      │ metrics     │
└─────────────┘      └─────────────┘      └─────────────┘
```

### 2. Documentation Generation

- **Docs Generator Integration**
  - Automatic API documentation generation
  - Documentation for agent capabilities
  - Integration with Markdown-based docs 