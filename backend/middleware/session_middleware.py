"""
Session saving middleware for automatic session persistence.
Ensures session data is saved after API operations that modify session state.
"""

import logging
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import get_logger

logger = get_logger(__name__)


class SessionSavingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically saves session state after API operations.
    This provides a safety net to ensure session data is persisted even if
    explicit save calls are missed in individual endpoints.
    """
    
    # API paths that modify session state and require saving
    SESSION_MODIFYING_PATHS = {
        "/interview/start",
        "/interview/message", 
        "/interview/reset"
    }
    
    def __init__(self, app, session_registry_getter: Optional[Callable] = None):
        """
        Initialize the middleware.
        
        Args:
            app: FastAPI application instance
            session_registry_getter: Optional function to get session registry
        """
        super().__init__(app)
        self.session_registry_getter = session_registry_getter

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and automatically save session if needed.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            HTTP response
        """
        # Process the request
        response = await call_next(request)
        
        # Check if this is a session-modifying endpoint
        if (request.method == "POST" and 
            request.url.path in self.SESSION_MODIFYING_PATHS):
            
            # Try to save session if we have session ID
            session_id = self._extract_session_id(request)
            if session_id:
                await self._save_session_safe(session_id, request.url.path)
        
        return response
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """
        Extract session ID from request headers.
        
        Args:
            request: HTTP request
            
        Returns:
            Session ID if found, None otherwise
        """
        return request.headers.get("X-Session-ID")
    
    async def _save_session_safe(self, session_id: str, endpoint_path: str) -> None:
        """
        Safely save session with error handling.
        
        Args:
            session_id: Session ID to save
            endpoint_path: API endpoint that triggered the save
        """
        try:
            # Get session registry from app state if available
            if hasattr(self.app, 'state') and hasattr(self.app.state, 'agent_manager'):
                session_registry = self.app.state.agent_manager
                
                # Check if session is active in memory
                if session_id in session_registry._active_sessions:
                    save_success = await session_registry.save_session(session_id)
                    if save_success:
                        logger.debug(f"Middleware auto-saved session {session_id} after {endpoint_path}")
                    else:
                        logger.warning(f"Middleware failed to save session {session_id} after {endpoint_path}")
                else:
                    logger.debug(f"Session {session_id} not active in memory, skipping middleware save")
            else:
                logger.debug("Session registry not available in app state, skipping middleware save")
                
        except Exception as e:
            # Don't fail the request due to save errors, just log them
            logger.error(f"Middleware session save error for {session_id} after {endpoint_path}: {e}")