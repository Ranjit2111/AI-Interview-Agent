# Skill Assessor Agent Reference Guide

## Overview

The Skill Assessor Agent is responsible for evaluating a candidate's technical and soft skills during the interview process. It identifies skills mentioned or demonstrated in responses, assesses proficiency levels, tracks skill development, suggests resources for improvement, and generates comprehensive skill profiles. This agent operates alongside the Interviewer and Coach agents, focusing specifically on skill identification and assessment.

## File Structure

```
backend/
└── agents/
    ├── skill_assessor.py       # Main SkillAssessorAgent implementation
    ├── base.py                 # BaseAgent class that SkillAssessorAgent inherits from
    └── templates/
        ├── __init__.py         # Template exports
        └── skill_templates.py  # Templates used by the skill assessor agent
```

## Key Relationships

- **Inherits from**: `BaseAgent` (defined in `backend/agents/base.py`)
- **Interacts with**: 
  - `InterviewerAgent` (through the event bus)
  - `CoachAgent` (through the event bus)
  - UI components via the event system

## Key Classes and Enums

### SkillAssessorAgent

The main agent class responsible for skill assessment functionality.

```python
class SkillAssessorAgent(BaseAgent):
    # ...implementation...
```

### ProficiencyLevel

Enum defining different levels of skill proficiency.

```python
class ProficiencyLevel(str, Enum):
    NOVICE = "novice"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
```

### SkillCategory

Enum defining different categories of skills.

```python
class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"
    PROCESS = "process"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
```

## Agent States and Lifecycle

The Skill Assessor Agent does not have explicit states like the Interviewer Agent. Instead, it continuously monitors the interview, reacting to events and building a skill profile over time.

### Key Agent Stages:

1. **Initialization**: Sets up LLM chains, tools, and preloaded skill keywords
2. **Skill Monitoring**: Listens for user responses and extracts skills
3. **Skill Assessment**: Evaluates proficiency levels for identified skills
4. **Resource Suggestion**: Recommends resources for skill improvement
5. **Profile Generation**: Creates comprehensive skill profiles at the end of interviews

## Key Methods

### Lifecycle Methods

- **`__init__`**: Initializes the skill assessor agent with configuration options
- **`_initialize_tools`**: Sets up the agent's tools for skill assessment
- **`_setup_llm_chains`**: Configures LangChain chains for the agent's tasks

### Core Logic Methods

- **`process_input`**: Processes user input and generates assessment responses
- **`_process_input_rule_based`**: Rule-based input processing fallback
- **`_extract_skills_tool`**: Tool function to extract skills from responses
- **`_assess_proficiency_tool`**: Tool function to assess skill proficiency levels
- **`_suggest_resources_tool`**: Tool function to suggest skill improvement resources
- **`_create_skill_profile_tool`**: Tool function to generate comprehensive skill profiles

### Skill Analysis Methods

- **`_identify_skills_in_text`**: Identifies skills mentioned in text
- **`_estimate_proficiency`**: Estimates proficiency level for a skill
- **`_assess_recent_answer`**: Assesses skills in the most recent answer
- **`_create_skill_update`**: Creates updates about newly identified skills
- **`_generate_skill_profile`**: Generates comprehensive skill profiles
- **`_suggest_skill_resources`**: Suggests resources for skill improvement
- **`_get_resources_for_skill`**: Gets resource recommendations for specific skills

### Event Handling Methods

- **`_handle_interviewer_response`**: Processes events from the interviewer agent
- **`_handle_user_response`**: Processes events from user responses
- **`_handle_interview_summary`**: Handles interview summary events

## Templates Used

The Skill Assessor Agent uses several prompt templates defined in `backend/agents/templates/skill_templates.py`:

- **`SKILL_SYSTEM_PROMPT`**: Defines the role of the AI skill assessor
- **`SKILL_EXTRACTION_TEMPLATE`**: Guides the identification of skills from responses
- **`PROFICIENCY_ASSESSMENT_TEMPLATE`**: Assesses proficiency levels for skills
- **`RESOURCE_SUGGESTION_TEMPLATE`**: Recommends resources for skill improvement
- **`SKILL_PROFILE_TEMPLATE`**: Creates comprehensive skill profiles
- **`ASSESSMENT_RESPONSE_TEMPLATE`**: Formats skill assessment responses
- **`RECENT_ANSWER_ASSESSMENT_TEMPLATE`**: Evaluates recent answers for skills
- **`SKILL_UPDATE_NOTIFICATION_TEMPLATE`**: Notifies about newly identified skills

## Data Flow

1. The agent receives events via the event bus when the user or interviewer responds
2. Skills are extracted from user responses using LLM-based analysis
3. Proficiency levels are assessed for each identified skill
4. Results are stored in the agent's internal state
5. The agent can generate reports, suggest resources, or provide assessments on request
6. At the end of an interview, a comprehensive skill profile is generated and published

## Event Handling

The Skill Assessor Agent subscribes to the following events:

- **`interviewer_response`**: When the interviewer agent generates a response
- **`user_response`**: When the user provides an answer
- **`interview_summary`**: When the interview concludes

The agent publishes the following events:

- **`skill_assessment_update`**: When new skills are identified
- **`comprehensive_skill_assessment`**: At the end of an interview

## Common Modifications

### Adding New Skill Categories

To add a new skill category:

1. Add the new category to the `SkillCategory` enum
2. Update the `_initialize_skill_keywords` method to include the new category
3. Update the `_identify_skills_in_text` method to properly categorize skills

```python
class SkillCategory(str, Enum):
    # ... existing categories ...
    NEW_CATEGORY = "new_category"
```

### Customizing Resource Recommendations

To customize resource recommendations:

1. Modify the `_get_resources_for_skill` method
2. Add new entries to the `technical_resources` or `soft_skill_resources` dictionaries

```python
technical_resources = {
    # ... existing resources ...
    "new_skill": [
        ("Resource Type", "Resource Name", "Description"),
        # ... more resources ...
    ]
}
```

### Improving Skill Detection

To improve skill detection accuracy:

1. Update the `_identify_skills_in_text` method with more sophisticated detection
2. Add specific patterns for skills in the `_initialize_skill_keywords` method
3. Consider integrating with external skill taxonomies or databases

### Adding Job-Specific Skill Sets

To add job-specific skill sets:

1. Expand the `role_skills` dictionary in the `__init__` method
2. Add new roles with their associated skills

```python
self.role_skills = {
    # ... existing roles ...
    "new_job_role": {
        "technical": ["skill1", "skill2"],
        "soft": ["skill3", "skill4"],
        # ... more categories ...
    }
}
```

## Best Practices

1. **Skill Taxonomy**: Maintain a consistent taxonomy of skills across your system
2. **Prompt Engineering**: Regularly review and refine the prompt templates for optimal skill extraction
3. **Resource Curation**: Curate high-quality, up-to-date resources for skill improvement
4. **Integration**: Ensure skill assessment results are integrated with the feedback provided by the Coach Agent
5. **Privacy**: Be transparent about how skill data is collected, stored, and used
6. **Calibration**: Regularly validate and calibrate the proficiency assessment against industry standards

## Common Issues and Solutions

### Issue: Skill Detection Misses Implied Skills

**Solution**: Update the `SKILL_EXTRACTION_TEMPLATE` to explicitly instruct the model to look for implied skills, not just explicitly mentioned ones. Consider adding a pre-processing step that expands responses with potential implied skills.

### Issue: Inaccurate Proficiency Assessment

**Solution**: Improve the `PROFICIENCY_ASSESSMENT_TEMPLATE` with more detailed criteria for each proficiency level. Consider implementing a multi-step assessment process that uses multiple indicators to determine proficiency.

### Issue: Irrelevant Skill Resources

**Solution**: Regularly update the resource recommendations in `_get_resources_for_skill`. Implement a feedback mechanism to track which resources are most helpful to users.

### Issue: Too Many Skill Notifications

**Solution**: Adjust the threshold in `_create_skill_update` to reduce interruptions. Consider batching skill updates or only interrupting for high-confidence skill identifications.

### Issue: Skill Categorization Errors

**Solution**: Enhance the `_identify_skills_in_text` method to handle ambiguous cases better. Consider implementing a validation step that cross-references skills against a known database.

## API Integration Points

The Skill Assessor Agent interacts with the frontend and other agents through events. Key integration points include:

- **Event Subscriptions**: The agent subscribes to user and interviewer events
- **Event Publications**: The agent publishes skill assessment events
- **Data Structures**: The agent works with `SkillAssessment` and `Resource` models 