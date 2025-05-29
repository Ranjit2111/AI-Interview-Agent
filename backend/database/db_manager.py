"""
Database manager for handling all database operations with Supabase.
Provides session management, speech task tracking, and user data persistence.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from supabase import create_client, Client
from backend.config import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages all database operations for the AI Interviewer Agent.
    Handles session persistence, speech task tracking, and user management.
    """
    
    def __init__(self):
        """Initialize the database manager with Supabase client."""
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
        logger.info("DatabaseManager initialized with Supabase client")

    async def create_session(self, user_id: Optional[str] = None, 
                           initial_config: Optional[Dict] = None) -> str:
        """
        Create a new interview session.
        
        Args:
            user_id: Optional user ID to associate with the session
            initial_config: Optional initial session configuration
            
        Returns:
            str: The created session ID
        """
        try:
            session_data = {
                "user_id": user_id,
                "session_config": initial_config or {},
                "conversation_history": [],
                "per_turn_feedback_log": [],
                "session_stats": {},
                "status": "active"
            }
            
            result = self.supabase.table("interview_sessions").insert(session_data).execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]["session_id"]
                logger.info(f"Created new session: {session_id}")
                return str(session_id)
            else:
                raise Exception("Failed to create session - no data returned")
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def load_session_state(self, session_id: str) -> Optional[Dict]:
        """
        Load complete session state from database.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            Optional[Dict]: Session data if found, None otherwise
        """
        try:
            result = self.supabase.table("interview_sessions").select("*").eq("session_id", session_id).execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                logger.debug(f"Loaded session state for: {session_id}")
                return session_data
            else:
                logger.warning(f"Session not found: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading session state for {session_id}: {e}")
            return None

    async def save_session_state(self, session_id: str, state_data: Dict) -> bool:
        """
        Save session state to database.
        
        Args:
            session_id: The session ID to update
            state_data: The session data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract relevant fields for update
            update_data = {
                "session_config": state_data.get("session_config", {}),
                "conversation_history": state_data.get("conversation_history", []),
                "per_turn_feedback_log": state_data.get("per_turn_feedback_log", []),
                "final_summary": state_data.get("final_summary"),
                "session_stats": state_data.get("session_stats", {}),
                "status": state_data.get("status", "active"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("interview_sessions").update(update_data).eq("session_id", session_id).execute()
            
            if result.data:
                logger.debug(f"Saved session state for: {session_id}")
                return True
            else:
                logger.error(f"Failed to save session state for: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving session state for {session_id}: {e}")
            return False

    async def create_speech_task(self, session_id: str, task_type: str) -> str:
        """
        Create a new speech processing task.
        
        Args:
            session_id: The session ID this task belongs to
            task_type: Type of task ('stt_batch', 'tts', 'stt_stream')
            
        Returns:
            str: The created task ID
        """
        try:
            task_data = {
                "session_id": session_id,
                "task_type": task_type,
                "status": "processing",
                "progress_data": {},
                "result_data": None,
                "error_message": None
            }
            
            result = self.supabase.table("speech_tasks").insert(task_data).execute()
            
            if result.data and len(result.data) > 0:
                task_id = result.data[0]["task_id"]
                logger.info(f"Created speech task: {task_id} for session: {session_id}")
                return str(task_id)
            else:
                raise Exception("Failed to create speech task - no data returned")
                
        except Exception as e:
            logger.error(f"Error creating speech task: {e}")
            raise

    async def update_speech_task(self, task_id: str, status: str, 
                               progress_data: Optional[Dict] = None, 
                               result_data: Optional[Dict] = None,
                               error_message: Optional[str] = None) -> bool:
        """
        Update speech task progress and results.
        
        Args:
            task_id: The task ID to update
            status: New status ('processing', 'completed', 'error')
            progress_data: Optional progress information
            result_data: Optional result data
            error_message: Optional error message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if progress_data is not None:
                update_data["progress_data"] = progress_data
            if result_data is not None:
                update_data["result_data"] = result_data
            if error_message is not None:
                update_data["error_message"] = error_message
            
            result = self.supabase.table("speech_tasks").update(update_data).eq("task_id", task_id).execute()
            
            if result.data:
                logger.debug(f"Updated speech task: {task_id}")
                return True
            else:
                logger.error(f"Failed to update speech task: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating speech task {task_id}: {e}")
            return False

    async def get_speech_task(self, task_id: str) -> Optional[Dict]:
        """
        Get speech task by ID.
        
        Args:
            task_id: The task ID to retrieve
            
        Returns:
            Optional[Dict]: Task data if found, None otherwise
        """
        try:
            result = self.supabase.table("speech_tasks").select("*").eq("task_id", task_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting speech task {task_id}: {e}")
            return None

    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Clean up completed speech tasks older than specified hours.
        
        Args:
            older_than_hours: Remove tasks completed more than this many hours ago
            
        Returns:
            int: Number of tasks cleaned up
        """
        try:
            cutoff_time = datetime.utcnow().replace(microsecond=0)
            cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - older_than_hours)
            
            result = self.supabase.table("speech_tasks").delete().in_("status", ["completed", "error"]).lt("updated_at", cutoff_time.isoformat()).execute()
            
            count = len(result.data) if result.data else 0
            if count > 0:
                logger.info(f"Cleaned up {count} completed speech tasks")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
            return 0

    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get sessions for a specific user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of sessions to return
            
        Returns:
            List[Dict]: List of session data
        """
        try:
            result = self.supabase.table("interview_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return [] 