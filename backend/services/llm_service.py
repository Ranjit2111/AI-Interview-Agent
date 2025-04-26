"""
Provides a centralized service for accessing the Large Language Model.
"""

import os
import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel

from backend.config import get_logger

class LLMService:
    """
    Manages the initialization and access to the LLM instance.
    Ensures a single point of configuration for the language model.
    """
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "gemini-1.5-pro", # Updated default
                 temperature: float = 0.7):
        """
        Initializes the LLMService.

        Args:
            api_key (Optional[str]): Google API key. Reads from GOOGLE_API_KEY env var if None.
            model_name (str): The name of the Google Generative AI model to use.
            temperature (float): The sampling temperature for the LLM.
        """
        self.logger = get_logger(__name__)
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            self.logger.error("Google API key not found. Set GOOGLE_API_KEY environment variable.")
            raise ValueError("Google API key is required.")

        self.model_name = model_name
        self.temperature = temperature
        self._llm: Optional[BaseChatModel] = None

        self.logger.info(f"LLMService initialized with model: {self.model_name}")

    def get_llm(self) -> BaseChatModel:
        """
        Returns the initialized LLM instance, creating it if necessary.

        Returns:
            BaseChatModel: The initialized LangChain chat model instance.
        """
        if self._llm is None:
            try:
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=self.temperature,
                    convert_system_message_to_human=True # Gemini specific setting
                )
                self.logger.info(f"Initialized ChatGoogleGenerativeAI model: {self.model_name}")
            except Exception as e:
                self.logger.exception(f"Failed to initialize LLM: {e}")
                raise
        return self._llm

# Example usage (optional)
if __name__ == '__main__':
    try:
        llm_service = LLMService()
        llm_instance = llm_service.get_llm()
        print(f"Successfully obtained LLM instance: {type(llm_instance)}")
        
        # Simple invocation test
        # response = llm_instance.invoke("Hello!")
        # print(f"LLM Response: {response.content}")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An error occurred: {e}")
