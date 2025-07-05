from abc import ABC, abstractmethod
import google.generativeai as genai
import asyncio
from ..config import config
from ..utils.logger import logger

class BaseAgent(ABC):
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        if not config.GEMINI_MODEL:
            raise ValueError("GEMINI_MODEL not found in environment variables")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        # Use model from config
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Initialized BaseAgent with model: {config.GEMINI_MODEL}")
    
    @abstractmethod
    async def process_query(self, query: str) -> str:
        """Process the user query and return a response."""
        pass
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate a response using the Gemini model."""
        try:
            logger.info(f"Sending prompt to Gemini: {prompt[:100]}...")
            # Add safety checks and model configuration
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
            }
            
            # Create a coroutine for the API call
            async def _generate():
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=generation_config
                )
                return response
            
            # Execute with timeout
            response = await asyncio.wait_for(_generate(), timeout=30.0)
            
            if not response or not response.text:
                logger.error("Empty response from Gemini")
                return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            return response.text.strip()
        except asyncio.TimeoutError:
            logger.error("Timeout while generating response from Gemini")
            return "I'm taking longer than expected to process your request. Please try again in a moment."
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            # Return a more specific error message
            if "404" in str(e):
                return f"I apologize, but there seems to be an issue with the AI model configuration. The model '{config.GEMINI_MODEL}' was not found. Please check your API settings."
            if "429" in str(e):
                return "I'm currently experiencing high demand. Please try again in a minute or contact anujsanjaysinghwork@gmail.com for assistance."
            return "I apologize, but I encountered an error while processing your request. Please try again later."
