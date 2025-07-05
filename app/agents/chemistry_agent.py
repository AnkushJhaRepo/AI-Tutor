from .base_agent import BaseAgent
from ..models.enums import Subject
from ..models.schemas import AgentResponse
from ..utils.logger import logger

class ChemistryAgent(BaseAgent):
    def __init__(self):
        super().__init__()
    
    async def process_query(self, query: str) -> AgentResponse:
        """Process chemistry-related queries with direct answers."""
        try:
            prompt = f"""Please answer this chemistry question: {query}

Provide a clear, concise answer that:
1. Directly addresses the question
2. Includes relevant chemical concepts
3. Uses simple, understandable language
4. Gives practical examples where appropriate

Keep the response focused and to the point."""
            
            answer = await self._generate_response(prompt)
            
            if not answer or answer.startswith("Rate limit"):
                logger.warning(f"Failed to generate answer: {answer}")
                return AgentResponse(
                    agent_type=Subject.CHEMISTRY,
                    answer="I'm currently experiencing high demand. Please try again in a minute.",
                    tools_used=[],
                    confidence=0.0
                )
            
            return AgentResponse(
                agent_type=Subject.CHEMISTRY,
                answer=answer,
                tools_used=[],
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Error in ChemistryAgent: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_type=Subject.CHEMISTRY,
                answer=f"I encountered an error while processing your chemistry question: {str(e)}",
                tools_used=[],
                confidence=0.0
            )
