import google.generativeai as genai
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import asyncio
import aiohttp
from app.config import config
from app.utils.logger import logger

class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False

    async def allow_request(self) -> bool:
        if not self.is_open:
            return True
        
        if self.last_failure_time and (datetime.now() - self.last_failure_time).seconds >= self.reset_timeout:
            self.is_open = False
            self.failures = 0
            return True
        return False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.warning("Circuit breaker opened due to too many failures")

    def record_success(self):
        self.failures = 0
        self.is_open = False

class GeminiClient:
    def __init__(self):
        config.validate()  # Validate required config
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Initialized Gemini client with model: {config.GEMINI_MODEL}")
        
        # Connection pool for API calls
        self.session = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.CIRCUIT_BREAKER_THRESHOLD,
            reset_timeout=config.CIRCUIT_BREAKER_TIMEOUT
        )
        
        # Track request counts and timestamps
        self.request_tracker: Dict[str, list] = {
            'classify': [],
            'generate': []
        }
        
        # Use config timeouts
        self.timeout = config.TIMEOUT
        self.max_retries = 2
        self.connection_timeout = config.CONNECTION_TIMEOUT
        
    async def _ensure_session(self):
        """Ensure we have an active aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(
                    total=self.timeout,
                    connect=self.connection_timeout
                )
            )

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _execute_with_timeout(self, coro, timeout_msg: str) -> str:
        """Execute a coroutine with timeout and circuit breaker."""
        if not await self.circuit_breaker.allow_request():
            logger.warning("Request blocked by circuit breaker")
            return "Service temporarily unavailable. Please try again in a minute."

        try:
            await self._ensure_session()
            async with asyncio.timeout(self.connection_timeout):
                response = await asyncio.wait_for(coro, timeout=self.timeout)
            self.circuit_breaker.record_success()
            return response
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Timeout while {timeout_msg}: {str(e)}")
            return "Request timed out. Please try again."
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Error during {timeout_msg}: {str(e)}")
            raise

    def _check_rate_limits(self, request_type: str) -> Optional[str]:
        """Check if we're hitting rate limits and return a user-friendly message if we are"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.request_tracker[request_type] = [
            ts for ts in self.request_tracker[request_type] 
            if ts > one_minute_ago
        ]
        
        # Use config rate limit
        if len(self.request_tracker[request_type]) >= config.RATE_LIMIT_PER_MINUTE:
            retry_after = 60 - (now - self.request_tracker[request_type][0]).seconds
            return f"I'm currently experiencing high demand. Please try again in {retry_after} seconds."

        return None

    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Gemini API with proper connection handling."""
        for attempt in range(self.max_retries + 1):
            try:
                # Check rate limits
                rate_limit_msg = self._check_rate_limits('generate')
                if rate_limit_msg:
                    return rate_limit_msg

                full_prompt = f"Context: {context}\n\nQuery: {prompt}" if context else prompt
                logger.info(f"Sending prompt to Gemini: {full_prompt[:100]}...")
                
                self.request_tracker['generate'].append(datetime.now())
                
                async def _generate():
                    try:
                        response = await asyncio.to_thread(
                            self.model.generate_content,
                            full_prompt,
                            generation_config={
                                "temperature": 0.7,
                                "top_p": 0.8,
                                "top_k": 40,
                            }
                        )
                        return response
                    except Exception as e:
                        if "429" in str(e):
                            raise
                        logger.error(f"Gemini API error: {str(e)}")
                        return None

                response = await self._execute_with_timeout(
                    _generate(),
                    "generating response from Gemini"
                )
                
                if isinstance(response, str):  # Error message
                    return response
                
                if response and response.text:
                    logger.info("Successfully received response from Gemini")
                    return response.text.strip()
                
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                    
                return "I apologize, but I couldn't generate a response. Please try again."
                    
            except Exception as e:
                logger.error(f"Error calling Gemini API (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                
                if "429" in str(e):
                    retry_seconds = 60
                    if "retry_delay" in str(e):
                        try:
                            retry_seconds = int(str(e).split('seconds: ')[-1].split()[0])
                        except:
                            pass
                    return f"I'm currently experiencing high demand. Please try again in {retry_seconds} seconds."
                
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                    
                return "I encountered an error while processing your question. Please try again."
        
        return "I'm having trouble processing your request. Please try again."
    
    async def classify_subject(self, question: str) -> str:
        """Use Gemini to classify the subject of a question using natural language understanding"""
        try:
            # Check rate limits before making request
            rate_limit_msg = self._check_rate_limits('classify')
            if rate_limit_msg:
                return "unknown"  # Return unknown on rate limit to prevent further processing

            classification_prompt = f"""You are a subject classifier for an AI tutoring system. Your task is to analyze the following question and determine which subject it belongs to: math, physics, or chemistry.

Question: {question}

Consider the following guidelines:
- Math questions involve calculations, equations, algebra, geometry, calculus, etc.
- Physics questions involve forces, energy, motion, waves, electricity, etc.
- Chemistry questions involve elements, reactions, compounds, molecules, etc.

Respond with ONLY one word: math, physics, or chemistry. If the question doesn't clearly fit any of these subjects, respond with 'unknown'."""
            
            # Track this request
            self.request_tracker['classify'].append(datetime.now())
            
            # Use await with generate_response
            response = await self.generate_response(classification_prompt)
            
            # Clean and validate response
            subject = response.lower().strip()
            valid_subjects = ["math", "physics", "chemistry", "unknown"]
            
            if subject in valid_subjects:
                logger.info(f"Gemini classified question as: {subject}")
                return subject
            else:
                logger.warning(f"Invalid classification response: {subject}")
                return "unknown"
                
        except Exception as e:
            logger.error(f"Error in subject classification: {str(e)}")
            return "unknown"

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Global instance
gemini_client = GeminiClient()