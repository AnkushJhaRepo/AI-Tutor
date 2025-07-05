from .base_agent import BaseAgent
from ..tools.constant_lookup import ConstantLookup
from ..models.enums import Subject, ToolType
from ..models.schemas import AgentResponse, ToolResult
from ..utils.logger import log_agent_action, logger
from ..config import config

class PhysicsAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.constant_lookup = ConstantLookup(constants=config.PHYSICS_CONSTANTS)
    
    async def process_query(self, query: str) -> AgentResponse:
        """Process physics-related queries, using appropriate tools based on query intent."""
        tools_used = []
        
        try:
            # First, analyze if this needs constant lookup
            prompt = f"""Analyze this physics question: {query}
            
            You must respond with a JSON object in exactly this format:
            {{
                "needs_constant": true/false,
                "constant_name": "the name or symbol of the constant (e.g., 'Planck's constant' or 'h')"  // only if needs_constant is true
                "explanation_needed": "what physics concepts need to be explained"  // only if needs_constant is false
            }}

            Examples:
            For "What is Planck's constant?":
            {{
                "needs_constant": true,
                "constant_name": "Planck's constant"
            }}

            For "What is the speed of light?":
            {{
                "needs_constant": true,
                "constant_name": "c"
            }}

            For "How does gravity work?":
            {{
                "needs_constant": false,
                "explanation_needed": "the concept of gravitational force and its effects"
            }}

            IMPORTANT: 
            1. Your response must be valid JSON
            2. Do not include any text before or after the JSON
            3. Do not use markdown formatting
            4. Include exactly the fields shown above"""
            
            analysis = await self._generate_response(prompt)
            logger.info(f"Raw analysis response: {analysis}")
            
            # Try to parse the analysis
            import json
            try:
                # Clean up the response to ensure it's valid JSON
                analysis = analysis.strip()
                if analysis.startswith('```json'):
                    analysis = analysis[7:]
                if analysis.endswith('```'):
                    analysis = analysis[:-3]
                analysis = analysis.strip()
                
                logger.info(f"Cleaned analysis response: {analysis}")
                analysis_data = json.loads(analysis)
                logger.info(f"Parsed analysis data: {analysis_data}")
                
                # Check if we need constant lookup
                if analysis_data.get("needs_constant"):
                    constant_name = analysis_data.get("constant_name")
                    if constant_name:
                        # Look up the constant
                        constant_result = self.constant_lookup.lookup(constant_name)
                        if constant_result:
                            tools_used.append(ToolResult(
                                tool_type=ToolType.CONSTANT_LOOKUP,
                                input_data={"constant_name": constant_name},
                                result=constant_result,
                                success=True
                            ))
                            
                            # Generate explanation with constant value
                            prompt = f"""Please explain this physics concept: {query}
                            
                            The constant {constant_name} = {constant_result['value']} {constant_result['unit']}
                            
                            Provide a clear explanation that:
                            1. Explains what {constant_name} represents
                            2. Describes its significance in physics
                            3. Uses the value {constant_result['value']} {constant_result['unit']} in context
                            4. Explains how it relates to the question
                            
                            Keep the explanation clear and concise."""
                            
                            explanation = await self._generate_response(prompt)
                            
                            if not explanation or explanation.startswith("Rate limit"):
                                logger.warning(f"Failed to generate explanation: {explanation}")
                                # Fallback to basic response if explanation generation fails
                                answer = f"{constant_result['symbol']} = {constant_result['value']} {constant_result['unit']}\n\n{constant_result['description']}"
                            else:
                                answer = explanation
                                
                            return AgentResponse(
                                agent_type=Subject.PHYSICS,
                                answer=answer,
                                tools_used=tools_used,
                                confidence=0.9
                            )
                        else:
                            logger.warning(f"Constant lookup failed for {constant_name}: {constant_result}")
                            raise ValueError(f"Could not find constant: {constant_name}")
                
                # For non-constant questions, give a focused explanation
                prompt = f"""Please solve this physics problem: {query}
                Focus on explaining: {analysis_data.get('explanation_needed', 'the physics concepts involved')}
                Keep the explanation clear and concise."""
                
                explanation = await self._generate_response(prompt)
                
                if not explanation or explanation.startswith("Rate limit"):
                    logger.warning(f"Failed to generate explanation: {explanation}")
                    return AgentResponse(
                        agent_type=Subject.PHYSICS,
                        answer="I'm currently experiencing high demand. Please try again in a minute.",
                        tools_used=tools_used,
                        confidence=0.0
                    )
                
                return AgentResponse(
                    agent_type=Subject.PHYSICS,
                    answer=explanation,
                    tools_used=tools_used,
                    confidence=0.9
                )
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from analysis: {str(e)}\nAnalysis was: {analysis}")
                # Fallback to general explanation
                prompt = f"""Please solve this physics problem: {query}
                Provide a clear, concise explanation."""
                
                explanation = await self._generate_response(prompt)
                return AgentResponse(
                    agent_type=Subject.PHYSICS,
                    answer=explanation,
                    tools_used=tools_used,
                    confidence=0.8
                )
            except Exception as e:
                logger.warning(f"Could not parse analysis or lookup failed: {str(e)}")
                # Fallback to general explanation
                prompt = f"""Please solve this physics problem: {query}
                Provide a clear, concise explanation."""
                
                explanation = await self._generate_response(prompt)
                return AgentResponse(
                    agent_type=Subject.PHYSICS,
                    answer=explanation,
                    tools_used=tools_used,
                    confidence=0.8
                )
            
        except Exception as e:
            logger.error(f"Error in PhysicsAgent: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_type=Subject.PHYSICS,
                answer=f"I encountered an error while processing your physics question: {str(e)}",
                tools_used=tools_used,
                confidence=0.0
            )
