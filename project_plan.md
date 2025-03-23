# AI Interviewer Agent - Enhanced Project Plan

## Project Overview

This project plan outlines the development roadmap for enhancing the existing AI Interviewer Agent from a minimum viable product (MVP) to a comprehensive AI-powered interview preparation system with multiple specialized agents, advanced tools, and robust data storage capabilities.

## Goals and Objectives

1. Implement a multi-agent system with specialized roles (Interview Agent, Interview Coach Agent, Skill Assessor Agent)
2. Integrate AI tools to enhance agent capabilities (Web Search, Coding Sandbox, RAG)
3. Develop robust data storage and retrieval mechanisms
4. Create a seamless user experience with real-time feedback and analytics
5. Ensure all functionality runs efficiently in a local environment

## Technology Stack

### Backend

- **Framework**: FastAPI (extending current implementation)
- **AI/ML**:
  - Google Gemini API (using gemma-3 model) for core agent functionalities
  - FAISS (CPU version) for vector search and embeddings
  - Sentence-transformers for generating embeddings
  - Local models where feasible (e.g., Kokoro TTS)
- **Agent Frameworks**:
  - Custom agent implementation with inspiration from smallagents/LlamaIndex patterns
  - Event-based communication system for inter-agent coordination
- **Database**:
  - SQLite for structured data
  - FAISS for vector embeddings
- **Speech Processing**:
  - STT: Web Speech API (browser-based) or AssemblyAI
  - TTS: Kokoro TTS (local deployment via Kokoro-FastAPI)
- **Agent Communication**:
  - Event bus pattern with direct method calls for immediate interactions
  - Shared database for persistent state
  - In-memory state management for active sessions

### Frontend

- **Framework**: Next.js (extending current implementation)
- **UI Components**: Custom React components with Tailwind CSS (maintaining current dark theme)
- **State Management**: React hooks and context
- **Client-side Integration**: API clients for backend services
- **Target Devices**: Desktop-focused design

## Development Approach

- **Testing Strategy**: Tests implemented after feature development
- **Documentation**: Separate documentation files with automatically generated API docs
- **Progress Tracking**: GitHub issues and project board
- **User Scope**: Single-user local application

## Development Roadmap

The development is organized into 9 sprints, each focusing on specific components and features:

### Sprint 1 - Core Infrastructure - COMPLETED

[x] Architecture planning and component design
[x] Set up database schemas and connections
[x] Implement core agent infrastructure (BaseAgent)
[x] Implement basic testing infrastructure
[x] Project documentation

### Sprint 2 - Interviewer Agent Enhancement - COMPLETED

[x] InterviewerAgent class enhancement

- [X] ReAct-style reasoning
- [X] Structured output format
- [X] Conversation context management
  [x] Prompt Engineering Framework
- [X] Question type templates
- [X] Context-aware prompt assembly
- [X] Prompt optimization techniques
  [x] Interview Style Customization
- [X] Four distinct interview styles
- [X] Style switching mechanism
- [X] Style-specific response handling
  [x] Adaptive Questioning
- [X] Response quality assessment
- [X] Follow-up question generation
- [X] Difficulty adjustment mechanism

### Sprint 3 - Coach Agent Implementation - COMPLETED

[x] Coach Agent class (extending BaseAgent)

- [X] Real-time feedback mechanism
- [X] Personalized coaching strategies
- [X] Performance analysis
  [x] Feedback Framework
- [X] Structured feedback templates
- [X] Actionable improvement suggestions
- [X] Positive reinforcement patterns
  [x] Response Analysis
- [X] STAR method evaluation
- [X] Communication skill assessment
- [X] Response completeness analysis

### Sprint 4 - Speech-to-Text, LLM Processing, and Text-to-Speech - COMPLETED

[x] Speech-to-Text Implementation

- [x] Web Speech API implementation for browser-based transcription
- [x] AssemblyAI integration as alternative option
- [x] Transcription error handling and fallback mechanisms
  [x] LLM Input Processing
- [x] Process transcribed text through interviewer agent
- [x] Optimize prompt handling for voice interactions
- [x] Context maintenance across voice interactions
  [x] Text-to-Speech Output
- [x] Kokoro TTS integration via Kokoro-FastAPI
- [x] Voice selection interface for different agent personas
- [x] Speech output optimization for natural-sounding responses

### Sprint 5 - API & System Integration - COMPLETED

[x] API Development
- [x] RESTful endpoints for agent interactions
- [x] Basic session tracking for local application
  
[x] System Integration
- [x] Event-driven communication architecture
- [x] Agent orchestration layer
- [x] Persistent context management
  
[x] Data Management
- [x] Interview session archiving
- [x] Performance metrics tracking
- [x] *User profile storage (ON HOLD for future implementation)*

### Sprint 6 - Skill Assessor Implementation - COMPLETED

[x] Skill Assessor Agent class (extending BaseAgent)

- [x] Skill extraction and categorization
- [x] Quantitative assessment metrics
- [x] Qualitative feedback generation
  [x] Competency Framework Integration
- [x] Technical skill evaluation
- [x] Soft skill evaluation
- [x] Job-specific competency mapping
  [x] Resource Recommendation
- [x] Web search integration for skill resources
- [x] Relevance filtering for search results

### Sprint 7 - Testing and Polish - COMPLETED

[x] Comprehensive system testing
- [x] Performance testing framework implementation
- [x] Load testing for key system operations
- [x] API endpoint testing and validation
- [x] End-to-end feature testing

[x] User experience improvements
- [x] Response time optimization
- [x] Error handling enhancements
- [x] Consistent feedback mechanisms

[x] Documentation finalization
- [x] Performance optimization documentation
- [x] Updated API documentation
- [x] System architecture documentation

[x] Performance optimization
- [x] Caching implementation for session data
- [x] Conversation history optimization
- [x] Database query optimization
- [x] Agent response caching
- [x] Resource utilization improvements

### Sprint 8: Web Search & Resource Integration (1 week) - COMPLETED

### Goals

- ✅ Implement web search API integration
- ✅ Create resource filtering and ranking
- ✅ Develop seamless resource display

### Tasks

#### 8.1 Web Search API Integration

- [x] Research and select web search API (Serper.dev or SerpAPI)
  - Selected both SerpAPI and Serper.dev with configurable provider selection
  - Implemented provider-specific API clients with proper error handling
- [x] Create API client for selected service
  - Implemented async clients for both services with rate limiting and retries
  - Added backoff mechanism for handling API errors and timeouts
- [x] Implement search query generation from skill gaps
  - Created intelligent query formulation based on skill and proficiency level
  - Added job role context to improve search relevance
- [x] Develop result parsing and filtering
  - Implemented result extraction for both API providers
  - Added filtering to remove irrelevant or low-quality results

#### 8.2 Resource Processing System

- [x] Build resource type classification (articles, courses, videos)
  - Implemented classification logic based on title, URL, and content
  - Created comprehensive domain recognition for educational platforms
- [x] Implement content relevance scoring
  - Developed multi-factor relevance scoring algorithm
  - Added domain quality assessment to prioritize reputable sources

#### 8.3 Search Query Optimization

- [x] Create query construction from skill gaps
  - Implemented semantic query generation based on skill and proficiency
- [x] Implement query refinement based on results
  - Added proficiency-level specific terminology to queries
- [x] Build fallback query strategies
  - Created fallback mechanism for failed searches with LLM-generated suggestions
- [x] Develop query logging and effectiveness tracking
  - Added logging infrastructure for search queries and results

#### 8.4 Frontend Resource Display

- [x] Design resource recommendation UI
  - Created modern, responsive SkillResources component with filtering
  - Implemented SkillCard component for displaying skills with integrated resources
- [x] Implement categorized resource presentation
  - Added resource type categorization with visual indicators
  - Implemented filtering by resource type
- [x] Create resource preview functionality
  - Added resource descriptions and relevance scoring
  - Implemented click tracking for resource visits
- [x] Build resource bookmarking and history
  - Added resource interaction tracking (clicks, feedback)
  - Implemented feedback collection for resource quality

#### 8.5 Integration with Skill Assessor

- [x] Link skill gaps to search queries
  - Updated Skill Assessor to use search service for resource retrieval
  - Integrated proficiency levels from assessment into search queries
- [x] Implement resource relevance feedback
  - Created API endpoints for collecting user feedback on resources
  - Added database models for resource tracking and feedback
- [x] Create personalized resource ranking
  - Implemented relevance scoring based on skill, proficiency, and content quality
  - Added sorting options to prioritize most relevant resources
- [x] Develop resource effectiveness tracking
  - Added metrics endpoints to evaluate resource effectiveness
  - Implemented tracking of resource interactions for future recommendations

### Accomplishments

- Created a robust `SearchService` with support for multiple search providers
- Implemented advanced resource classification and relevance scoring
- Integrated search functionality with the Skill Assessor agent
- Added intelligent caching to reduce API calls and improve performance
- Updated API endpoints to support new resource retrieval functionality
- Created comprehensive documentation for the web search integration
- Implemented unit tests for the search service
- Built frontend components for displaying and filtering resources
- Added resource feedback collection for improving future recommendations
- Implemented resource effectiveness tracking and metrics

### Deliverables

- ✅ Integrated web search functionality
- ✅ Resource processing and ranking system
- ✅ Optimized search query generation
- ✅ Interactive resource recommendation UI

---

## Sprint 9: Data Storage & Transcript Management (1-2 weeks)

### Goals

- ✅ Implement comprehensive transcript storage system
- ✅ Create transcript export and import functionality
- ✅ Enable RAG with imported transcripts

### Tasks

#### 9.1 Transcript Storage System

- [x] Design transcript data model
  - Created schema for interview Q&A pairs with metadata in `backend/models/transcript.py`
  - Implemented relationships with existing models
- [x] Implement transcript creation and updating
  - Built CRUD operations in `TranscriptService` class
  - Added automatic transcript generation at session end
- [x] Create metadata association with transcripts
  - Implemented tagging system and categorization
  - Added rich metadata fields for additional context
- [x] Develop transcript search and filtering
  - Created search and filter utilities with user and tag filtering
  - Built frontend interface for browsing and searching transcripts

#### 9.2 Embedding Storage and Retrieval

- [x] Implement FAISS for conversation embeddings
  - Optimized index configuration for local hardware in VectorStore
  - Added namespacing support for organization
- [x] Implement batch embedding processing
  - Created efficient processing pipeline for large transcripts
  - Added caching mechanisms to avoid redundant processing
- [x] Develop similarity search for past conversations
  - Built search tools for finding related content
  - Implemented relevance scoring for search results

#### 9.3 Export and Import Features

- [x] Determine optimal transcript export format
  - Designed format that includes conversation and metadata
  - Supported multiple formats: JSON, CSV, Markdown, and Text
- [x] Implement transcript export functionality
  - Created export utility for downloading conversations
  - Added format selection options in the UI
- [x] Develop transcript import functionality
  - Built import parser for uploaded conversation files
  - Created API endpoint for uploading transcripts
- [x] Build import validation and error handling
  - Implemented data integrity checks
  - Added error reporting to the frontend

#### 9.4 RAG Implementation with Past Conversations

- [x] Create embedding generation for imported conversations
  - Built processing pipeline for uploaded content
  - Implemented automatic embedding generation on import
- [x] Implement RAG context enhancement from past conversations
  - Designed prompt augmentation with relevant past exchanges
  - Created vector search utilities for context retrieval
- [x] Develop relevance scoring for retrieved conversation fragments
  - Created metrics for context relevance
  - Implemented fragment extraction for granular context
- [x] Implement user interface for viewing enhanced context
  - Built UI to display how past conversations influence responses
  - Added transcript browsing and search capabilities

### Accomplishments

- Created a comprehensive transcript storage system with `Transcript`, `TranscriptTag`, `TranscriptEmbedding`, and `TranscriptFragment` models
- Implemented a robust `TranscriptService` for CRUD operations and transcript management
- Built a `VectorStore` utility for efficient embedding storage and retrieval
- Created API endpoints for transcript management, export/import, and search
- Implemented automatic transcript generation when interview sessions end
- Developed frontend components for browsing, viewing, and managing transcripts
- Added support for multiple export/import formats (JSON, CSV, Markdown, Text)
- Implemented semantic search across transcripts with relevance scoring

### Deliverables

- ✅ Complete transcript storage and retrieval system
- ✅ Conversation export and import functionality
- ✅ RAG integration with imported conversations
- ✅ User interface for transcript management

---

## Kokoro TTS Integration

We will use the Kokoro FastAPI implementation to provide high-quality Text-to-Speech capabilities. Key integration points include:

1. **Local Deployment**: Deploy Kokoro TTS as a containerized service using the provided Docker configuration
2. **Voice Selection**: Implement voice selection UI allowing users to choose from available voices
3. **Streaming Support**: Use the streaming API for real-time speech generation during interviews
4. **Word-level Timestamps**: Leverage captioned_speech endpoint for synchronized highlighting of spoken text
5. **Performance Optimization**: Configure appropriate chunking settings based on hardware constraints

Implementation will focus on the CPU version initially, with parameters tuned for the GTX 1650 GPU if performance issues arise.

## Agent Communication Pattern (Event Bus)

Based on the LlamaIndex and smolagents documentation, we'll implement:

1. **Event-driven Architecture**: Agents communicate via typed events published to the event bus
2. **Planning Intervals**: Incorporate planning steps where agents reflect on gathered information and plan next actions
3. **ReAct Pattern**: Use the Thought-Action-Observation pattern for structured agent reasoning
4. **Telemetry**: Implement instrumentation similar to LlamaIndex for debugging and monitoring agent behavior

This approach ensures agents can operate both independently and collaboratively while maintaining clear responsibility boundaries.

## Risk Assessment and Mitigation

### Technical Risks

| Risk                       | Impact | Mitigation                                                                           |
| -------------------------- | ------ | ------------------------------------------------------------------------------------ |
| LLM API costs              | Medium | Implement caching, optimize prompts, limit token usage (within Gemini's rate limits) |
| Performance bottlenecks    | Medium | Profile early, implement async processing, optimize database queries                 |
| Integration complexity     | High   | Develop modular architecture, clear interfaces, thorough testing                     |
| Local resource constraints | High   | Optimize FAISS for CPU usage, implement batch processing, memory monitoring          |

### External Dependencies

| Dependency        | Risk Level | Mitigation                                                             |
| ----------------- | ---------- | ---------------------------------------------------------------------- |
| Google Gemini API | Low        | Stay within rate limits (30 RPM, 15000 TPM, 14400 RPD), error handling |
| Web Search APIs   | Medium     | Support multiple providers, implement caching, create fallback search  |
| Local ML models   | High       | Optimize for limited RAM/VRAM (8GB RAM, 4GB VRAM GTX 1650)             |

## Success Criteria

1. All specified agents function correctly with appropriate specialization
2. Tools (Web Search, Coding Sandbox, RAG) integrate seamlessly
3. Data storage provides reliable persistence and retrieval
4. System provides valuable, actionable feedback to users
5. Performance remains acceptable on standard consumer hardware (target: 8GB RAM, GTX 1650)
6. User experience feels cohesive and intuitive

## Future Considerations

1. Multi-user support
2. Extended language model options
3. Additional interview domains beyond technical roles
4. Advanced analytics and progress tracking
5. Integration with job application platforms

---

This document serves as a comprehensive roadmap for the enhanced AI Interviewer Agent project. Each sprint builds upon the previous work, gradually transforming the MVP into a sophisticated AI-powered interview preparation system. The plan is designed to be adaptable, allowing for adjustments based on discoveries and challenges encountered during development.
