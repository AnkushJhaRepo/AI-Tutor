from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import HistoryEntry, QueryResponse
from app.utils.logger import logger

class HistoryManager:
    def __init__(self):
        # In-memory storage for conversation history
        # In production, this would be replaced with a database
        self.sessions: Dict[str, List[HistoryEntry]] = {}
        self.max_history_per_session = 50  # Limit to prevent memory issues
    
    def add_entry(self, session_id: str, question: str, response: QueryResponse):
        """Add a new entry to the conversation history"""
        try:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            
            entry = HistoryEntry(
                question=question,
                response=response,
                timestamp=datetime.now().isoformat()
            )
            
            self.sessions[session_id].append(entry)
            
            # Trim history if it gets too long
            if len(self.sessions[session_id]) > self.max_history_per_session:
                self.sessions[session_id] = self.sessions[session_id][-self.max_history_per_session:]
            
            logger.info(f"Added history entry for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error adding history entry: {str(e)}")
    
    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[HistoryEntry]:
        """Get conversation history for a session"""
        try:
            if session_id not in self.sessions:
                return []
            
            history = self.sessions[session_id]
            
            if limit:
                return history[-limit:]
            
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving history: {str(e)}")
            return []
    
    def get_context(self, session_id: str, limit: int = 3) -> str:
        """Get recent conversation context for better responses"""
        try:
            recent_history = self.get_history(session_id, limit)
            
            if not recent_history:
                return ""
            
            context_parts = []
            for entry in recent_history:
                context_parts.append(f"Previous Q: {entry.question}")
                context_parts.append(f"Previous A: {entry.response.response.answer}")
            
            context = "\n".join(context_parts)
            return f"Recent conversation context:\n{context}\n"
            
        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            return ""
    
    def clear_session(self, session_id: str):
        """Clear history for a specific session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Cleared history for session {session_id}")
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self.sessions)
    
    def get_total_entries(self) -> int:
        """Get total number of history entries across all sessions"""
        return sum(len(history) for history in self.sessions.values())

# Global instance
history_manager = HistoryManager() 