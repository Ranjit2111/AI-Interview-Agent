"""
Mock Database Manager for Development

This module provides a mock implementation of the database manager
that works without Supabase for development and testing purposes.
"""

import uuid
import logging
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from backend.config import get_logger

logger = get_logger(__name__)

class MockDatabaseManager:
    """Mock database manager for development."""
    
    def __init__(self):
        """Initialize mock database."""
        self.users = {}  # In-memory user storage
        self.sessions = {}  # In-memory session storage
        self.speech_tasks = {}  # In-memory speech task storage
        self.jwt_secret = "development_secret_key_not_for_production"
        logger.info("Initialized MockDatabaseManager")
    
    def _generate_token(self, user_id: str) -> str:
        """Generate a JWT token for the user."""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    async def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """
        Register a new user (mock implementation).
        
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
            # Check if user already exists
            for user in self.users.values():
                if user["email"] == email:
                    raise Exception(f"User with email {email} already exists")
            
            # Create new user
            user_id = str(uuid.uuid4())
            user_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "password": password,  # In real app, this would be hashed
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.users[user_id] = user_data
            
            # Generate tokens
            access_token = self._generate_token(user_id)
            refresh_token = str(uuid.uuid4())  # Simple refresh token for mock
            
            logger.info(f"Mock user registered: {email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "created_at": user_data["created_at"]
                }
            }
            
        except Exception as e:
            logger.error(f"Mock user registration failed: {e}")
            raise Exception(f"User registration failed: {str(e)}")

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user (mock implementation).
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict: Auth data including tokens and user info
            
        Raises:
            Exception: If login fails
        """
        try:
            # Find user by email
            user_data = None
            for user in self.users.values():
                if user["email"] == email:
                    user_data = user
                    break
            
            if not user_data:
                raise Exception("Invalid email or password")
            
            # Check password (in real app, this would be hashed comparison)
            if user_data["password"] != password:
                raise Exception("Invalid email or password")
            
            # Generate tokens
            access_token = self._generate_token(user_data["id"])
            refresh_token = str(uuid.uuid4())  # Simple refresh token for mock
            
            logger.info(f"Mock user logged in: {email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user_data["id"],
                    "email": email,
                    "name": user_data["name"],
                    "created_at": user_data["created_at"]
                }
            }
            
        except Exception as e:
            logger.error(f"Mock user login failed: {e}")
            raise Exception(f"User login failed: {str(e)}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token (mock implementation).
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict: New auth data including tokens and user info
            
        Raises:
            Exception: If token refresh fails
        """
        try:
            # In a real implementation, you'd validate the refresh token
            # For mock, we'll just generate new tokens for the first user
            if not self.users:
                raise Exception("No users found")
            
            user_data = list(self.users.values())[0]  # Get first user for mock
            
            # Generate new tokens
            access_token = self._generate_token(user_data["id"])
            new_refresh_token = str(uuid.uuid4())
            
            logger.info("Mock token refreshed")
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "user": {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "created_at": user_data["created_at"]
                }
            }
            
        except Exception as e:
            logger.error(f"Mock token refresh failed: {e}")
            raise Exception(f"Token refresh failed: {str(e)}")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID (mock implementation).
        
        Args:
            user_id: The user ID
            
        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        try:
            user_data = self.users.get(user_id)
            if user_data:
                # Return user data without password
                return {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "created_at": user_data["created_at"],
                    "updated_at": user_data["updated_at"]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting mock user {user_id}: {e}")
            return None

    async def create_session(self, user_id: Optional[str] = None, 
                           initial_config: Optional[Dict] = None) -> str:
        """
        Create a new interview session (mock implementation).
        
        Args:
            user_id: Optional user ID to associate with the session
            initial_config: Optional initial session configuration
            
        Returns:
            str: The created session ID
        """
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "session_config": initial_config or {},
                "conversation_history": [],
                "per_turn_feedback_log": [],
                "session_stats": {},
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.sessions[session_id] = session_data
            logger.info(f"Created mock session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating mock session: {e}")
            raise

    async def load_session_state(self, session_id: str) -> Optional[Dict]:
        """
        Load complete session state from mock storage.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            Optional[Dict]: Session data if found, None otherwise
        """
        try:
            session_data = self.sessions.get(session_id)
            if session_data:
                logger.debug(f"Loaded mock session state for: {session_id}")
            else:
                logger.warning(f"Mock session not found: {session_id}")
            return session_data
                
        except Exception as e:
            logger.error(f"Error loading mock session state for {session_id}: {e}")
            return None

    async def save_session_state(self, session_id: str, state_data: Dict) -> bool:
        """
        Save session state to mock storage.
        
        Args:
            session_id: The session ID to update
            state_data: The session data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if session_id in self.sessions:
                # Update existing session
                self.sessions[session_id].update(state_data)
                self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
                logger.debug(f"Saved mock session state for: {session_id}")
                return True
            else:
                logger.error(f"Mock session not found for save: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving mock session state for {session_id}: {e}")
            return False

    async def create_speech_task(self, session_id: str, task_type: str) -> str:
        """
        Create a new speech processing task (mock implementation).
        
        Args:
            session_id: The session ID this task belongs to
            task_type: Type of task ('stt_batch', 'tts', 'stt_stream')
            
        Returns:
            str: The created task ID
        """
        try:
            task_id = str(uuid.uuid4())
            task_data = {
                "task_id": task_id,
                "session_id": session_id,
                "task_type": task_type,
                "status": "processing",
                "progress_data": {},
                "result_data": None,
                "error_message": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.speech_tasks[task_id] = task_data
            logger.info(f"Created mock speech task: {task_id} for session: {session_id}")
            return task_id
                
        except Exception as e:
            logger.error(f"Error creating mock speech task: {e}")
            raise

    async def update_speech_task(self, task_id: str, status: str, 
                               progress_data: Optional[Dict] = None, 
                               result_data: Optional[Dict] = None,
                               error_message: Optional[str] = None) -> bool:
        """
        Update speech task progress and results (mock implementation).
        
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
            if task_id in self.speech_tasks:
                task_data = self.speech_tasks[task_id]
                task_data["status"] = status
                task_data["updated_at"] = datetime.utcnow().isoformat()
                
                if progress_data is not None:
                    task_data["progress_data"] = progress_data
                if result_data is not None:
                    task_data["result_data"] = result_data
                if error_message is not None:
                    task_data["error_message"] = error_message
                
                logger.debug(f"Updated mock speech task: {task_id}")
                return True
            else:
                logger.error(f"Mock speech task not found: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating mock speech task {task_id}: {e}")
            return False

    async def get_speech_task(self, task_id: str) -> Optional[Dict]:
        """
        Get speech task by ID (mock implementation).
        
        Args:
            task_id: The task ID to retrieve
            
        Returns:
            Optional[Dict]: Task data if found, None otherwise
        """
        try:
            return self.speech_tasks.get(task_id)
                
        except Exception as e:
            logger.error(f"Error getting mock speech task {task_id}: {e}")
            return None

    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Clean up completed speech tasks (mock implementation).
        
        Args:
            older_than_hours: Remove tasks completed more than this many hours ago
            
        Returns:
            int: Number of tasks cleaned up
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            tasks_to_remove = []
            for task_id, task_data in self.speech_tasks.items():
                if task_data["status"] in ["completed", "error"]:
                    updated_at = datetime.fromisoformat(task_data["updated_at"])
                    if updated_at < cutoff_time:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.speech_tasks[task_id]
            
            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} mock speech tasks")
            
            return len(tasks_to_remove)
            
        except Exception as e:
            logger.error(f"Error cleaning up mock tasks: {e}")
            return 0

    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get sessions for a specific user (mock implementation).
        
        Args:
            user_id: The user ID
            limit: Maximum number of sessions to return
            
        Returns:
            List[Dict]: List of session data
        """
        try:
            user_sessions = []
            for session_data in self.sessions.values():
                if session_data.get("user_id") == user_id:
                    user_sessions.append(session_data)
            
            # Sort by created_at descending and limit
            user_sessions.sort(key=lambda x: x["created_at"], reverse=True)
            return user_sessions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting mock user sessions for {user_id}: {e}")
            return [] 