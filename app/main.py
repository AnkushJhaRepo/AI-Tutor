from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
import uuid
import asyncio
from typing import Optional, Dict, Set
from contextlib import asynccontextmanager

from app.agents.tutor_agent import TutorAgent
from app.models.schemas import QueryRequest, QueryResponse, AgentResponse
from app.utils.logger import logger
from app.config import config

# Global state
active_requests: Dict[str, dict] = {}
active_tasks: Set[asyncio.Task] = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting up AI Tutor application...")
    yield
    # Shutdown
    logger.info("Shutting down AI Tutor application...")
    # Cancel all active tasks
    for task in active_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    active_tasks.clear()
    active_requests.clear()

app = FastAPI(title="AI Tutor API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Initialize the tutor agent
tutor_agent = TutorAgent()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

async def process_query_with_timeout(query: str, request_id: str) -> AgentResponse:
    """Process a query with proper timeout and cleanup."""
    try:
        # Create a task for the query processing
        task = asyncio.create_task(tutor_agent.process_query(query))
        active_tasks.add(task)
        
        try:
            # Wait for the task with timeout
            response = await asyncio.wait_for(task, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            # Cancel the task if it times out
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise
        finally:
            # Clean up the task
            active_tasks.discard(task)
    except Exception as e:
        # Ensure the task is cleaned up on any error
        if task in active_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            active_tasks.discard(task)
        raise

@app.post("/api/query", response_model=QueryResponse)
async def process_query(
    query: QueryRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Process a user query and return a response."""
    request_id = str(uuid.uuid4())
    active_requests[request_id] = {
        "start_time": datetime.utcnow(),
        "status": "processing"
    }
    
    try:
        # Process query with config timeout
        agent_response = await asyncio.wait_for(
            tutor_agent.process_query(query.question),
            timeout=config.TIMEOUT
        )
        
        # Update request status
        active_requests[request_id]["status"] = "completed"
        
        # Create response
        response = QueryResponse(
            question=query.question,
            subject_identified=agent_response.agent_type,
            response=agent_response,
            session_id=query.session_id or str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Processed query: {query.question} | Subject: {agent_response.agent_type}")
        logger.info(f"Tools used in response: {agent_response.tools_used}")
        return response
        
    except asyncio.TimeoutError:
        active_requests[request_id]["status"] = "timeout"
        logger.error(f"Request timeout for query: {query.question}")
        raise HTTPException(
            status_code=504,
            detail="The request took too long to process. Please try again."
        )
    except Exception as e:
        # Update request status
        active_requests[request_id]["status"] = "error"
        active_requests[request_id]["error"] = str(e)
        
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        
        if isinstance(e, HTTPException):
            raise e
            
        # Handle specific error types
        error_msg = str(e)
        if "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="I'm currently experiencing high demand. Please try again in a minute."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail="The request took too long to process. Please try again."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your question. Please try again."
            )
    finally:
        # Schedule cleanup with config delay
        background_tasks.add_task(cleanup_request, request_id)

async def cleanup_request(request_id: str):
    """Clean up a specific request after a delay."""
    try:
        await asyncio.sleep(config.REQUEST_CLEANUP_DELAY)
        if request_id in active_requests:
            del active_requests[request_id]
    except Exception as e:
        logger.error(f"Error cleaning up request {request_id}: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint with request status."""
    try:
        # Get active request stats without processing a test query
        active_count = len([r for r in active_requests.values() if r["status"] == "processing"])
        timeout_count = len([r for r in active_requests.values() if r["status"] == "timeout"])
        error_count = len([r for r in active_requests.values() if r["status"] == "error"])
        
        # Use a lower threshold for Vercel
        max_active_requests = 5 if config.IS_VERCEL else 10
        
        if active_count > max_active_requests:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "overloaded",
                    "active_requests": active_count,
                    "recent_timeouts": timeout_count,
                    "recent_errors": error_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return {
            "status": "healthy",
            "environment": config.ENVIRONMENT,
            "is_vercel": config.IS_VERCEL,
            "timestamp": datetime.utcnow().isoformat(),
            "active_requests": active_count,
            "recent_timeouts": timeout_count,
            "recent_errors": error_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    return response 