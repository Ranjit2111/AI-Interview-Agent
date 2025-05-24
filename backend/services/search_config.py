"""
Search service configuration.
Contains domain mappings, resource classifications, and proficiency level terms.
"""

from typing import Dict, List, Set


# Domain mappings for resource classification
COURSE_DOMAINS = {
    "coursera.org", "udemy.com", "edx.org", "pluralsight.com", 
    "linkedin.com/learning", "udacity.com", "skillshare.com"
}

VIDEO_DOMAINS = {
    "youtube.com", "vimeo.com", "youtube", "youtu.be"
}

DOCUMENTATION_DOMAINS = {
    "docs.", ".io/docs", "developer.", "reference"
}

COMMUNITY_DOMAINS = {
    "stackoverflow.com", "reddit.com", "forum.", "community."
}

BOOK_DOMAINS = {
    "amazon.com", "goodreads.com", "oreilly.com", "manning.com"
}

# Resource type indicators
COURSE_INDICATORS = {"course", "class", "learn", "training", "bootcamp", "academy"}

VIDEO_INDICATORS = {"video", "watch", "tutorial"}

DOCUMENTATION_INDICATORS = {"documentation", "docs", "reference", "manual", "guide"}

TUTORIAL_INDICATORS = {"tutorial", "how to", "guide", "learn", "step by step"}

COMMUNITY_INDICATORS = {"forum", "community", "discussion", "stack overflow", "reddit"}

BOOK_INDICATORS = {"book", "ebook", "reading", "publication"}

# Quality domain mappings  
TOP_QUALITY_DOMAINS = {
    "github.com", "stackoverflow.com", "mdn.mozilla.org", "freecodecamp.org",
    "coursera.org", "udemy.com", "pluralsight.com", "edx.org",
    "medium.com", "dev.to", "docs.microsoft.com", "developer.mozilla.org",
    "w3schools.com", "geeksforgeeks.org", "youtube.com", "linkedin.com/learning",
    "udacity.com", "tutorialspoint.com", "khanacademy.org", "harvard.edu",
    "mit.edu", "stanford.edu", "educative.io", "reddit.com", "hackernoon.com"
}

MEDIUM_QUALITY_DOMAINS = {
    "guru99.com", "javatpoint.com", "educba.com", "simplilearn.com", 
    "bitdegree.org", "digitalocean.com/community/tutorials",
    "towardsdatascience.com", "css-tricks.com", "hackr.io", "baeldung.com",
    "tutorialrepublic.com", "programiz.com", "learnpython.org"
}

# Proficiency level terms
PROFICIENCY_LEVEL_TERMS = {
    "beginner": {"beginner", "introduction", "basics", "start", "learn"},
    "basic": {"beginner", "introduction", "basics", "start", "learn"},
    "intermediate": {"intermediate", "improve", "practice"},
    "advanced": {"advanced", "expert", "mastering", "deep dive"},
    "expert": {"expert", "mastering", "advanced techniques", "professional"}
}

# Fallback platform templates
FALLBACK_PLATFORMS = [
    {
        "title_template": "Learn {skill} on Coursera",
        "url_template": "https://www.coursera.org/courses?query={skill}",
        "description_template": "Find online courses on {skill} from leading universities and companies.",
        "type": "course"
    },
    {
        "title_template": "{skill} tutorials on Udemy",
        "url_template": "https://www.udemy.com/courses/search/?q={skill}",
        "description_template": "Explore a wide range of {skill} courses for all skill levels.",
        "type": "course"
    },
    {
        "title_template": "{skill} on YouTube",
        "url_template": "https://www.youtube.com/results?search_query={skill}+{proficiency_level}+tutorial",
        "description_template": "Watch free video tutorials on {skill} at {proficiency_level} level.",
        "type": "video"
    },
    {
        "title_template": "{skill} community on Stack Overflow",
        "url_template": "https://stackoverflow.com/questions/tagged/{skill_tag}",
        "description_template": "Find answers to your {skill} questions from the developer community.",
        "type": "community"
    },
    {
        "title_template": "{skill} on GitHub",
        "url_template": "https://github.com/topics/{skill_tag}",
        "description_template": "Explore {skill} projects, libraries, and resources on GitHub.",
        "type": "community"
    }
]

# Scoring weights for relevance calculation
RELEVANCE_WEIGHTS = {
    "skill_in_title": 0.4,
    "skill_in_url": 0.2,
    "skill_in_description": 0.1,
    "level_in_title": 0.15,
    "level_in_description": 0.05,
    "job_role_in_title": 0.15,
    "job_role_in_description": 0.05,
    "domain_quality_multiplier": 0.1
}

# Quality scores for domain categories
DOMAIN_QUALITY_SCORES = {
    "top": 1.0,
    "medium": 0.7,
    "default": 0.4
} 