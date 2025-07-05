from .base_agent import BaseAgent
from ..tools.calculator import Calculator
from ..models.enums import Subject, ToolType
from ..models.schemas import AgentResponse, ToolResult
from ..utils.logger import log_agent_action, logger

class MathAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.calculator = Calculator()
    
    async def process_query(self, query: str) -> AgentResponse:
        """Process math-related queries, using calculator for any calculations needed."""
        tools_used = []
        logger.info(f"MathAgent processing query: {query}")
        
        try:
            # Extract any numbers and operations from the query
            prompt = f"""Given this math question: {query}
            
            Extract any calculations that need to be performed. For example:
            - "What is 5 + 3?" -> "5 + 3"
            - "Calculate the area of a rectangle with length 5.2m and width 3.8m" -> "5.2 * 3.8"
            - "What is 20% of 150?" -> "150 * 0.2"
            
            Respond with ONLY the expression to calculate, or 'no calculation needed' if none found."""
            
            logger.info("Extracting mathematical expression from query...")
            expression = await self._generate_response(prompt)
            logger.info(f"Extracted expression: {expression}")
            
            if expression and expression.lower() != "no calculation needed":
                logger.info("Calculation needed, attempting to use calculator...")
                try:
                    # Use calculator tool
                    logger.info(f"Calculating expression: {expression}")
                    result = self.calculator.calculate(expression)
                    logger.info(f"Calculator result: {result}")
                    
                    tools_used.append(ToolResult(
                        tool_type=ToolType.CALCULATOR,
                        input_data={"expression": expression},
                        result=result,
                        success=True
                    ))
                    logger.info("Calculator tool used successfully")
                    
                    # Generate explanation with the calculation result
                    prompt = f"""Please solve this math problem: {query}
                    
                    The calculation needed is: {expression} = {result}
                    
                    Provide a complete mathematical solution that includes:
                    1. Mathematical Concepts Involved
                    2. Step-by-Step Solution
                    3. Verification and Reasoning
                    4. Final Answer
                    
                    Make sure to explain the mathematical concepts and reasoning clearly."""
                    
                except Exception as calc_error:
                    logger.warning(f"Calculator error: {str(calc_error)}")
                    logger.info("Falling back to explanation without calculation")
                    # Fall back to explanation without calculation
                    prompt = f"""Please solve this math problem: {query}
                    
                    I tried to calculate {expression} but encountered an error.
                    
                    Provide a complete mathematical solution that includes:
                    1. Mathematical Concepts Involved
                    2. Step-by-Step Solution
                    3. Verification and Reasoning
                    4. Final Answer
                    
                    Make sure to explain the mathematical concepts and reasoning clearly."""
            else:
                logger.info("No calculation needed, generating explanation only")
                # No calculation needed, just explain the math
                prompt = f"""Please solve this math problem: {query}
                
                Provide a complete mathematical solution that includes:
                1. Mathematical Concepts Involved
                2. Step-by-Step Solution
                3. Verification and Reasoning
                4. Final Answer
                
                Make sure to explain the mathematical concepts and reasoning clearly."""
            
            logger.info(f"Generating response with prompt: {prompt[:100]}...")
            explanation = await self._generate_response(prompt)
            logger.info("Generated explanation successfully")
            
            if not explanation or explanation.startswith("Rate limit"):
                logger.warning(f"Failed to generate explanation: {explanation}")
                return AgentResponse(
                    agent_type=Subject.MATH,
                    answer="I'm currently experiencing high demand. Please try again in a minute.",
                    tools_used=tools_used,
                    confidence=0.0
                )
            
            logger.info("Returning successful response")
            return AgentResponse(
                agent_type=Subject.MATH,
                answer=explanation,
                tools_used=tools_used,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Error in MathAgent: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_type=Subject.MATH,
                answer=f"I encountered an error while processing your math question: {str(e)}",
                tools_used=tools_used,
                confidence=0.0
            )
