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

    # === User Authentication Methods ===

    async def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth.
        
        Args:
            email: User email
            password: User password
            name: User full name
            
        Returns:
            Dict: Auth data including tokens and user info
            
        Raises:
            Exception: If registration fails
        """
        try:
            # Register user with Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if not user_data or not session_data:
                raise Exception("User registration failed - no user or session data returned")
            
            # Create user record in our users table
            user_record = {
                "id": user_data.id,
                "email": email,
                "name": name,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("users").insert(user_record).execute()
            
            # Format response
            return {
                "access_token": session_data.access_token,
                "refresh_token": session_data.refresh_token,
                "user": {
                    "id": user_data.id,
                    "email": email,
                    "name": name,
                    "created_at": user_record["created_at"]
                }
            }
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise Exception(f"User registration failed: {str(e)}")

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user with Supabase Auth.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict: Auth data including tokens and user info
            
        Raises:
            Exception: If login fails
        """
        try:
            # Login user with Supabase Auth
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if not user_data or not session_data:
                raise Exception("User login failed - no user or session data returned")
            
            # Get user's name from our users table
            user_record = await self.get_user(user_data.id)
            user_name = user_record.get("name", "") if user_record else ""
            
            # Format response
            return {
                "access_token": session_data.access_token,
                "refresh_token": session_data.refresh_token,
                "user": {
                    "id": user_data.id,
                    "email": user_data.email,
                    "name": user_name,
                    "created_at": user_data.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"User login failed: {e}")
            raise Exception(f"User login failed: {str(e)}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict: New auth data including tokens and user info
            
        Raises:
            Exception: If token refresh fails
        """
        try:
            # Refresh token with Supabase Auth
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if not user_data or not session_data:
                raise Exception("Token refresh failed - no user or session data returned")
            
            # Format response
            return {
                "access_token": session_data.access_token,
                "refresh_token": session_data.refresh_token,
                "user": {
                    "id": user_data.id,
                    "email": user_data.email,
                    "created_at": user_data.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise Exception(f"Token refresh failed: {str(e)}")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        try:
            # Get user from our users table
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    # === Session Management Methods ===

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

    # === Speech Task Methods ===

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
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
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