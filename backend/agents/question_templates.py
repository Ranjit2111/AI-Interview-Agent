"""
Question templates for the InterviewerAgent.
Contains all the template configurations for generating generic interview questions.
"""

from typing import Dict, List
from backend.agents.config_models import InterviewStyle

# Question templates organized by interview style
QUESTION_TEMPLATES: Dict[InterviewStyle, List[str]] = {
    InterviewStyle.FORMAL: [
        "Can you describe your experience with {technology}?",
        "How would you approach a situation where {scenario}?",
        "What methodology would you use to solve {problem_type} problems?",
        "Describe a time when you had to {challenge}. How did you handle it?",
        "How do you ensure {quality_aspect} in your work?",
    ],
    InterviewStyle.CASUAL: [
        "Tell me about a time you worked with {technology}. How did it go?",
        "What would you do if {scenario}?",
        "How do you typically tackle {problem_type} problems?",
        "Have you ever had to {challenge}? What happened?",
        "How do you make sure your work is {quality_aspect}?",
    ],
    InterviewStyle.AGGRESSIVE: [
        "Prove to me you have experience with {technology}.",
        "What exactly would you do if {scenario}? Be specific.",
        "I need to know exactly how you would solve {problem_type} problems. Details.",
        "Give me a specific example of when you {challenge}. What exactly did you do?",
        "How specifically do you ensure {quality_aspect}? Don't give me generalities.",
    ],
    InterviewStyle.TECHNICAL: [
        "Explain the key concepts of {technology} and how you've implemented them.",
        "What is your approach to {scenario} from a technical perspective?",
        "Walk me through your process for solving {problem_type} problems, including any algorithms or data structures you would use.",
        "Describe a technical challenge where you had to {challenge}. What was your solution?",
        "What metrics and tools do you use to ensure {quality_aspect} in your technical work?",
    ]
}

# Template variables organized by job role
TEMPLATE_VARIABLES: Dict[str, Dict[str, List[str]]] = {
    "Software Engineer": {
        "technology": ["React", "Python", "cloud infrastructure", "REST APIs", "microservices"],
        "scenario": ["production system failure", "changing requirements", "performance optimization"],
        "problem_type": ["algorithmic", "debugging", "system design"],
        "challenge": ["lead a project", "mentor juniors", "meet tight deadlines"],
        "quality_aspect": ["code quality", "test coverage", "reliability"]
    },
    "Data Scientist": {
        "technology": ["Python for data analysis", "machine learning frameworks", "data visualization"],
        "scenario": ["incomplete data", "explaining results", "poor model performance"],
        "problem_type": ["prediction", "classification", "clustering"],
        "challenge": ["clean messy data", "deploy a model", "interpret complex results"],
        "quality_aspect": ["model accuracy", "reproducibility", "interpretability"]
    },
}

# General questions that work for any role
GENERAL_QUESTIONS = [
    "What attracted you to this position?",
    "Where do you see yourself professionally in five years?",
    "Why do you think you're a good fit for this {job_role}?",
    "Describe your ideal work environment.",
    "How do you stay updated with the latest developments in your field?"
] 