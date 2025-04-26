"""
Templates for the Skill Assessor Agent.

This module contains prompts for skill extraction, assessment, and resource suggestion.
"""

# System prompt for the Skill Assessor Agent
SKILL_SYSTEM_PROMPT = """
You are a Skill Assessor AI specialized in evaluating technical competencies for {job_role} positions.
Your task is to analyze a candidate's responses during an interview to:
1. Identify technical and soft skills mentioned or demonstrated
2. Assess the candidate's proficiency level in each skill (beginner, basic, intermediate, advanced, expert)
3. Suggest relevant resources for skill development (optional, if requested/relevant)

Be objective and evidence-based in your assessments. Focus on specific statements, examples, and demonstrations
of knowledge. Output structured data.
"""

# Template for extracting skills from text
SKILL_EXTRACTION_TEMPLATE = """
Analyze the following response from a job candidate for the {job_role} position.
Identify all technical and soft skills mentioned or demonstrated in the response.

For each skill:
1. Determine the skill name (be specific, e.g., 'Python (language)', 'React (framework)')
2. Categorize it (technical, language, framework, soft, tool, process, domain, etc.)
3. Assess the confidence that this skill was actually demonstrated (0.0-1.0)

Response:
{response}

Output ONLY a valid JSON object with an array under the key "extracted_skills":
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

Context (candidate's relevant statements):
{context}

Job role context: {job_role}

Proficiency should be categorized as one of: beginner | basic | intermediate | advanced | expert
- beginner: Basic awareness, needs significant guidance
- basic: Fundamental knowledge, can perform simple tasks with support
- intermediate: Solid practical experience, works independently on routine tasks
- advanced: Deep knowledge, handles complex problems, may mentor others
- expert: Comprehensive mastery, thought leadership, innovator

Output ONLY a valid JSON object with proficiency level and confidence score:
```json
{{
  "proficiency_level": "proficiency_category",
  "confidence": confidence_score_0_to_1
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

Output ONLY a valid JSON object with an array under the key "resources":
```json
{{
  "resources": [
    {{
      "type": "resource_type (e.g., course, book, tutorial, project, community)",
      "title": "resource_title",
      "url": "resource_url (if applicable, else null)",
      "description": "Brief description of the resource and why it's relevant"
    }},
    ...
  ]
}}
```
"""

# Template for generating a skill profile (Simplified)
SKILL_PROFILE_TEMPLATE = """
Generate a structured skill summary based on the following skills assessment data:

Skills data (JSON array): 
{skills_json}

Job role: {job_role}

Output ONLY a valid JSON object summarizing the assessed skills and levels:
```json
{{
  "job_role": "{job_role}",
  "assessed_skills": [
    {{
       "skill_name": "skill_name",
       "category": "skill_category",
       "assessed_proficiency": "proficiency_level",
       "assessment_confidence": confidence_score_0_to_1, 
       "evidence_mentions": mention_count
    }},
    ...
  ]
}}
```
"""
