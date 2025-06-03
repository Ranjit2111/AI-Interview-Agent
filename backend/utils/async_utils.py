"""
Async utilities for handling async operations safely across the application.
Provides thread-safe ways to run async code from sync contexts.
"""

import asyncio
import logging
from typing import Any, Coroutine, TypeVar, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')

class AsyncRunner:
    """
    Thread-safe async runner that handles event loop management properly.
    Prevents conflicts with existing event loops in FastAPI and other frameworks.
    """
    
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="async_runner")
        self._lock = threading.Lock()
    
    def run_async(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Run an async coroutine from sync context safely.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
            
        Raises:
            Exception: Any exception raised by the coroutine
        """
        try:
            # Try to get current loop
            current_loop = asyncio.get_running_loop()
            if current_loop.is_running():
                # We're in an async context, run in thread pool
                future = self._executor.submit(self._run_in_new_thread, coro)
                return future.result(timeout=30)  # 30 second timeout
            else:
                # Loop exists but not running, use it
                return current_loop.run_until_complete(coro)
                
        except RuntimeError:
            # No event loop exists, create one
            with self._lock:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
    
    def _run_in_new_thread(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run coroutine in a new thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def shutdown(self):
        """Shutdown the async runner and cleanup resources."""
        self._executor.shutdown(wait=True)


# Global async runner instance
_async_runner: Optional[AsyncRunner] = None


def get_async_runner() -> AsyncRunner:
    """Get the global async runner instance."""
    global _async_runner
    if _async_runner is None:
        _async_runner = AsyncRunner()
    return _async_runner


def run_async_safe(coro: Coroutine[Any, Any, T]) -> T:
    """
    Convenience function to run async code safely from sync context.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    runner = get_async_runner()
    return runner.run_async(coro) 