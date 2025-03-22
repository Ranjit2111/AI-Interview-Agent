"""
Agent orchestrator for coordinating multiple agents in the AI interview system.
This module manages communication between agents and determines which agent should respond to user input.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Type
from datetime import datetime

from backend.agents.base import BaseAgent, AgentContext
from backend.agents.interviewer import InterviewerAgent
from backend.agents.coach import CoachAgent
from backend.agents.skill_assessor import SkillAssessorAgent
from backend.utils.event_bus import Event, EventBus
from backend.models.interview import InterviewStyle


class OrchestratorMode(str):
    """Orchestrator operating modes that determine which agents are active."""
    INTERVIEW_ONLY = "interview_only"  # Only interviewer agent responds
    INTERVIEW_WITH_COACHING = "interview_with_coaching"  # Interviewer leads with coaching feedback
    COACHING_ONLY = "coaching_only"  # Only coach responds
    SKILL_ASSESSMENT = "skill_assessment"  # Targeted skill assessment
    FULL_FEEDBACK = "full_feedback"  # All agents provide feedback


class AgentOrchestrator:
    """
    Orchestrator that coordinates multiple agents.
    
    The orchestrator is responsible for:
    - Managing the lifecycle of multiple agents
    - Routing user input to appropriate agents
    - Aggregating responses from multiple agents
    - Determining when to switch between agents
    - Maintaining coherent conversation flow
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4-turbo",
        logger: Optional[logging.Logger] = None,
        mode: str = OrchestratorMode.INTERVIEW_WITH_COACHING,
        job_role: str = "",
        job_description: str = "",
        interview_style: InterviewStyle = InterviewStyle.FORMAL
    ):
        """
        Initialize the agent orchestrator.
        
        Args:
            api_key: API key for the language model
            model_name: Name of the language model to use
            logger: Logger for recording orchestrator activity
            mode: Operating mode that determines which agents are active
            job_role: Target job role for the interview
            job_description: Description of the job
            interview_style: Style of interview to conduct
        """
        self.api_key = api_key
        self.model_name = model_name
        self.logger = logger or logging.getLogger(__name__)
        self.mode = mode
        self.job_role = job_role
        self.job_description = job_description
        self.interview_style = interview_style
        
        # Create event bus for inter-agent communication
        self.event_bus = EventBus()
        
        # Create agents
        self.agents = {}
        self._initialize_agents()
        
        # Track which agent is currently active/responding
        self.active_agent_id = None
        
        # Track conversation contexts for each agent
        self.agent_contexts = {}
        
        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.user_id = None
        self.conversation_history = []
        
        # Command tracking
        self.commands = {
            "help": self._handle_help_command,
            "mode": self._handle_mode_command,
            "reset": self._handle_reset_command,
            "agents": self._handle_agents_command,
            "switch": self._handle_switch_command,
            "start": self._handle_start_command,
            "end": self._handle_end_command
        }
        
        # Subscribe to relevant events
        self.event_bus.subscribe("*", self._handle_event)
    
    def _initialize_agents(self) -> None:
        """
        Initialize all required agents based on the current mode.
        """
        # Create interviewer agent
        interviewer = InterviewerAgent(
            api_key=self.api_key,
            model_name=self.model_name,
            event_bus=self.event_bus,
            logger=self.logger,
            interview_style=self.interview_style,
            job_role=self.job_role,
            job_description=self.job_description
        )
        self.agents["interviewer"] = interviewer
        
        # Only create coach and skill assessor for modes that need them
        if self.mode in [OrchestratorMode.INTERVIEW_WITH_COACHING, 
                         OrchestratorMode.COACHING_ONLY,
                         OrchestratorMode.FULL_FEEDBACK]:
            coach = CoachAgent(
                api_key=self.api_key,
                model_name=self.model_name,
                event_bus=self.event_bus,
                logger=self.logger
            )
            self.agents["coach"] = coach
        
        if self.mode in [OrchestratorMode.SKILL_ASSESSMENT, 
                         OrchestratorMode.FULL_FEEDBACK]:
            skill_assessor = SkillAssessorAgent(
                api_key=self.api_key,
                model_name=self.model_name,
                event_bus=self.event_bus,
                logger=self.logger,
                job_role=self.job_role
            )
            self.agents["skill_assessor"] = skill_assessor
        
        # Set initial active agent based on mode
        if self.mode == OrchestratorMode.COACHING_ONLY:
            self.active_agent_id = "coach"
        elif self.mode == OrchestratorMode.SKILL_ASSESSMENT:
            self.active_agent_id = "skill_assessor"
        else:
            self.active_agent_id = "interviewer"
    
    def process_input(self, input_text: str, user_id: Optional[str] = None) -> str:
        """
        Process user input and route it to the appropriate agent(s).
        
        Args:
            input_text: The user's input text
            user_id: Identifier for the user (for session tracking)
            
        Returns:
            The agent's response
        """
        # Update user ID if provided
        if user_id:
            self.user_id = user_id
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": input_text,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Publish user input event
        self.event_bus.publish(Event(
            event_type="user_response",
            source="user",
            data={
                "response": input_text,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        # Check if this is a command
        if input_text.startswith("/"):
            command_parts = input_text[1:].split()
            command = command_parts[0].lower()
            args = command_parts[1:] if len(command_parts) > 1 else []
            
            if command in self.commands:
                return self.commands[command](args)
            else:
                return f"Unknown command: /{command}. Type /help for available commands."
        
        # Determine which agent(s) should respond
        if self.mode == OrchestratorMode.FULL_FEEDBACK:
            # In full feedback mode, get responses from all agents
            responses = self._get_all_agent_responses(input_text)
            return self._format_multi_agent_response(responses)
        else:
            # In other modes, use the active agent
            return self._get_active_agent_response(input_text)
    
    def _get_active_agent_response(self, input_text: str) -> str:
        """
        Get a response from the currently active agent.
        
        Args:
            input_text: The user's input text
            
        Returns:
            The active agent's response
        """
        agent_id = self.active_agent_id
        agent = self.agents.get(agent_id)
        
        if not agent:
            self.logger.error(f"Active agent {agent_id} not found")
            return "Sorry, there was an error processing your request. Please try again."
        
        # Get or create context for this agent
        context = self._get_agent_context(agent_id)
        
        # Get response from agent
        response = agent.process_input(input_text, context)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "agent": agent_id,
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return response
    
    def _get_all_agent_responses(self, input_text: str) -> Dict[str, str]:
        """
        Get responses from all active agents.
        
        Args:
            input_text: The user's input text
            
        Returns:
            Dictionary mapping agent ID to response
        """
        responses = {}
        
        for agent_id, agent in self.agents.items():
            # Get or create context for this agent
            context = self._get_agent_context(agent_id)
            
            # Get response from agent
            try:
                response = agent.process_input(input_text, context)
                responses[agent_id] = response
            except Exception as e:
                self.logger.error(f"Error getting response from agent {agent_id}: {e}")
                responses[agent_id] = f"[Agent {agent_id} encountered an error]"
        
        # Add combined response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "agent": "multi",
            "responses": responses,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return responses
    
    def _format_multi_agent_response(self, responses: Dict[str, str]) -> str:
        """
        Format responses from multiple agents into a single coherent response.
        
        Args:
            responses: Dictionary mapping agent ID to response
            
        Returns:
            Formatted multi-agent response
        """
        # Prioritize responses based on content and agent role
        has_interviewer = "interviewer" in responses and responses["interviewer"].strip()
        has_coach = "coach" in responses and responses["coach"].strip()
        has_skill_assessor = "skill_assessor" in responses and responses["skill_assessor"].strip()
        
        result_parts = []
        
        # Always include interviewer response first if available
        if has_interviewer:
            result_parts.append(f"👩‍💼 **Interviewer**: {responses['interviewer']}")
        
        # Add coaching feedback if substantial
        if has_coach and len(responses["coach"]) > 30:  # Only add if meaningful
            result_parts.append(f"\n\n🧠 **Coach**: {responses['coach']}")
        
        # Add skill assessment if substantial
        if has_skill_assessor and len(responses["skill_assessor"]) > 30:
            result_parts.append(f"\n\n📊 **Skill Assessment**: {responses['skill_assessor']}")
        
        if not result_parts:
            return "No response from agents. Please try again."
        
        return "\n".join(result_parts)
    
    def _get_agent_context(self, agent_id: str) -> AgentContext:
        """
        Get or create a context for an agent.
        
        Args:
            agent_id: The agent identifier
            
        Returns:
            Agent context
        """
        if agent_id not in self.agent_contexts:
            # Create new context
            self.agent_contexts[agent_id] = AgentContext(
                session_id=self.session_id,
                user_id=self.user_id
            )
        
        return self.agent_contexts[agent_id]
    
    def _handle_event(self, event: Event) -> None:
        """
        Handle events from the event bus.
        
        Args:
            event: The event to handle
        """
        # Log events for debugging
        self.logger.debug(f"Event received: {event.event_type} from {event.source}")
        
        # Handle specific event types
        if event.event_type == "interview_start":
            # Update session ID if provided
            if "session_id" in event.data:
                self.session_id = event.data["session_id"]
            
            # Reset contexts
            self.agent_contexts = {}
        
        elif event.event_type == "interview_end":
            # Clean up after interview ends
            pass
    
    def _handle_help_command(self, args: List[str]) -> str:
        """
        Handle the /help command.
        
        Args:
            args: Command arguments
            
        Returns:
            Help message
        """
        return (
            "Available commands:\n"
            "/help - Show this help message\n"
            "/mode [mode] - Show or set the orchestrator mode\n"
            "/reset - Reset the current session\n"
            "/agents - List available agents\n"
            "/switch [agent] - Switch to a different agent\n"
            "/start - Start a new interview\n"
            "/end - End the current interview"
        )
    
    def _handle_mode_command(self, args: List[str]) -> str:
        """
        Handle the /mode command.
        
        Args:
            args: Command arguments
            
        Returns:
            Mode information or confirmation
        """
        if not args:
            available_modes = [
                OrchestratorMode.INTERVIEW_ONLY,
                OrchestratorMode.INTERVIEW_WITH_COACHING,
                OrchestratorMode.COACHING_ONLY,
                OrchestratorMode.SKILL_ASSESSMENT,
                OrchestratorMode.FULL_FEEDBACK
            ]
            
            return (
                f"Current mode: {self.mode}\n\n"
                f"Available modes:\n" + 
                "\n".join([f"- {mode}" for mode in available_modes])
            )
        
        new_mode = args[0]
        valid_modes = [
            OrchestratorMode.INTERVIEW_ONLY,
            OrchestratorMode.INTERVIEW_WITH_COACHING,
            OrchestratorMode.COACHING_ONLY,
            OrchestratorMode.SKILL_ASSESSMENT,
            OrchestratorMode.FULL_FEEDBACK
        ]
        
        if new_mode not in valid_modes:
            return f"Invalid mode: {new_mode}. Valid modes are: {', '.join(valid_modes)}"
        
        # Change mode
        old_mode = self.mode
        self.mode = new_mode
        
        # Reinitialize agents for new mode
        self._initialize_agents()
        
        return f"Mode changed from {old_mode} to {self.mode}"
    
    def _handle_reset_command(self, args: List[str]) -> str:
        """
        Handle the /reset command.
        
        Args:
            args: Command arguments
            
        Returns:
            Reset confirmation
        """
        # Generate new session ID
        self.session_id = str(uuid.uuid4())
        
        # Reset contexts
        self.agent_contexts = {}
        
        # Reset conversation history
        self.conversation_history = []
        
        # Publish reset event
        self.event_bus.publish(Event(
            event_type="session_reset",
            source="orchestrator",
            data={
                "session_id": self.session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        return "Session reset. Ready for a new conversation."
    
    def _handle_agents_command(self, args: List[str]) -> str:
        """
        Handle the /agents command.
        
        Args:
            args: Command arguments
            
        Returns:
            Agent information
        """
        agent_info = []
        
        for agent_id, agent in self.agents.items():
            status = "active" if agent_id == self.active_agent_id else "inactive"
            agent_info.append(f"- {agent_id}: {status}")
        
        return f"Available agents:\n{chr(10).join(agent_info)}"
    
    def _handle_switch_command(self, args: List[str]) -> str:
        """
        Handle the /switch command.
        
        Args:
            args: Command arguments
            
        Returns:
            Switch confirmation or error
        """
        if not args:
            return "Please specify an agent to switch to. Available agents: " + ", ".join(self.agents.keys())
        
        agent_id = args[0]
        
        if agent_id not in self.agents:
            return f"Unknown agent: {agent_id}. Available agents: " + ", ".join(self.agents.keys())
        
        # Switch active agent
        old_agent = self.active_agent_id
        self.active_agent_id = agent_id
        
        return f"Switched from {old_agent} to {agent_id}"
    
    def _handle_start_command(self, args: List[str]) -> str:
        """
        Handle the /start command.
        
        Args:
            args: Command arguments
            
        Returns:
            Start confirmation
        """
        # Generate new session ID
        self.session_id = str(uuid.uuid4())
        
        # Reset contexts
        self.agent_contexts = {}
        
        # Reset conversation history
        self.conversation_history = []
        
        # Publish interview start event
        self.event_bus.publish(Event(
            event_type="interview_start",
            source="orchestrator",
            data={
                "session_id": self.session_id,
                "job_role": self.job_role,
                "job_description": self.job_description,
                "interview_style": self.interview_style.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        # Get initial response from interviewer
        if "interviewer" in self.agents:
            interviewer = self.agents["interviewer"]
            context = self._get_agent_context("interviewer")
            
            # Use empty string as initial input to get introduction
            response = interviewer.process_input("", context)
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "agent": "interviewer",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return response
        else:
            return "Interview started. What would you like to discuss?"
    
    def _handle_end_command(self, args: List[str]) -> str:
        """
        Handle the /end command.
        
        Args:
            args: Command arguments
            
        Returns:
            End confirmation
        """
        # Publish interview end event
        self.event_bus.publish(Event(
            event_type="interview_end",
            source="orchestrator",
            data={
                "session_id": self.session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        return "Interview ended. Type /start to begin a new interview." 