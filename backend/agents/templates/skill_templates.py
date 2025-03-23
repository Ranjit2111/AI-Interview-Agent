"""
Templates for the Skill Assessor Agent.

This module contains prompts for skill extraction, assessment, and resource suggestion.
"""

# System prompt for the Skill Assessor Agent
SKILL_SYSTEM_PROMPT = """
You are a Skill Assessor AI specialized in evaluating technical competencies for {job_role} positions.
Your task is to analyze a candidate's responses during an interview to:
1. Identify technical and soft skills mentioned or demonstrated
2. Assess the candidate's proficiency level in each skill
3. Provide feedback on skill strengths and areas for improvement
4. Suggest relevant resources for skill development

Be objective and evidence-based in your assessments. Focus on specific statements, examples, and demonstrations
of knowledge rather than making assumptions. Consider both explicit mentions of skills and implicit demonstrations
of competency.
"""

# Template for extracting skills from text
SKILL_EXTRACTION_TEMPLATE = """
Analyze the following response from a job candidate for the {job_role} position.
Identify all technical and soft skills mentioned or demonstrated in the response.

For each skill:
1. Determine the skill name
2. Categorize it (technical, language, framework, soft, etc.)
3. Assess the confidence that this skill was actually demonstrated (0.0-1.0)

Response:
{response}

Output a JSON object with an array of extracted skills:
```json
{{
  "extracted_skills": [
    {{
      "skill_name": "skill_name",
      "category": "skill_category",
      "confidence": confidence_score
    }},
    ...
  ]
}}
```
"""

# Template for assessing proficiency level
PROFICIENCY_ASSESSMENT_TEMPLATE = """
Assess the candidate's proficiency level in {skill} based on the following context:

Context:
{context}

Job role: {job_role}

Proficiency should be categorized as:
- beginner: Basic understanding, needs significant guidance
- basic: Fundamental knowledge, can use with support
- intermediate: Solid practical experience, works independently on routine tasks
- advanced: Deep knowledge, handles complex problems, can mentor others
- expert: Comprehensive mastery, thought leadership, creates novel solutions

Output your assessment as a JSON object with proficiency level and feedback:
```json
{{
  "proficiency_level": "proficiency_level",
  "feedback": "Detailed feedback explaining the assessment, with evidence from the context",
  "confidence": confidence_score
}}
```
"""

# Template for suggesting resources
RESOURCE_SUGGESTION_TEMPLATE = """
The candidate has demonstrated a {proficiency_level} level in {skill} for the {job_role} position.

Suggest high-quality learning resources to help improve this skill. Consider:
1. Online courses or tutorials
2. Books or documentation
3. Practice exercises or projects
4. Communities or forums

Tailor your suggestions to the candidate's current proficiency level, focusing on resources that will help them advance to the next level.

Output your suggestions as a JSON object with an array of resources:
```json
{{
  "resources": [
    {{
      "type": "resource_type",
      "title": "resource_title",
      "url": "resource_url",
      "description": "Brief description of the resource and why it's relevant"
    }},
    ...
  ]
}}
```
"""

# Template for generating a skill profile
SKILL_PROFILE_TEMPLATE = """
Generate a comprehensive skill profile based on the following skills assessment data:

Skills data:
{skills}

Job role: {job_role}

Consider:
1. Overall profile strengths and gaps relative to the job role
2. Key technical competencies demonstrated and their levels
3. Soft skills demonstrated and their relevance
4. Areas for improvement and growth

Output a comprehensive skill profile as a JSON object:
```json
{{
  "overall_assessment": "Overall assessment of the candidate's skills relative to the job role",
  "strengths": [
    "Key strength 1",
    "Key strength 2",
    ...
  ],
  "areas_for_improvement": [
    "Area for improvement 1",
    "Area for improvement 2",
    ...
  ],
  "recommended_learning_path": "Suggested learning path to improve job readiness"
}}
```
"""

# Template for assessment response
ASSESSMENT_RESPONSE_TEMPLATE = """
Based on your interview responses, I've identified the following skills:

{skills_list}

Would you like me to:
1. Provide a detailed assessment of a specific skill?
2. Suggest resources to improve any of these skills?
3. Generate a comprehensive skill profile based on our conversation?
"""

# Template for recent answer assessment
RECENT_ANSWER_ASSESSMENT_TEMPLATE = """
Based on your recent answer, I've identified and assessed these skills:

{skills_list}

This assessment is based on specific examples and statements in your response.
For the {job_role} position, I'd recommend focusing on strengthening the skills marked at a basic level.
"""

# Template for skill update notification
SKILL_UPDATE_NOTIFICATION_TEMPLATE = """
I've identified these skills in your response: {skills}. 
I'll continue to update your skill assessment as we proceed with the interview.
""" 