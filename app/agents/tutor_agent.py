from .base_agent import BaseAgent
from .math_agent import MathAgent
from .physics_agent import PhysicsAgent
from .chemistry_agent import ChemistryAgent
from ..models.enums import Subject
from ..utils.classifier import classifier
from ..models.schemas import AgentResponse, ToolResult
from ..utils.logger import logger
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..services.gemini_client import gemini_client

class TutorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.math_agent = MathAgent()
        self.physics_agent = PhysicsAgent()
        self.chemistry_agent = ChemistryAgent()
        self.classifier = gemini_client  # Use GeminiClient directly as classifier
        
        # Keywords for subject identification
        self.subject_keywords = {
            'math': ['math', 'mathematics', 'algebra', 'calculus', 'geometry', 'trigonometry', 'equation', 'function'],
            'physics': ['physics', 'force', 'motion', 'energy', 'velocity', 'acceleration', 'mass', 'gravity'],
            'chemistry': ['chemistry', 'chemical', 'molecule', 'atom', 'reaction', 'element', 'compound', 'solution']
        }
        
        # Cache for recent queries and their responses
        self.response_cache: Dict[str, tuple[AgentResponse, datetime]] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache responses for 5 minutes
    
    def _get_cached_response(self, query: str) -> Optional[AgentResponse]:
        """Get a cached response if available and not expired"""
        if query in self.response_cache:
            response, timestamp = self.response_cache[query]
            if datetime.now() - timestamp < self.cache_duration:
                logger.info("Using cached response")
                return response
            else:
                # Remove expired cache entry
                del self.response_cache[query]
        return None
    
    async def process_query(self, query: str) -> AgentResponse:
        """Process a user query and return a response."""
        try:
            # Classify the subject
            subject = await self.classifier.classify_subject(query)
            logger.info(f"Classified query as: {subject}")
            
            if subject == "unknown":
                logger.info("Question classified as non-subject")
                return AgentResponse(
                    agent_type="unknown",
                    answer="""I'm sorry, but I can only help with questions related to math, physics, or chemistry. 
                    
Your question doesn't seem to fit into these categories. Could you please rephrase your question to focus on one of these subjects?

If you believe this is a mistake, please try rephrasing your question to make the subject clearer."""
                )
            
            # Get the appropriate agent
            agent = self.get_agent(subject)
            if not agent:
                logger.error(f"No agent found for subject: {subject}")
                return AgentResponse(
                    agent_type=subject,
                    answer="I apologize, but I'm having trouble processing your question. Please try again."
                )
            
            # Process with the appropriate agent
            return await agent.process_query(query)
            
        except Exception as e:
            logger.error(f"Error in tutor agent: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_type="error",
                answer="I encountered an error while processing your question. Please try again."
            )
    
    def _identify_subject(self, query: str) -> str:
        """Identify the subject of the query based on keywords."""
        subject_scores = {
            'math': 0,
            'physics': 0,
            'chemistry': 0
        }
        
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    subject_scores[subject] += 1
        
        # Return the subject with the highest score, or None if no matches
        max_score = max(subject_scores.values())
        if max_score == 0:
            return None
        
        return max(subject_scores.items(), key=lambda x: x[1])[0]

    def get_agent(self, subject: str):
        """Get the appropriate agent for a subject."""
        agents = {
            "math": self.math_agent,
            "physics": self.physics_agent,
            "chemistry": self.chemistry_agent
        }
        return agents.get(subject)
