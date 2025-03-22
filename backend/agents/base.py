"""
Base agent module.
Provides the foundation for all specialized agents in the system.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, Tool
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.tools.render import format_tool_to_openai_function
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.utils.event_bus import EventBus, Event


class AgentContext:
    """
    Context object for agents to maintain state across interactions.
    """
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (user, agent, system)
            content: The content of the message
            metadata: Optional metadata for the message
        """
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        self.last_updated = datetime.utcnow()
    
    def get_history_as_text(self, max_tokens: Optional[int] = None) -> str:
        """
        Get the conversation history as a formatted text string.
        
        Args:
            max_tokens: Optional maximum number of tokens to include
            
        Returns:
            The conversation history as a formatted string
        """
        history = ""
        for message in self.conversation_history:
            history += f"{message['role']}: {message['content']}\n\n"
        
        # TODO: Implement token truncation if max_tokens is specified
        return history.strip()
    
    def get_langchain_messages(self) -> List[Any]:
        """
        Convert conversation history to LangChain message format.
        
        Returns:
            List of LangChain message objects
        """
        messages = []
        for message in self.conversation_history:
            if message["role"] == "user":
                messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                messages.append(AIMessage(content=message["content"]))
            elif message["role"] == "system":
                messages.append(SystemMessage(content=message["content"]))
        return messages
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        
        Returns:
            A dictionary representation of the context
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        """
        Create a context object from a dictionary.
        
        Args:
            data: A dictionary representation of the context
            
        Returns:
            An AgentContext object
        """
        context = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id")
        )
        context.conversation_history = data["conversation_history"]
        context.metadata = data["metadata"]
        context.created_at = datetime.fromisoformat(data["created_at"])
        context.last_updated = datetime.fromisoformat(data["last_updated"])
        return context


class BaseAgent(ABC):
    """
    Base agent class that all specialized agents inherit from.
    """
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gemini-1.5-pro",
                 planning_interval: int = 0,
                 event_bus: Optional[EventBus] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the base agent.
        
        Args:
            api_key: Google Gemini API key (if None, will use environment variable)
            model_name: Name of the Gemini model to use (default: gemini-1.5-pro)
            planning_interval: How often to run planning steps (0 = disabled)
            event_bus: Event bus for inter-agent communication
            logger: Logger for the agent
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        self.model_name = model_name
        self.planning_interval = planning_interval
        self.step_count = 0
        
        # Set up LLM with Google Gemini
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, 
            google_api_key=self.api_key,
            temperature=0.7,
            convert_system_message_to_human=True  # Gemini handles system messages differently
        )
        
        # Set up event bus
        self.event_bus = event_bus or EventBus()
        
        # Set up logger
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Initialize state
        self.current_context: Optional[AgentContext] = None
        
        # Initialize LangChain tools
        self.tools = self._initialize_tools()
        
        # Initialize agent executor if tools are available
        if self.tools:
            self._setup_agent_executor()
    
    def _initialize_tools(self) -> List[Tool]:
        """
        Initialize the tools for the agent.
        Override in subclasses to provide specific tools.
        
        Returns:
            List of LangChain tools
        """
        return []
    
    def _setup_agent_executor(self) -> None:
        """
        Set up the LangChain agent executor.
        Called after tools are initialized.
        """
        if not self.tools:
            return
        
        # Convert tools to OpenAI functions format
        functions = [format_tool_to_openai_function(t) for t in self.tools]
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Set up the agent chain
        self.agent_chain = (
            RunnableParallel({
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(x["intermediate_steps"]),
            })
            | prompt
            | self.llm
            | OpenAIFunctionsAgentOutputParser()
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent_chain,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the agent.
        Override in subclasses to provide specific system prompts.
        
        Returns:
            System prompt string
        """
        return (
            "You are an AI interview assistant. Your goal is to help users prepare for job interviews. "
            "You should be professional, helpful, and constructive in your responses."
        )
    
    def create_context(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> AgentContext:
        """
        Create a new context for the agent.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            user_id: Optional user ID
            
        Returns:
            A new AgentContext object
        """
        session_id = session_id or str(uuid.uuid4())
        self.current_context = AgentContext(session_id=session_id, user_id=user_id)
        return self.current_context
    
    def load_context(self, context: AgentContext) -> None:
        """
        Load an existing context.
        
        Args:
            context: The context to load
        """
        self.current_context = context
    
    @abstractmethod
    def process_input(self, input_text: str, context: Optional[AgentContext] = None) -> str:
        """
        Process user input and generate a response.
        
        Args:
            input_text: The user input text
            context: Optional context (uses self.current_context if not provided)
            
        Returns:
            The agent's response
        """
        pass
    
    def process_with_langchain(self, input_text: str, context: AgentContext) -> Dict[str, Any]:
        """
        Process input using LangChain agent if available.
        
        Args:
            input_text: The user input text
            context: The conversation context
            
        Returns:
            Response from the LangChain agent
        """
        if not hasattr(self, 'agent_executor') or not self.agent_executor:
            raise ValueError("LangChain agent not initialized")
        
        # Extract chat history from context
        chat_history = context.get_langchain_messages()
        
        # Run the agent
        return self.agent_executor.invoke({
            "input": input_text,
            "chat_history": chat_history,
            "intermediate_steps": []
        })
    
    def _should_plan(self) -> bool:
        """
        Determine if planning should be executed based on the planning interval.
        
        Returns:
            True if planning should be executed, False otherwise
        """
        if self.planning_interval <= 0:
            return False
        
        return self.step_count % self.planning_interval == 0
    
    def _run_planning_step(self, context: AgentContext) -> Dict[str, Any]:
        """
        Run a planning step to update the agent's understanding and plan.
        
        Args:
            context: The current context
            
        Returns:
            The planning result
        """
        # Default implementation - can be overridden in subclasses
        return {
            "planning_completed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish an event to the event bus.
        
        Args:
            event_type: The type of event
            data: The event data
        """
        event = Event(
            event_type=event_type,
            source=self.__class__.__name__,
            data=data
        )
        self.event_bus.publish(event)
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: The callback function to call when an event is received
        """
        self.event_bus.subscribe(event_type, callback) 