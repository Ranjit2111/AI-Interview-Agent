# Agent constants
# Placeholder values for missing data
DEFAULT_JOB_ROLE = "the position"
DEFAULT_COMPANY_NAME = "our company"
DEFAULT_VALUE_NOT_PROVIDED = "Not provided"

# Question generation constants
DEFAULT_OPENING_QUESTION = "To start, could you please tell me a bit about yourself and your background?"
DEFAULT_FALLBACK_QUESTION = "Can you tell me about your professional background and experience?"
MINIMUM_QUESTION_COUNT = 3
ESTIMATED_TIME_PER_QUESTION = 3  # minutes

# Error messages
ERROR_AGENT_LOAD_FAILED = "Agent could not be loaded"
ERROR_INITIALIZATION_FAILED = "Initialization failed, no questions generated."
ERROR_INTERVIEW_SETUP = "Sorry, I encountered an error setting up the interview questions."
ERROR_PROCESSING_REQUEST = "Sorry, I encountered an error processing your request. Please try again."
ERROR_INTERVIEW_CONCLUDED = "The interview has already concluded."
ERROR_NO_QUESTION_TEXT = "It seems we've reached a natural stopping point. Thank you for your time."

# Interview closing messages
INTERVIEW_CONCLUSION = "Thank you for your time. This concludes the interview."

# Logging messages
LOG_GENERATING_QUESTIONS = "Generating initial interview questions..."
LOG_INTERVIEW_INTRODUCTION = "Interview introduction generated."
LOG_INTERVIEW_CONCLUDED = "Interview concluded based on ReAct decision."

# Coach feedback constants
COACH_FEEDBACK_ERROR = "An error occurred while generating coach feedback for this turn."
COACH_FEEDBACK_UNAVAILABLE = "Coach agent was not available to provide feedback for this turn."
COACH_FEEDBACK_NOT_GENERATED = "Coach feedback was not generated for this turn." 