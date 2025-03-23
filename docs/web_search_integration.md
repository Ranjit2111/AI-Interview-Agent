# Web Search & Resource Integration

This document outlines the web search and resource integration feature implemented in Sprint 8 of the AI Interviewer Agent project.

## Overview

The Web Search & Resource Integration feature enhances the Skill Assessor's capability to provide relevant, up-to-date learning resources for skills identified during interviews. Instead of relying solely on pre-defined or AI-generated resource suggestions, the system now utilizes web search APIs to find current, high-quality learning resources.

## Key Components

### Search Service

The `SearchService` class (`backend/services/search_service.py`) serves as the core component of the web search integration:

- Supports multiple search providers (SerpAPI and Serper.dev)
- Implements caching to reduce API calls and improve performance
- Classifies resources by type (article, course, video, etc.)
- Scores resources based on relevance to the skill and proficiency level
- Provides fallback mechanisms if search services are unavailable

### Resource Processing

Resources retrieved from search APIs undergo a comprehensive processing pipeline:

1. **Query Generation**: Constructs optimized search queries based on skill name, proficiency level, and job role
2. **Result Filtering**: Filters out irrelevant or low-quality search results
3. **Resource Classification**: Categorizes resources into types (courses, articles, videos, etc.)
4. **Relevance Scoring**: Scores resources based on how well they match the skill, proficiency level, and educational quality
5. **Result Ranking**: Ranks resources by relevance score to present the most suitable options first

### Integration with Skill Assessor

The `SkillAssessorAgent` has been enhanced to leverage the search service:

- Updated `_get_resources_for_skill` method to use the search service
- Modified `_suggest_resources_tool` to prioritize search-based resources
- Added resource type mapping to ensure consistency with existing systems
- Implemented fallback to LLM-based resource generation if search fails

### API Endpoint Updates

The `/api/interview/skill-resources` endpoint has been enhanced:

- Added optional `proficiency_level` parameter to allow targeting resources at specific skill levels
- Improved resource relevance with better scoring algorithms
- Added automatic proficiency detection from the database

## Resource Types

The system categorizes resources into the following types:

- **Articles**: Blog posts, tutorials, and written guides
- **Courses**: Interactive learning platforms (Coursera, Udemy, etc.)
- **Videos**: Video tutorials, webinars, and recorded lectures
- **Tutorials**: Step-by-step instructional content
- **Documentation**: Official documentation and references
- **Books**: Books, ebooks, and long-form content
- **Tools**: Relevant tools and utilities for skill practice
- **Community**: Forums, communities, and Q&A platforms

## Implementation Details

### Query Construction

Queries are constructed based on the skill name and proficiency level, with optional job role context:

```python
# Example query construction
query = f"{skill} {level_term} tutorial resources"
if job_role:
    query += f" for {job_role}"
```

### Relevance Scoring

Resources are scored based on several factors:

- Presence of skill name in title (highest weight)
- Presence of skill name in URL
- Presence of skill name in description
- Mention of appropriate proficiency level terms
- Quality of the source domain
- Job role relevance

### Caching Strategy

Resource results are cached to improve performance:

- Cache TTL of 1 hour to balance freshness with API usage
- Cache keys based on query string and number of results
- Intelligent cache invalidation when service is restarted

## Usage Example

```python
# Example usage
search_service = get_search_service()
resources = await search_service.search_resources(
    skill="python",
    proficiency_level="intermediate",
    job_role="Data Scientist",
    num_results=5
)
```

## Configuration

Search providers require API keys, which should be set in environment variables:

- `SERPAPI_API_KEY`: API key for SerpAPI
- `SERPER_API_KEY`: API key for Serper.dev

The default provider can be configured in `backend/services/search_service.py`.

## Fallback Mechanism

If web search fails (due to API issues, rate limiting, etc.), the system falls back to:

1. Pre-cached resources if available
2. LLM-generated resource suggestions
3. Static generic resources for common platforms

## Future Enhancements

Planned enhancements for the web search and resource integration:

1. **Resource Saving**: Allow users to save/bookmark resources for later reference
2. **Resource Voting**: Enable feedback on resource quality to improve future recommendations
3. **Custom Resource Filters**: Allow users to filter by resource type, length, difficulty
4. **Content Previews**: Implement previews for resources when available
5. **Personalized Recommendations**: Track which resources users engage with to improve future suggestions

## Testing

Unit tests for the search service are available in `backend/tests/test_search_service.py`, covering:

- Resource object creation and serialization
- Query generation for different skills and levels
- Resource classification based on content and URL
- Relevance score calculation
- Search provider functionality (mocked for testing)
- Caching functionality
- Fallback resource generation
