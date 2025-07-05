from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .enums import Subject, ToolType

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ToolResult(BaseModel):
    tool_type: ToolType
    input_data: Dict[str, Any]
    result: Any
    success: bool
    error_message: Optional[str] = None

class AgentResponse(BaseModel):
    agent_type: Subject
    answer: str
    tools_used: List[ToolResult] = []
    confidence: Optional[float] = None

class QueryResponse(BaseModel):
    question: str
    subject_identified: Subject
    response: AgentResponse
    session_id: Optional[str] = None
    timestamp: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

class HistoryEntry(BaseModel):
    question: str
    response: QueryResponse
    timestamp: str