# Plan for CoachAgent Overhaul and SkillAssessorAgent Removal

## I. Deletion of SkillAssessorAgent and Associated Components

* [ ] **Delete Files:**
  * [ ] Delete file: `backend/agents/skill_assessor.py`
  * [ ] Delete file: `backend/agents/templates/skill_templates.py`
  * [ ] Delete file: `skill_assessor_documentation.txt` (from workspace root or docs folder)
* [ ] **Update `backend/agents/orchestrator.py`:**
  * [ ] Remove import of `SkillAssessorAgent`.
  * [ ] In `_get_agent()`, remove the `elif agent_type == "skill_assessor":` block.
  * [ ] In `end_interview()`, remove the entire `try-except` block related to `skill_agent.generate_skill_profile()`.
  * [ ] Remove `final_results["skill_profile"] = None` initialization if present, and ensure `skill_profile` is not part of `final_results`.
* [ ] **Update `backend/utils/event_bus.py`:**
  * [ ] In the `EventType` enum, remove:
    * [ ] `SKILL_ASSESSMENT = "skill_assessment"`
    * [ ] `SKILL_EXTRACTED = "skill_extracted"`
* [ ] **Update `backend/agents/templates/__init__.py`:**
  * [ ] Remove any exports related to `skill_templates`.
* [ ] **Update `backend/schemas/session.py`:**
  * [ ] In `SessionEndResponse`, remove the field `skill_profile: Optional[Dict[str, Any]]`.

## II. Overhaul of CoachAgent

* [ ] **Restructure `backend/agents/coach.py`:**
  * [ ] Delete all existing methods and logic within the `CoachAgent` class, except for the `__init__` method (which will be modified) and `subscribe` (if inherited and used).
  * [ ] Modify `CoachAgent.__init__(self, llm_service: LLMService, event_bus: EventBus, logger: logging.Logger, resume: Optional[str], job_description: Optional[str])`:
    * [ ] Store `resume` and `job_description` as instance attributes (e.g., `self.resume_content`, `self.job_description`).
    * [ ] Initialize any other necessary state for the new CoachAgent.
  * [ ] Implement `evaluate_answer(self, question: str, answer: str, justification: Optional[str], conversation_history: List[Dict[str, Any]]) -> Dict[str, str]`:
    * [ ] This method will take the question posed, user's answer, interviewer's justification for the *next* question, and the conversation history.
    * [ ] It will use an LLM (via `self.llm` and a new prompt template) to generate feedback based on the specified dimensions:
      * Conciseness
      * Completeness
      * Technical Accuracy / Depth
      * Contextual Alignment (using stored `self.resume_content`, `self.job_description`)
      * Fixes & Improvements
      * (Optional) STAR Support
    * [ ] The output should be a dictionary where keys are the dimensions and values are the textual feedback. Example: `{"conciseness": "Your answer was a bit verbose because...", "completeness": "..."}`.
  * [ ] Implement `generate_final_summary(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]`:
    * [ ] This method will analyze the entire `conversation_history`.
    * [ ] Use an LLM with a new prompt template to:
      * Identify patterns/tendencies.
      * List strengths with examples.
      * List weaknesses with causes.
      * Suggest areas of focus.
    * [ ] Based on identified weaknesses, formulate 2-3 search queries.
    * [ ] **(Requires External Tool Call by Assistant)** Execute web searches using these queries. *Developer Note: The CoachAgent code will prepare the queries; the assistant (Gemini) will execute them when running the code.*
    * [ ] Incorporate search results into recommended resources.
    * [ ] Return a structured dictionary for the final summary. Example: `{"overall_feedback": "...", "strengths": ["...", "..."], "weaknesses": ["...", "..."], "improvement_areas": ["...", "..."], "recommended_resources": [{"query_used": "...", "title": "Resource 1", "url": "...", "snippet": "..."}, ...]}`.
* [ ] **Update `backend/agents/templates/coach_templates.py`:**
  * [ ] Delete all existing template strings.
  * [ ] Add a new prompt template for `evaluate_answer` covering all required feedback dimensions, designed for detailed, explanatory output. This prompt will need placeholders for `question`, `answer`, `justification`, `resume`, `job_description`, and relevant parts of `conversation_history` for context.
  * [ ] Add a new prompt template for `generate_final_summary` for analyzing the full interview, identifying patterns, strengths, weaknesses, and areas for improvement. This prompt should also guide the LLM to suggest topics for resource searching.
* [ ] **Update `backend/agents/templates/__init__.py`:**
  * [ ] Ensure new templates from `coach_templates.py` are correctly exported if a central export mechanism is used.

## III. Integration with Orchestrator (`backend/agents/orchestrator.py`)

* [ ] **Modify `AgentSessionManager._get_agent()`:**
  * [ ] Update the `elif agent_type == "coach":` block:
    * [ ] Instantiate `CoachAgent` passing `resume=self.session_config.resume_content` and `job_description=self.session_config.job_description`. (Verify these fields exist in `SessionConfig` from `backend/agents/config_models.py`).
* [ ] **Modify `AgentSessionManager.process_message()`:**
  * [ ] After receiving `user_message_data` (the user's answer) and adding it to `self.conversation_history`:
  * [ ] Identify `question_that_was_answered` from `self.conversation_history` (typically the last message from 'assistant' with agent 'interviewer').
  * [ ] After `interviewer_agent_response = interviewer_agent.process(agent_context)` is called:
    * [ ] Extract `justification_for_new_question` from `interviewer_agent_response.get("metadata", {}).get("justification")`.
  * [ ] If a valid `question_that_was_answered` exists:
    * [ ] Get the `coach_agent` instance using `self._get_agent("coach")`.
    * [ ] Call `coaching_feedback = coach_agent.evaluate_answer(question=question_that_was_answered, answer=user_message_data["content"], justification=justification_for_new_question, conversation_history=self.conversation_history)`.
    * [ ] Create a `coach_feedback_message` dictionary (role: 'assistant', agent: 'coach', content: `coaching_feedback`, response_type: 'coaching_feedback', timestamp).
    * [ ] Append `coach_feedback_message` to `self.conversation_history`.
    * [ ] Publish an event for this coach feedback (e.g., `EventType.ASSISTANT_RESPONSE` with source 'CoachAgent', or a new `EventType.COACH_CYCLE_FEEDBACK`).
* [ ] **Modify `AgentSessionManager.end_interview()`:**
  * [ ] Get the `coach_agent` instance.
  * [ ] Call `final_coaching_summary = coach_agent.generate_final_summary(conversation_history=self.conversation_history)`.
  * [ ] Update `final_results["coaching_summary"] = final_coaching_summary`. Ensure this replaces any old structure.
  * [ ] Remove `final_results["skill_profile"]` if it's still being assigned or accessed.

## IV. Updates to InterviewerAgent (`backend/agents/interviewer.py`)

* [ ] **Modify `InterviewerAgent.process()`:**
  * [ ] In the section where `response_data` is prepared for a question (i.e., not introduction or closing):
    * [ ] Ensure that the `justification` obtained from `action_result = self._determine_and_generate_next_action(context)` is included in `response_data["metadata"]`.
    * [ ] Specifically, change `response_data["metadata"] = {"question_number": self.asked_question_count}` to something like `response_data["metadata"] = {"question_number": self.asked_question_count, "justification": action_result.get("justification")}`.

## V. Verification and Testing

* [ ] Review all modified files for correctness and completeness.
* [ ] Manually trace the data flow for a typical Q&A cycle to ensure `CoachAgent` receives correct inputs.
* [ ] Manually trace the data flow for `end_interview` to ensure the final summary is generated and included.
* [ ] Test the application to confirm that:
  * `SkillAssessorAgent` is completely removed and no errors occur due to its absence.
  * `CoachAgent` provides feedback after each user answer.
  * `CoachAgent` provides a final summary when the interview ends.
  * The feedback format matches the new requirements.
  * Session flow is not broken.
