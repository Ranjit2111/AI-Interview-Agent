"""
Coach agent module for providing feedback and guidance to users during interview preparation.
This agent analyzes interview performance and offers personalized advice for improvement.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.output_parsers.json import JsonOutputParser
from langchain.output_parsers.structured import StructuredOutputParser
from langchain.output_parsers.format_instructions import FORMAT_INSTRUCTIONS

from backend.agents.base import BaseAgent, AgentContext
from backend.utils.event_bus import Event, EventBus


class CoachingFocus(str):
    """
    Predefined coaching focus areas.
    These represent different aspects of interview performance that can be coached.
    """
    COMMUNICATION = "communication"
    CONTENT = "content"
    CONFIDENCE = "confidence"
    TECHNICAL_DEPTH = "technical_depth"
    STORYTELLING = "storytelling"
    SPECIFICITY = "specificity"
    BODY_LANGUAGE = "body_language"
    CONCISENESS = "conciseness"


class CoachingMode(str):
    """Enum representing the coaching modes."""
    REAL_TIME = "real_time"
    SUMMARY = "summary"
    TARGETED = "targeted"
    PASSIVE = "passive"


class CoachAgent(BaseAgent):
    """
    Agent that provides coaching and feedback during interview preparation.
    
    The coach agent is responsible for:
    - Analyzing user's interview answers
    - Providing real-time feedback and improvement suggestions
    - Identifying strengths and weaknesses
    - Offering personalized coaching plans
    - Suggesting resources for skill development
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        planning_interval: int = 5,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        coaching_mode: CoachingMode = CoachingMode.REAL_TIME,
        coaching_focus: Optional[List[str]] = None,
        feedback_verbosity: str = "detailed"
    ):
        """
        Initialize the coach agent.
        
        Args:
            api_key: API key for the language model
            model_name: Name of the language model to use
            planning_interval: Number of interactions before planning
            event_bus: Event bus for inter-agent communication
            logger: Logger for recording agent activity
            coaching_mode: Mode of coaching (real_time, summary, targeted, passive)
            coaching_focus: List of areas to focus coaching on (defaults to all areas)
            feedback_verbosity: Level of detail in feedback (brief, moderate, detailed)
        """
        super().__init__(api_key, model_name, planning_interval, event_bus, logger)
        
        self.coaching_mode = coaching_mode
        self.coaching_focus = coaching_focus or [
            CoachingFocus.COMMUNICATION,
            CoachingFocus.CONTENT,
            CoachingFocus.CONFIDENCE,
            CoachingFocus.SPECIFICITY
        ]
        self.feedback_verbosity = feedback_verbosity
        self.interview_session_id = None
        self.current_question = None
        self.current_answer = None
        self.interview_performance = {}
        self.improvement_areas = set()
        self.strength_areas = set()
        
        # Setup LLM chains
        self._setup_llm_chains()
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe("interviewer_response", self._handle_interviewer_message)
            self.event_bus.subscribe("user_response", self._handle_user_message)
            self.event_bus.subscribe("interview_summary", self._handle_interview_summary)
            self.event_bus.subscribe("coaching_request", self._handle_coaching_request)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the coach agent.
        
        Returns:
            System prompt string
        """
        return (
            "You are an expert interview coach with years of experience helping candidates "
            "succeed in job interviews. Your goal is to provide constructive, actionable "
            "feedback to help the candidate improve their interview performance. "
            f"You're currently operating in {self.coaching_mode} mode. "
            f"Your focus areas are: {', '.join(self.coaching_focus)}. "
            "Be supportive but honest, highlighting both strengths and areas for improvement."
        )
    
    def _initialize_tools(self) -> List[Tool]:
        """
        Initialize tools for the coach agent.
        
        Returns:
            List of LangChain tools
        """
        return [
            Tool(
                name="analyze_response",
                func=self._analyze_response_tool,
                description="Analyze a candidate's response to an interview question and provide feedback"
            ),
            Tool(
                name="generate_improvement_tips",
                func=self._generate_improvement_tips_tool,
                description="Generate specific tips for improving in particular areas of interview performance"
            ),
            Tool(
                name="create_coaching_summary",
                func=self._create_coaching_summary_tool,
                description="Create a comprehensive coaching summary based on the entire interview"
            ),
            Tool(
                name="generate_response_template",
                func=self._generate_response_template_tool,
                description="Generate a template for how to effectively answer a specific type of interview question"
            )
        ]
    
    def _setup_llm_chains(self) -> None:
        """
        Set up LangChain chains for the agent's tasks.
        """
        # Response analysis chain
        analysis_template = """
        You are an expert interview coach analyzing a candidate's response to an interview question.
        
        Question: {question}
        Candidate's Response: {response}
        
        Analyze the response on the following dimensions:
        1. Content relevance (How well did they answer what was asked?)
        2. Structure (How well organized was the response?)
        3. Communication clarity (How clearly did they express their points?)
        4. Use of examples (Did they provide specific, relevant examples?)
        5. Brevity vs. detail (Was the response appropriately detailed?)
        6. Confidence indicators (What does their language suggest about confidence?)
        
        Focus especially on these areas: {focus_areas}
        
        Provide a balanced assessment highlighting strengths and areas for improvement.
        """
        
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(analysis_template),
            output_key="analysis"
        )
        
        # Improvement tips chain
        tips_template = """
        You are an expert interview coach helping a candidate improve their interview performance.
        
        Focus area: {focus_area}
        Context: {context}
        
        Provide 3-5 specific, actionable tips to help the candidate improve in this area.
        Each tip should include:
        1. A clear instruction
        2. The rationale behind it
        3. A brief example of how to implement it
        
        Make your advice practical and immediately applicable in their next response.
        """
        
        self.tips_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(tips_template),
            output_key="tips"
        )
        
        # Coaching summary chain
        summary_template = """
        You are an expert interview coach creating a comprehensive coaching summary for a candidate.
        
        Interview Context: {interview_context}
        Question-Answer Pairs: {qa_pairs}
        
        Create a comprehensive coaching summary that includes:
        1. Overall assessment of interview performance
        2. Key strengths demonstrated throughout the interview
        3. Primary areas for improvement
        4. 3-5 specific, actionable recommendations for future interviews
        5. A brief motivational conclusion
        
        Focus especially on these areas: {focus_areas}
        
        Be constructive and supportive while providing honest feedback.
        """
        
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(summary_template),
            output_key="coaching_summary"
        )
        
        # Response template chain
        template_prompt = """
        You are an expert interview coach creating a template for effectively answering a specific type of interview question.
        
        Question type: {question_type}
        Example question: {example_question}
        Candidate's job role: {job_role}
        
        Create a response template that includes:
        1. Recommended structure for this type of question
        2. Key components to include
        3. Common pitfalls to avoid
        4. A brief example of a strong response
        
        The template should be adaptable to various specific questions of this type.
        """
        
        self.template_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(template_prompt),
            output_key="response_template"
        )
    
    def _analyze_response_tool(self, question: str, response: str) -> str:
        """
        Tool function to analyze a candidate's response to an interview question.
        
        Args:
            question: The interview question
            response: The candidate's response
            
        Returns:
            Analysis of the response
        """
        return self.analysis_chain.invoke({
            "question": question,
            "response": response,
            "focus_areas": ", ".join(self.coaching_focus)
        })["analysis"]
    
    def _generate_improvement_tips_tool(self, focus_area: str, context: str) -> str:
        """
        Tool function to generate improvement tips for a specific area.
        
        Args:
            focus_area: The area to focus on
            context: Context about the candidate's performance
            
        Returns:
            Improvement tips
        """
        return self.tips_chain.invoke({
            "focus_area": focus_area,
            "context": context
        })["tips"]
    
    def _create_coaching_summary_tool(self, interview_context: str, qa_pairs: List[Dict[str, str]]) -> str:
        """
        Tool function to create a comprehensive coaching summary.
        
        Args:
            interview_context: Context about the interview
            qa_pairs: List of question-answer pairs
            
        Returns:
            Coaching summary
        """
        qa_text = "\n\n".join([f"Q: {pair['question']}\nA: {pair['answer']}" for pair in qa_pairs])
        
        return self.summary_chain.invoke({
            "interview_context": interview_context,
            "qa_pairs": qa_text,
            "focus_areas": ", ".join(self.coaching_focus)
        })["coaching_summary"]
    
    def _generate_response_template_tool(self, question_type: str, example_question: str, job_role: str) -> str:
        """
        Tool function to generate a template for answering a specific type of question.
        
        Args:
            question_type: The type of question
            example_question: An example question of this type
            job_role: The candidate's job role
            
        Returns:
            Response template
        """
        return self.template_chain.invoke({
            "question_type": question_type,
            "example_question": example_question,
            "job_role": job_role
        })["response_template"]
    
    def process_input(self, input_text: str, context: AgentContext) -> str:
        """
        Process input from the user and generate coaching feedback.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            The agent's coaching response
        """
        # Update context with user input
        context.add_message("user", input_text)
        
        # Determine if this is a request for specific coaching or general feedback
        if "help" in input_text.lower() or "advice" in input_text.lower() or "tip" in input_text.lower():
            response = self._provide_generic_advice(input_text, context)
        elif "strength" in input_text.lower() or "good" in input_text.lower() or "well" in input_text.lower():
            response = self._highlight_strengths(context)
        elif "improve" in input_text.lower() or "weakness" in input_text.lower() or "better" in input_text.lower():
            response = self._suggest_improvements(context)
        elif "summarize" in input_text.lower() or "summary" in input_text.lower():
            response = self._generate_coaching_summary(context)
        elif "resource" in input_text.lower() or "learn" in input_text.lower() or "study" in input_text.lower():
            response = self._suggest_resources(input_text, context)
        else:
            # Analyze the most recent answer and provide feedback
            response = self._analyze_recent_response(context)
        
        # Add response to context
        context.add_message("assistant", response)
        
        # Publish event
        if self.event_bus:
            self.event_bus.publish(Event(
                event_type="coach_feedback",
                source="coach_agent",
                data={
                    "feedback": response,
                    "session_id": self.interview_session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        
        return response
    
    def _analyze_recent_response(self, context: AgentContext) -> str:
        """
        Analyze the most recent user response and provide coaching feedback.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Coaching feedback on the user's response
        """
        # Get the most recent user message
        for idx in range(len(context.conversation_history) - 1, -1, -1):
            message = context.conversation_history[idx]
            if message["role"] == "user":
                recent_response = message["content"]
                break
        else:
            return "I don't see any recent responses to analyze. Could you share what you'd like feedback on?"
        
        # TODO: Replace with actual LLM call for more intelligent analysis
        
        # Simple analysis based on response length and complexity
        words = recent_response.split()
        
        feedback_parts = []
        
        # Communication analysis
        if CoachingFocus.COMMUNICATION in self.coaching_focus:
            if len(words) < 20:
                feedback_parts.append("Your response was quite brief. In interviews, it's generally better to provide more context and details to fully showcase your experience and thinking.")
                self.improvement_areas.add(CoachingFocus.COMMUNICATION)
            elif len(words) > 200:
                feedback_parts.append("Your answer was quite lengthy. While detail is good, try to be more concise while still conveying the key points to respect the interviewer's time.")
                self.improvement_areas.add(CoachingFocus.CONCISENESS)
            else:
                feedback_parts.append("You communicated with a good balance of detail and conciseness.")
                self.strength_areas.add(CoachingFocus.COMMUNICATION)
        
        # Content analysis
        if CoachingFocus.CONTENT in self.coaching_focus:
            specificity_words = ["specifically", "example", "instance", "case", "situation", "experience", "project"]
            has_specifics = any(word in recent_response.lower() for word in specificity_words)
            
            if has_specifics:
                feedback_parts.append("Great job including specific examples in your answer. This makes your response more credible and memorable.")
                self.strength_areas.add(CoachingFocus.SPECIFICITY)
            else:
                feedback_parts.append("Try to include specific examples from your experience to support your points. Instead of general statements, provide concrete instances that demonstrate your skills.")
                self.improvement_areas.add(CoachingFocus.SPECIFICITY)
        
        # Structure analysis
        structure_words = ["first", "second", "third", "finally", "additionally", "moreover", "in conclusion"]
        has_structure = any(word in recent_response.lower() for word in structure_words)
        
        if has_structure:
            feedback_parts.append("Your answer has a clear structure, which makes it easy to follow. Well done.")
            self.strength_areas.add(CoachingFocus.COMMUNICATION)
        else:
            feedback_parts.append("Consider structuring your answer more clearly with an introduction, key points, and a conclusion. This makes it easier for the interviewer to follow your thoughts.")
            self.improvement_areas.add(CoachingFocus.COMMUNICATION)
        
        # Personalized improvement tip
        improvement_tip = self._get_improvement_tip()
        if improvement_tip:
            feedback_parts.append(f"\n\nAction item: {improvement_tip}")
        
        # Combine feedback parts
        if self.feedback_verbosity == "brief":
            # Return only the most important feedback point and improvement tip
            return f"{feedback_parts[0]}\n\n{feedback_parts[-1]}"
        elif self.feedback_verbosity == "moderate":
            # Return a subset of feedback points
            return "\n\n".join(feedback_parts[:2] + [feedback_parts[-1]])
        else:
            # Return all feedback
            return "\n\n".join(feedback_parts)
    
    def _provide_generic_advice(self, input_text: str, context: AgentContext) -> str:
        """
        Provide generic interview advice based on the user's query.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            Generic interview advice
        """
        # TODO: Replace with actual LLM-based contextual advice
        
        # Check for common advice topics
        if "nervous" in input_text.lower() or "anxiety" in input_text.lower():
            return (
                "It's normal to feel nervous before and during interviews. Here are some strategies to manage interview anxiety:\n\n"
                "1. **Preparation**: The more prepared you are, the more confident you'll feel. Research the company, practice common questions, and know your resume well.\n\n"
                "2. **Breathing techniques**: Before the interview, take deep breaths: inhale for 4 seconds, hold for 2, exhale for 6. This can help calm your nervous system.\n\n"
                "3. **Reframe your thinking**: Think of the interview as a conversation rather than an interrogation. You're also evaluating if the company is right for you.\n\n"
                "4. **Practice makes progress**: The more interviews you do (even practice ones), the more comfortable you'll become with the process.\n\n"
                "5. **Positive visualization**: Spend time visualizing the interview going well and you responding confidently."
            )
        elif "tell me about yourself" in input_text.lower() or "introduce yourself" in input_text.lower():
            return (
                "The 'Tell me about yourself' question is often used to start interviews. Here's a structure to craft an effective response:\n\n"
                "1. **Present**: Start with your current role and responsibilities. Mention your title, what you do, and briefly describe your primary responsibilities.\n\n"
                "2. **Past**: Briefly explain your background and how you got to where you are today. Highlight relevant experiences and accomplishments.\n\n"
                "3. **Future**: Explain why you're interested in this position and how it aligns with your career goals.\n\n"
                "4. **Keep it professional**: Focus on your professional background rather than personal details.\n\n"
                "5. **Be concise**: Aim for 1-2 minutes maximum. This should be a highlight reel, not your entire work history.\n\n"
                "Example structure: 'I'm currently a [position] at [company] where I [key responsibilities]. Before that, I [relevant past experience] where I accomplished [notable achievement]. I'm looking for opportunities to [career goal] which is why I'm excited about this position.'"
            )
        elif "strength" in input_text.lower() or "weakness" in input_text.lower():
            return (
                "Questions about strengths and weaknesses are interview classics. Here's how to approach them effectively:\n\n"
                "**For strengths**:\n"
                "1. Choose strengths that are relevant to the position\n"
                "2. Back them up with specific examples and achievements\n"
                "3. Explain how these strengths would benefit the company\n\n"
                "**For weaknesses**:\n"
                "1. Choose genuine weaknesses that aren't critical to the job\n"
                "2. Focus primarily on how you're actively working to improve\n"
                "3. Demonstrate self-awareness and commitment to professional growth\n"
                "4. Avoid clichés like 'I'm a perfectionist' without genuine context\n\n"
                "Example weakness response: 'I've sometimes struggled with public speaking. To address this, I joined Toastmasters last year and have been volunteering to lead more team presentations. While I still get nervous, I've made significant progress in my delivery and confidence.'"
            )
        elif "salary" in input_text.lower() or "compensation" in input_text.lower():
            return (
                "Discussing salary can be tricky. Here's how to navigate compensation questions:\n\n"
                "1. **Research first**: Know the market rate for your position, experience level, and location using sites like Glassdoor, PayScale, or industry reports.\n\n"
                "2. **Timing matters**: Ideally, wait for the employer to bring up compensation first. Focus on establishing your value before discussing numbers.\n\n"
                "3. **Give a range**: When asked, provide a range rather than a specific number. Make sure your minimum is still acceptable to you.\n\n"
                "4. **Consider the total package**: Remember that compensation includes benefits, work flexibility, growth opportunities, and other perks—not just salary.\n\n"
                "5. **Practice your response**: Be prepared to confidently state something like: 'Based on my research and experience, I'm looking for a range between $X and $Y, but I'm also considering the entire compensation package and growth opportunities.'"
            )
        else:
            return (
                "Here are some general interview tips that may help:\n\n"
                "1. **Research the company**: Understand their mission, products, culture, and recent news.\n\n"
                "2. **Use the STAR method** for behavioral questions: Situation, Task, Action, Result.\n\n"
                "3. **Prepare thoughtful questions** to ask the interviewer about the role, team, and company.\n\n"
                "4. **Practice but don't memorize**: Have talking points ready, but keep your responses conversational.\n\n"
                "5. **Quantify achievements** whenever possible with numbers, percentages, or timeframes.\n\n"
                "6. **Listen carefully** to questions before answering to ensure you're addressing what's being asked.\n\n"
                "7. **Follow up** with a thank-you email within 24 hours of the interview.\n\n"
                "Is there a specific aspect of interviewing you'd like more targeted advice on?"
            )
    
    def _highlight_strengths(self, context: AgentContext) -> str:
        """
        Highlight the user's strengths based on their interview performance.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Summary of the user's strengths
        """
        # TODO: Replace with actual LLM-based analysis of the user's performance
        
        if not self.strength_areas:
            return (
                "I haven't observed enough of your interview responses yet to identify specific strengths. "
                "As you continue with the interview practice, I'll provide more personalized feedback on what you're doing well. "
                "Would you like me to share some general strengths that are valuable in interviews?"
            )
        
        strengths_feedback = {
            CoachingFocus.COMMUNICATION: "You communicate your thoughts clearly and effectively. Your answers are well-structured and easy to follow.",
            CoachingFocus.CONTENT: "You provide substantive answers with good depth of knowledge and relevant information.",
            CoachingFocus.CONFIDENCE: "You project confidence in your responses, which makes your answers more compelling and credible.",
            CoachingFocus.TECHNICAL_DEPTH: "You demonstrate strong technical knowledge and can explain complex concepts clearly.",
            CoachingFocus.STORYTELLING: "You use storytelling effectively to make your experiences memorable and engaging.",
            CoachingFocus.SPECIFICITY: "You provide specific, concrete examples that effectively illustrate your points.",
            CoachingFocus.CONCISENESS: "You communicate efficiently, making your points without unnecessary verbosity."
        }
        
        response_parts = ["Based on your interview responses, here are your key strengths:"]
        
        for strength in self.strength_areas:
            if strength in strengths_feedback:
                response_parts.append(f"- **{strength.title()}**: {strengths_feedback[strength]}")
        
        response_parts.append("\nContinue leveraging these strengths while we work on other areas for improvement.")
        
        return "\n\n".join(response_parts)
    
    def _suggest_improvements(self, context: AgentContext) -> str:
        """
        Suggest improvements based on the user's interview performance.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Suggested improvements for the user
        """
        # TODO: Replace with actual LLM-based analysis of the user's performance
        
        if not self.improvement_areas:
            return (
                "I haven't observed enough of your interview responses yet to identify specific improvement areas. "
                "As you continue with the interview practice, I'll provide more personalized feedback on areas to enhance. "
                "Would you like me to share some common interview skill improvement areas?"
            )
        
        improvement_feedback = {
            CoachingFocus.COMMUNICATION: "Work on structuring your answers more clearly with an introduction, key points, and a conclusion.",
            CoachingFocus.CONTENT: "Try to include more substantive content in your answers, including relevant skills, experiences, and achievements.",
            CoachingFocus.CONFIDENCE: "Practice speaking with more confidence by eliminating filler words and maintaining a steady pace.",
            CoachingFocus.TECHNICAL_DEPTH: "Consider deepening your technical explanations to demonstrate more expertise in your field.",
            CoachingFocus.STORYTELLING: "Incorporate more storytelling techniques to make your experiences more engaging and memorable.",
            CoachingFocus.SPECIFICITY: "Include more specific examples, metrics, and outcomes when discussing your experiences.",
            CoachingFocus.CONCISENESS: "Work on being more concise while still conveying all key information."
        }
        
        response_parts = ["Based on your interview responses, here are areas for improvement:"]
        
        for area in self.improvement_areas:
            if area in improvement_feedback:
                response_parts.append(f"- **{area.title()}**: {improvement_feedback[area]}")
        
        response_parts.append("\nI recommend focusing on one or two of these areas at a time. Would you like specific exercises to improve in any of these areas?")
        
        return "\n\n".join(response_parts)
    
    def _suggest_resources(self, input_text: str, context: AgentContext) -> str:
        """
        Suggest resources for skill development.
        
        Args:
            input_text: The user's input text
            context: The current context of the conversation
            
        Returns:
            Suggested resources for skill development
        """
        # Check if the query is about a specific area
        if "technical" in input_text.lower() or "coding" in input_text.lower():
            return (
                "Here are resources to improve your technical interview skills:\n\n"
                "1. **Books**:\n"
                "   - 'Cracking the Coding Interview' by Gayle Laakmann McDowell\n"
                "   - 'System Design Interview' by Alex Xu\n\n"
                "2. **Online Platforms**:\n"
                "   - LeetCode for coding practice\n"
                "   - HackerRank for algorithm challenges\n"
                "   - AlgoExpert for guided technical interview prep\n\n"
                "3. **Courses**:\n"
                "   - 'Master the Coding Interview: Data Structures + Algorithms' on Udemy\n"
                "   - 'Grokking the System Design Interview' on Educative.io\n\n"
                "4. **YouTube Channels**:\n"
                "   - Tech Dummies for system design\n"
                "   - Back To Back SWE for algorithms\n\n"
                "Practice explaining your thought process aloud while solving problems, as communication during technical interviews is just as important as finding the right solution."
            )
        elif "behavior" in input_text.lower() or "star" in input_text.lower():
            return (
                "Here are resources to improve your behavioral interview skills:\n\n"
                "1. **Books**:\n"
                "   - 'The STAR Interview' by Misha Yurchenko\n"
                "   - 'Knock 'em Dead Job Interview' by Martin Yate\n\n"
                "2. **Online Resources**:\n"
                "   - The Muse for common behavioral questions and example answers\n"
                "   - Big Interview for practice interviews with AI feedback\n\n"
                "3. **Courses**:\n"
                "   - LinkedIn Learning's 'Mastering Common Interview Questions'\n"
                "   - Coursera's 'How to Succeed in Your English Language Interview'\n\n"
                "4. **The STAR Method Framework**:\n"
                "   - **S**ituation: Describe the context\n"
                "   - **T**ask: Explain your responsibility\n"
                "   - **A**ction: Detail the steps you took\n"
                "   - **R**esult: Share the outcomes and learnings\n\n"
                "I recommend creating a document with 10-15 stories from your experience that can be adapted to answer different behavioral questions."
            )
        elif "present" in input_text.lower() or "communication" in input_text.lower():
            return (
                "Here are resources to improve your communication and presentation skills:\n\n"
                "1. **Books**:\n"
                "   - 'Talk Like TED' by Carmine Gallo\n"
                "   - 'Crucial Conversations' by Kerry Patterson et al.\n\n"
                "2. **Organizations**:\n"
                "   - Toastmasters International for public speaking practice\n"
                "   - Improv classes for thinking on your feet\n\n"
                "3. **Courses**:\n"
                "   - Coursera's 'Dynamic Public Speaking' from University of Washington\n"
                "   - edX's 'Effective Business Communication' from RITx\n\n"
                "4. **Practice Methods**:\n"
                "   - Record yourself answering questions and review your verbal habits\n"
                "   - Practice in front of a mirror to observe your body language\n"
                "   - Ask friends to conduct mock interviews and provide feedback\n\n"
                "Communication is a skill that improves with deliberate practice, so set aside time regularly to practice speaking clearly and concisely."
            )
        else:
            return (
                "Here are general resources to improve your interview skills:\n\n"
                "1. **All-Around Interview Prep**:\n"
                "   - Glassdoor for company-specific interview questions\n"
                "   - LinkedIn Premium for interview preparation features\n"
                "   - Pramp for peer-to-peer mock interviews\n\n"
                "2. **Books**:\n"
                "   - 'What Color Is Your Parachute?' by Richard Bolles\n"
                "   - 'How to Answer Interview Questions' by Peggy McKee\n\n"
                "3. **Podcasts**:\n"
                "   - 'Find Your Dream Job' by Mac's List\n"
                "   - 'The Ken Coleman Show' for career advice\n\n"
                "4. **YouTube Channels**:\n"
                "   - Linda Raynier for professional interview tips\n"
                "   - Andrew LaCivita for strategic career advice\n\n"
                "5. **Communities**:\n"
                "   - Reddit's r/interviews for peer advice\n"
                "   - Professional associations in your industry\n\n"
                "Remember that consistent practice with feedback is the most effective way to improve. Would you like more specific resources for a particular type of interview skill?"
            )
    
    def _generate_coaching_summary(self, context: AgentContext) -> str:
        """
        Generate a comprehensive coaching summary.
        
        Args:
            context: The current context of the conversation
            
        Returns:
            Coaching summary
        """
        # TODO: Replace with actual LLM-based analysis of the interview
        
        strengths = list(self.strength_areas)
        improvements = list(self.improvement_areas)
        
        if not strengths and not improvements:
            return (
                "I don't have enough information yet to provide a comprehensive coaching summary. "
                "As we continue with more interview practice, I'll be able to offer more personalized insights. "
                "Would you like to continue with the interview questions to gather more data?"
            )
        
        strength_items = "\n".join(f"- {s.title()}" for s in strengths) if strengths else "- Not enough data to determine specific strengths yet"
        improvement_items = "\n".join(f"- {s.title()}" for s in improvements) if improvements else "- Not enough data to determine specific improvement areas yet"
        
        summary = (
            "# Interview Coaching Summary\n\n"
            "## Strengths\n"
            f"{strength_items}\n\n"
            "## Areas for Improvement\n"
            f"{improvement_items}\n\n"
            "## Action Plan\n"
            "1. **Practice structured answers** using the STAR method (Situation, Task, Action, Result)\n"
            "2. **Record yourself** answering common interview questions and review for areas to improve\n"
            "3. **Research the companies** you're interviewing with to tailor your responses\n"
            "4. **Prepare concise stories** that highlight your relevant achievements\n\n"
            "## Next Steps\n"
            "Would you like to focus on practicing any specific type of questions or interview scenarios?"
        )
        
        return summary
    
    def _get_improvement_tip(self) -> str:
        """
        Get a personalized improvement tip based on identified areas for improvement.
        
        Returns:
            A specific improvement tip
        """
        if not self.improvement_areas:
            return ""
        
        # Select a random improvement area from those identified
        import random
        area = random.choice(list(self.improvement_areas))
        
        tips = {
            CoachingFocus.COMMUNICATION: "Before your next answer, take 3-5 seconds to mentally organize your response into an introduction, 2-3 key points, and a conclusion.",
            CoachingFocus.CONTENT: "For your next response, include at least one quantifiable achievement with specific metrics or results.",
            CoachingFocus.CONFIDENCE: "For your next answer, eliminate filler words like 'um' and 'like', and practice speaking at a measured, deliberate pace.",
            CoachingFocus.TECHNICAL_DEPTH: "In your next technical explanation, go one level deeper by explaining not just what you did but why you chose that approach and what alternatives you considered.",
            CoachingFocus.STORYTELLING: "Structure your next example as a story with a clear beginning (challenge), middle (your actions), and end (positive results).",
            CoachingFocus.SPECIFICITY: "In your next answer, include at least two specific examples with details about context, your actions, and measurable outcomes.",
            CoachingFocus.CONCISENESS: "Try to make your next response more concise by focusing on the most relevant details and limiting your answer to 1-2 minutes."
        }
        
        return tips.get(area, "Practice using the STAR method (Situation, Task, Action, Result) in your next response.")
    
    def _handle_interviewer_message(self, event: Event) -> None:
        """
        Handle messages from the interviewer agent.
        
        Args:
            event: The event containing the interviewer message
        """
        # Update context with interviewer message
        if self.current_context:
            message = event.data.get("response", "")
            self.current_context.add_message(
                "assistant", 
                message, 
                metadata={"source": "interviewer", "is_question": "?" in message}
            )
            
            # In real-time coaching mode, automatically provide feedback after user responds
            # This would be handled by the _handle_user_message method
    
    def _handle_user_message(self, event: Event) -> None:
        """
        Handle messages from the user.
        
        Args:
            event: The event containing the user message
        """
        # Update context with user message
        if self.current_context:
            self.current_context.add_message(
                "user", 
                event.data.get("response", "")
            )
            
            # In real-time coaching mode, provide immediate feedback
            if self.coaching_mode == CoachingMode.REAL_TIME:
                feedback = self._provide_real_time_coaching()
                
                # Publish feedback event
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type="coach_feedback",
                        source="coach_agent",
                        data={"feedback": feedback}
                    ))
    
    def _handle_interview_summary(self, event: Event) -> None:
        """
        Handle interview summary events.
        
        Args:
            event: The event containing the interview summary
        """
        # When an interview ends, provide comprehensive coaching in summary mode
        if self.coaching_mode == CoachingMode.SUMMARY:
            summary = self._provide_coaching_summary()
            
            # Publish coaching summary event
            if self.event_bus:
                self.event_bus.publish(Event(
                    event_type="coaching_summary",
                    source="coach_agent",
                    data={"summary": summary}
                ))
    
    def _handle_coaching_request(self, event: Event) -> None:
        """
        Handle explicit coaching requests.
        
        Args:
            event: The event containing the coaching request
        """
        # Process specific coaching requests
        request_type = event.data.get("request_type", "general")
        request_data = event.data.get("request_data", {})
        
        response = None
        
        if request_type == "targeted":
            focus_area = request_data.get("focus_area", "communication")
            context = request_data.get("context", self._extract_interview_context())
            response = self._generate_improvement_tips_tool(focus_area, context)
        elif request_type == "template":
            question_type = request_data.get("question_type", "behavioral")
            example_question = request_data.get("example_question", "Tell me about yourself")
            job_role = request_data.get("job_role", "software developer")
            response = self._generate_response_template_tool(question_type, example_question, job_role)
        elif request_type == "summary":
            response = self._provide_coaching_summary()
        
        # Publish response event if we generated one
        if response and self.event_bus:
            self.event_bus.publish(Event(
                event_type="coaching_response",
                source="coach_agent",
                data={"response": response}
            ))
    
    def _provide_real_time_coaching(self) -> str:
        """
        Provide real-time coaching feedback on the most recent exchange.
        
        Returns:
            Real-time coaching feedback
        """
        # Get last question and answer
        question = None
        answer = None
        
        # Scan conversation history in reverse to find the last Q&A pair
        history = self.current_context.conversation_history
        for i in range(len(history) - 1, 0, -1):
            if history[i]["role"] == "user":
                answer = history[i]["content"]
                # Look for the preceding question
                for j in range(i - 1, -1, -1):
                    if history[j]["role"] == "assistant" and history[j].get("metadata", {}).get("is_question", False):
                        question = history[j]["content"]
                        break
                if question:
                    break
        
        if not question or not answer:
            return "I don't have enough context to provide real-time coaching. Could you provide more details about what you'd like coaching on?"
        
        # Analyze the response using LangChain
        analysis = self._analyze_response_tool(question, answer)
        
        # Generate improvement tips for a focus area
        # For real-time coaching, we'll pick a focus area based on the analysis
        # This is a simplistic approach - in a real system we might use more sophisticated selection
        import random
        focus_area = random.choice(self.coaching_focus)
        
        tips = self._generate_improvement_tips_tool(focus_area, analysis)
        
        # Combine analysis and tips
        return f"{analysis}\n\n**Specific tips to improve your {focus_area}:**\n\n{tips}"
    
    def _provide_coaching_summary(self) -> str:
        """
        Provide a comprehensive coaching summary based on the entire interview.
        
        Returns:
            Coaching summary
        """
        # Extract relevant information from context
        interview_context = self._extract_interview_context()
        qa_pairs = self._extract_qa_pairs()
        
        # Generate summary using LangChain
        if qa_pairs:
            summary = self._create_coaching_summary_tool(interview_context, qa_pairs)
            return summary
        else:
            return "I don't have enough question and answer exchanges to provide a meaningful coaching summary yet."
    
    def _extract_interview_context(self) -> str:
        """
        Extract relevant context about the interview from the conversation history.
        
        Returns:
            Interview context as a string
        """
        if not self.current_context:
            return "No context available"
        
        metadata = self.current_context.metadata
        job_role = metadata.get("job_role", "Unknown position")
        
        return f"Interview for {job_role} position. The conversation includes multiple question-answer exchanges."
    
    def _extract_qa_pairs(self) -> List[Dict[str, str]]:
        """
        Extract question-answer pairs from the conversation history.
        
        Returns:
            List of question-answer pairs
        """
        if not self.current_context:
            return []
        
        qa_pairs = []
        current_question = None
        
        for message in self.current_context.conversation_history:
            if message["role"] == "assistant" and message.get("metadata", {}).get("is_question", False):
                current_question = message["content"]
            elif message["role"] == "user" and current_question:
                qa_pairs.append({"question": current_question, "answer": message["content"]})
                current_question = None
        
        return qa_pairs 