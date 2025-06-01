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
        "title_template": "Free {skill} Course on freeCodeCamp",
        "url_template": "https://www.freecodecamp.org/learn",
        "description_template": "Learn {skill} with free, hands-on coding tutorials and projects.",
        "type": "course"
    },
    {
        "title_template": "{skill} Documentation and Tutorials",
        "url_template": "https://developer.mozilla.org/en-US/",
        "description_template": "Comprehensive {skill} documentation and learning resources from Mozilla Developer Network.",
        "type": "documentation"
    },
    {
        "title_template": "{skill} Learning Path on GitHub",
        "url_template": "https://github.com/topics/learning-resources",
        "description_template": "Open source {skill} learning materials, projects, and examples on GitHub.",
        "type": "tutorial"
    },
    {
        "title_template": "Interactive {skill} Tutorials",
        "url_template": "https://www.codecademy.com/catalog",
        "description_template": "Interactive coding lessons and exercises for learning {skill} at {proficiency_level} level.",
        "type": "interactive"
    },
    {
        "title_template": "{skill} Community on Reddit",
        "url_template": "https://www.reddit.com/r/learnprogramming/",
        "description_template": "Active community discussions, resources, and help for learning {skill}.",
        "type": "community"
    },
    {
        "title_template": "Khan Academy {skill} Course",
        "url_template": "https://www.khanacademy.org/computing",
        "description_template": "Free educational content for learning {skill} fundamentals with visual explanations.",
        "type": "course"
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