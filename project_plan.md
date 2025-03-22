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

The development is organized into 8 sprints, each focusing on specific components and features:

---

## Sprint 1: Project Setup & Architecture Enhancement (1 week)

### Goals

- Refine project architecture to support multi-agent system
- Set up the necessary database infrastructure
- Develop core agent interfaces

### Tasks

#### 1.1 Architecture Planning

- [ ] Review current codebase and identify integration points
- [ ] Create detailed system architecture diagram
- [ ] Define agent communication protocols and data flow
- [ ] Document API contracts between frontend and backend

#### 1.2 Database Setup

- [ ] Set up SQLite database for structured data
  - Create schemas for user profiles, interview sessions, Q&A pairs
  - Implement ORM models using SQLAlchemy
- [ ] Initialize FAISS vector database structure (CPU version)
  - Define embedding dimensions and indexing strategy (384 dimensions for all-MiniLM-L6-v2)
  - Create utilities for adding, searching, and managing vectors
  - Implement memory optimization for 8GB RAM constraint
  - Use IndexFlatL2 for exact search to start with

#### 1.3 Core Agent Infrastructure

- [ ] Design base agent class with common functionalities
  - Implement message parsing and handling (inspired by smallagents pattern)
  - Create context management for maintaining conversation state
  - Implement planning intervals for agent reflection (like smallagents planning_interval)
- [ ] Set up event bus for agent communication
  - Create pub/sub mechanisms for agent messages
  - Implement event serialization and deserialization
- [ ] Implement agent factory pattern for creating different agent types
- [ ] Implement agent registry for accessing agents by type
- [ ] Create telemetry and instrumentation system (inspired by LlamaIndex)

#### 1.4 Testing Infrastructure

- [ ] Create testing framework for agent behaviors
- [ ] Set up integration test environment
- [ ] Implement mock services for external APIs

#### 1.5 Project Documentation

- [ ] Update README with architecture details
- [ ] Create developer documentation for agent system
- [ ] Document database schemas and access patterns
- [ ] Set up automated API documentation generation

### Deliverables

- System architecture document and diagrams
- Functional database connections (SQLite and FAISS)
- Base agent infrastructure code with event bus communication
- Testing framework for agent behaviors
- Updated project documentation

---

## Sprint 2: Interview Agent Implementation (1-2 weeks)

### Goals

- Implement the core Interview Agent with dynamic questioning capabilities
- Develop structured prompt engineering for Gemini API
- Create interview style selection functionality

### Tasks

#### 2.1 Interview Agent Core Development

- [ ] Design the Interview Agent class extending base agent
  - Implement ReAct-style reasoning (Thought, Action, Observation pattern from LlamaIndex)
  - Create structured output format for consistent responses
- [ ] Implement conversation context management
  - Create memory system for tracking conversation history
  - Implement context windowing for token management
- [ ] Create question generation logic based on job context
- [ ] Develop response analysis for adaptive questioning
- [ ] Implement Gemini API rate limit handling (30 RPM, 15000 TPM, 14400 RPD)
  - Add backoff mechanisms and retry logic
  - Implement token counting for input prompts

#### 2.2 Prompt Engineering Framework

- [ ] Create structured prompt templates for different question types
  - Use template approach with placeholders for dynamic content
- [ ] Build prompt assembly pipeline based on context
  - Implement automatic assembly of context, history, and query
- [ ] Implement prompt optimization techniques
  - Create prompt compression methods for reducing token usage
- [ ] Design system for tracking prompt effectiveness
  - Build evaluation metrics for prompt quality

#### 2.3 Interview Style Customization

- [ ] Implement four interview styles:
  - Formal style prompt templates
  - Casual style prompt templates
  - Aggressive style prompt templates
  - Technical-heavy style prompt templates
- [ ] Create style switching mechanism
  - Implement state machine for interview style tracking
- [ ] Implement style-specific response handling
  - Create specialized prompts for each style

#### 2.4 Adaptive Questioning

- [ ] Develop response quality assessment
  - Create metrics for evaluating completeness and relevance
- [ ] Create follow-up question generation
  - Implement logic for identifying gaps in responses
- [ ] Implement difficulty adjustment based on user performance
  - Build scoring system for user responses
- [ ] Build context-aware question sequencing
  - Create interview flow management system

#### 2.5 Frontend Integration

- [ ] Update interview UI to support style selection
- [ ] Implement interview style indicators
- [ ] Create frontend components for displaying adaptive questions
- [ ] Add visual indicators for question difficulty level

### Deliverables

- Fully functional Interview Agent with dynamic questioning
- Interview style selection UI and backend implementation
- Adaptive questioning system based on user responses
- Documentation for prompt engineering techniques
- Gemini API integration with rate limit management

---

## Sprint 3: Interview Coach Agent & Real-time Feedback (1-2 weeks)

### Goals

- Implement the Interview Coach Agent for real-time feedback
- Create feedback display in the frontend
- Develop STAR format analysis

### Tasks

#### 3.1 Interview Coach Agent Development

- [ ] Design the Interview Coach Agent class
  - Implement feedback analysis logic
  - Create scoring mechanisms for responses
- [ ] Implement response analysis using STAR format
  - Build pattern recognition for STAR components
  - Create validation logic for each component
- [ ] Create feedback generation for various response aspects
  - Implement constructive feedback templates
- [ ] Develop constructive suggestion mechanisms
  - Create contextual suggestion generation

#### 3.2 Real-time Feedback System

- [ ] Build concurrent feedback processing pipeline
  - Implement asynchronous feedback generation
- [ ] Create real-time feedback delivery system
  - Implement WebSocket or polling mechanism for updates
- [ ] Implement feedback prioritization based on severity
  - Create severity scoring for different feedback types
- [ ] Develop feedback categorization (structure, content, delivery)
  - Build classification system for feedback types

#### 3.3 STAR Analysis Framework

- [ ] Implement detection of Situation, Task, Action, Result components
  - Create NLP analysis for identifying STAR elements
- [ ] Create scoring system for each STAR component
  - Implement weighted scoring based on completeness
- [ ] Develop suggestions for improving weak components
  - Build template-based suggestions for each component
- [ ] Build examples of well-structured responses
  - Create examples database for reference

#### 3.4 Frontend Feedback Display

- [ ] Design and implement chat-like feedback UI
- [ ] Create visual indicators for feedback categories
- [ ] Implement expandable feedback details
- [ ] Add interactive feedback acknowledgment

#### 3.5 Integration with Interview Agent

- [ ] Connect agents through the event bus system
  - Create event topics for feedback exchange
- [ ] Implement shared context between agents
  - Develop context synchronization mechanism
- [ ] Develop synchronized feedback timing with question flow
  - Create feedback scheduling based on interview state
- [ ] Build mechanisms for feedback to influence future questions
  - Implement feedback-driven question adaptation

### Deliverables

- Functional Interview Coach Agent with real-time feedback capabilities
- STAR format analysis system
- Interactive feedback display in the frontend
- Integrated agent communication system via event bus

---

## Sprint 4: Skill Assessor Agent & Analysis (1-2 weeks)

### Goals

- Implement the Skill Assessor Agent for identifying skill gaps
- Develop transcript analysis capabilities
- Create learning resource recommendation system

### Tasks

#### 4.1 Skill Assessor Agent Development

- [ ] Design the Skill Assessor Agent class
  - Implement skill gap analysis logic
- [ ] Implement transcript processing and analysis
  - Create text processing pipeline for transcripts
- [ ] Create skill categorization framework
  - Develop taxonomy of technical and soft skills
- [ ] Develop skill gap detection algorithms
  - Implement pattern matching for skill identification

#### 4.2 Pattern Recognition System

- [ ] Build pattern recognition for recurring issues
  - Implement statistical analysis for response patterns
- [ ] Implement technical depth assessment
  - Create depth scoring for technical responses
- [ ] Create specificity and relevance scoring
  - Develop metrics for response specificity
- [ ] Develop competency mapping to job requirements
  - Create job requirement parser and matcher

#### 4.3 Learning Resource Recommendation

- [ ] Design resource recommendation system
  - Create recommendation algorithm based on gaps
- [ ] Create resource categorization framework
  - Develop taxonomy for learning resources
- [ ] Implement relevance ranking for resources
  - Build scoring system for resource relevance
- [ ] Develop resource storage and retrieval
  - Create database schema for resources

#### 4.4 Frontend Integration

- [ ] Design and implement skill assessment display
- [ ] Create visual representation of skill gaps
- [ ] Implement resource recommendation UI
- [ ] Build interactive skill improvement planning

#### 4.5 Integration with Other Agents

- [ ] Connect skill assessor to other agents via event bus
  - Create event topics for skill information
- [ ] Implement influence of skill assessment on question generation
  - Develop question adaptation based on gaps
- [ ] Develop coordinated feedback between coach and assessor
  - Create feedback enrichment with skill context
- [ ] Build unified skill development tracking
  - Implement progress tracking system

### Deliverables

- Functional Skill Assessor Agent with gap analysis
- Pattern recognition system for identifying weaknesses
- Learning resource recommendation system
- Integrated skill assessment UI

---

## Sprint 5: Web Search & Resource Integration (1 week)

### Goals

- Implement web search API integration
- Create resource filtering and ranking
- Develop seamless resource display

### Tasks

#### 5.1 Web Search API Integration

- [ ] Research and select web search API (Serper.dev or SerpAPI)
  - Evaluate options based on cost, limits, and capabilities
- [ ] Create API client for selected service
  - Implement rate limiting and error handling
- [ ] Implement search query generation from skill gaps
  - Create query formulation logic
- [ ] Develop result parsing and filtering
  - Build content extraction and cleaning

#### 5.2 Resource Processing System

- [ ] Build resource type classification (articles, courses, videos)
  - Implement content type detection
- [ ] Implement content relevance scoring
  - Create relevance metrics based on content and query
- [ ] Create resource metadata extraction
  - Build metadata parser for different content types
- [ ] Develop resource storage in database
  - Create database schema for resources

#### 5.3 Search Query Optimization

- [ ] Create query construction from skill gaps
  - Implement semantic query generation
- [ ] Implement query refinement based on results
  - Build query expansion and narrowing logic
- [ ] Build fallback query strategies
  - Create alternative query patterns
- [ ] Develop query logging and effectiveness tracking
  - Implement metrics for query success

#### 5.4 Frontend Resource Display

- [ ] Design resource recommendation UI
- [ ] Implement categorized resource presentation
- [ ] Create resource preview functionality
- [ ] Build resource bookmarking and history

#### 5.5 Integration with Skill Assessor

- [ ] Link skill gaps to search queries
  - Create mapping between gaps and query types
- [ ] Implement resource relevance feedback
  - Build feedback mechanism for resource quality
- [ ] Create personalized resource ranking
  - Develop user preference learning
- [ ] Develop resource effectiveness tracking
  - Implement usage and benefit tracking

### Deliverables

- Integrated web search functionality
- Resource processing and ranking system
- Optimized search query generation
- Interactive resource recommendation UI

---

## Sprint 6: Coding Sandbox Environment (2 weeks)

### Goals

- Implement coding sandbox for technical assessment
- Create code evaluation system
- Develop coding challenge generation

### Tasks

#### 6.1 Coding Sandbox Backend

- [ ] Research and select code execution approach (custom FastAPI service or third-party API)
  - Evaluate security implications of each approach
- [ ] Implement secure code execution environment
  - Create containerized execution if using custom solution
- [ ] Create language support for Python (extensible to others)
  - Implement language-specific execution environments
- [ ] Develop input/output handling for code testing
  - Create standardized I/O interface

#### 6.2 Code Challenge Generation

- [ ] Create challenge templates for different difficulty levels
  - Build template database with difficulty tags
- [ ] Implement challenge selection based on job requirements
  - Create job requirement to challenge mapping
- [ ] Develop test case generation for challenges
  - Implement automatic test case creation
- [ ] Build solution evaluation criteria
  - Create scoring rubrics for different challenge types

#### 6.3 Code Evaluation System

- [ ] Implement code execution and result capture
  - Build execution pipeline with timeout handling
- [ ] Create evaluation against test cases
  - Implement test runner and result compiler
- [ ] Develop code quality assessment
  - Integrate static analysis tools
- [ ] Build performance metrics calculation
  - Implement runtime and memory usage tracking

#### 6.4 Frontend Coding UI

- [ ] Design and implement code editor component
  - Integrate syntax highlighting and code completion
- [ ] Create test case display and results visualization
  - Build test result explorer
- [ ] Implement real-time syntax highlighting
  - Integrate Monaco editor or similar
- [ ] Build code execution control UI
  - Create execution status and control panel

#### 6.5 Integration with Interview Agent

- [ ] Link technical questions to coding challenges
  - Create mapping between question types and challenges
- [ ] Implement coding challenge difficulty adjustment
  - Build adaptive difficulty based on performance
- [ ] Create context-aware challenge selection
  - Implement selection logic based on conversation
- [ ] Develop coding performance feedback integration
  - Connect code performance to interview feedback

### Deliverables

- Functional coding sandbox environment
- Code challenge generation system
- Code execution and evaluation pipeline
- Interactive coding UI integrated with interview flow

---

## Sprint 7: RAG & Knowledge Base Implementation (1-2 weeks)

### Goals

- Implement Retrieval-Augmented Generation (RAG) system
- Create local knowledge base
- Develop embedding-based information retrieval

### Tasks

#### 7.1 Knowledge Base Setup

- [ ] Design knowledge base structure
  - Create schema for documents and metadata
- [ ] Collect and organize technical articles and interview resources
  - Gather domain-specific content for different roles
- [ ] Create knowledge categorization system
  - Implement topic and domain tagging
- [ ] Implement knowledge base management utilities
  - Build tools for adding and updating content

#### 7.2 Embedding System Implementation

- [ ] Set up embedding model (all-MiniLM-L6-v2 via sentence-transformers)
  - Configure for CPU optimization
- [ ] Create embedding generation pipeline
  - Implement batched processing for efficiency
- [ ] Implement vector storage in FAISS (CPU optimized)
  - Configure index parameters for CPU usage
- [ ] Develop vector search and retrieval with memory optimization
  - Implement paged loading for large indices

#### 7.3 RAG Integration with Gemini

- [ ] Design RAG-enhanced prompt structure
  - Create prompt templates with context insertion
- [ ] Implement knowledge retrieval for prompt enhancement
  - Build context selection and formatting
- [ ] Create relevance scoring for retrieved knowledge
  - Implement result ranking and filtering
- [ ] Develop knowledge fusion into prompts
  - Create context integration strategies

#### 7.4 Query Understanding and Processing

- [ ] Implement query embedding generation
  - Create optimized query processing
- [ ] Create semantic search for knowledge retrieval
  - Implement similarity search with thresholds
- [ ] Develop query expansion techniques
  - Build query reformulation logic
- [ ] Build query-specific knowledge filtering
  - Create content type and domain filtering

#### 7.5 Performance Optimization

- [ ] Implement caching for common queries
  - Create LRU cache for query results
- [ ] Create batch processing for embeddings
  - Implement efficient batching for CPU
- [ ] Develop index optimization for FAISS
  - Configure index parameters for speed
- [ ] Build performance monitoring for RAG system
  - Implement timing and resource usage tracking

### Deliverables

- Functional RAG system with local knowledge base
- Embedding generation and search pipeline
- Knowledge retrieval and fusion with Gemini prompts
- Optimized performance for real-time use within hardware constraints

---

## Sprint 8: Data Storage, Transcript Management & Final Integration (1-2 weeks)

### Goals

- Implement comprehensive data storage system
- Create transcript management features
- Finalize system integration
- Conduct thorough testing

### Tasks

#### 8.1 Transcript Storage System

- [ ] Design transcript data model
  - Create schema for Q&A pairs and metadata
- [ ] Implement transcript creation and updating
  - Build CRUD operations for transcripts
- [ ] Create metadata association with transcripts
  - Implement tagging and categorization
- [ ] Develop transcript search and filtering
  - Create search and filter utilities

#### 8.2 Embedding Storage and Retrieval

- [ ] Finalize FAISS integration for Q&A embeddings
  - Optimize index configuration
- [ ] Implement batch embedding processing
  - Create efficient processing pipeline
- [ ] Create metadata linkage with vectors
  - Implement metadata storage with vectors
- [ ] Develop similarity search utilities
  - Build search tools with filtering

#### 8.3 Export and Import Features

- [ ] Implement plain text transcript export
  - Create formatting for readable export
- [ ] Create JSON metadata export with embeddings
  - Implement serialization for complete data
- [ ] Develop transcript import functionality
  - Build import parsers and validators
- [ ] Build import validation and error handling
  - Implement data integrity checks

#### 8.4 System Integration and Testing

- [ ] Complete end-to-end integration of all components
  - Validate all component interactions
- [ ] Conduct comprehensive system testing
  - Create test suite for complete system
- [ ] Implement error handling and recovery
  - Build robust error management
- [ ] Develop system monitoring and logging
  - Create monitoring dashboard

#### 8.5 Performance Optimization and Documentation

- [ ] Conduct performance profiling
  - Identify bottlenecks and issues
- [ ] Implement optimization for identified bottlenecks
  - Apply targeted performance improvements
- [ ] Create comprehensive user documentation
  - Write user guides and tutorials
- [ ] Develop maintenance and troubleshooting guides
  - Create system administrator documentation

### Deliverables

- Complete data storage and retrieval system
- Transcript export and import functionality
- Fully integrated and tested system
- Comprehensive documentation

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

| Dependency        | Risk Level | Mitigation                                                               |
| ----------------- | ---------- | ------------------------------------------------------------------------ |
| Google Gemini API | Low        | Stay within rate limits (30 RPM, 15000 TPM, 14400 RPD), error handling  |
| Web Search APIs   | Medium     | Support multiple providers, implement caching, create fallback search    |
| Local ML models   | High       | Optimize for limited RAM/VRAM (8GB RAM, 4GB VRAM GTX 1650)              |

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
