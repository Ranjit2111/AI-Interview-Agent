"""
Time management utility for agentic time-based interviews.
Provides time tracking, notifications, and decision support for interview agents.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TimePhase(Enum):
    """Interview time phases for agentic decision making."""
    OPENING = "opening"           # 0-20% of time
    EXPLORATION = "exploration"   # 20-60% of time  
    DEEPENING = "deepening"      # 60-80% of time
    CLOSING = "closing"          # 80-100% of time


@dataclass
class TimeContext:
    """Time context information for agent decision making."""
    total_duration_minutes: int
    elapsed_minutes: float
    remaining_minutes: float
    progress_percentage: float
    current_phase: TimePhase
    phase_progress: float  # Progress within current phase (0.0-1.0)
    time_pressure: str     # "low", "medium", "high"
    suggested_actions: List[str]


class InterviewTimeManager:
    """
    Agentic time management for interviews.
    Provides time awareness and decision support to interview agents.
    """
    
    def __init__(self, duration_minutes: int):
        """
        Initialize time manager.
        
        Args:
            duration_minutes: Total interview duration in minutes
        """
        self.duration_minutes = duration_minutes
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_active = False
        
        # Time phase boundaries (percentage of total time)
        self.phase_boundaries = {
            TimePhase.OPENING: (0.0, 0.2),
            TimePhase.EXPLORATION: (0.2, 0.6),
            TimePhase.DEEPENING: (0.6, 0.8),
            TimePhase.CLOSING: (0.8, 1.0)
        }
        
        # Event callbacks for time milestones
        self.callbacks: Dict[str, List[Callable[[TimeContext], None]]] = {
            "phase_change": [],
            "time_warning": [],
            "halfway_point": [],
            "final_warning": []
        }
        
        self._last_phase = None
        self._milestone_triggered = set()
        
        logger.info(f"InterviewTimeManager initialized for {duration_minutes} minutes")
    
    def start_interview(self) -> None:
        """Start the interview timer."""
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        self.is_active = True
        self._milestone_triggered.clear()
        
        logger.info(f"Interview timer started. Duration: {self.duration_minutes} minutes")
    
    def get_time_context(self) -> TimeContext:
        """
        Get current time context for agent decision making.
        
        Returns:
            TimeContext with current time information and suggestions
        """
        if not self.is_active or not self.start_time:
            return self._create_inactive_context()
        
        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds() / 60.0  # minutes
        remaining = max(0, self.duration_minutes - elapsed)
        progress = min(1.0, elapsed / self.duration_minutes)
        
        # Determine current phase
        current_phase = self._get_current_phase(progress)
        phase_start, phase_end = self.phase_boundaries[current_phase]
        phase_duration = phase_end - phase_start
        phase_progress = min(1.0, (progress - phase_start) / phase_duration) if phase_duration > 0 else 0.0
        
        # Determine time pressure
        time_pressure = self._calculate_time_pressure(progress, remaining)
        
        # Generate suggested actions
        suggested_actions = self._generate_time_based_suggestions(current_phase, progress, remaining)
        
        context = TimeContext(
            total_duration_minutes=self.duration_minutes,
            elapsed_minutes=elapsed,
            remaining_minutes=remaining,
            progress_percentage=progress * 100,
            current_phase=current_phase,
            phase_progress=phase_progress,
            time_pressure=time_pressure,
            suggested_actions=suggested_actions
        )
        
        # Check for phase changes and milestones
        self._check_milestones(context)
        
        return context
    
    def _create_inactive_context(self) -> TimeContext:
        """Create a context for inactive timer."""
        return TimeContext(
            total_duration_minutes=self.duration_minutes,
            elapsed_minutes=0.0,
            remaining_minutes=self.duration_minutes,
            progress_percentage=0.0,
            current_phase=TimePhase.OPENING,
            phase_progress=0.0,
            time_pressure="low",
            suggested_actions=["Start the interview"]
        )
    
    def _get_current_phase(self, progress: float) -> TimePhase:
        """Determine current phase based on progress."""
        for phase, (start, end) in self.phase_boundaries.items():
            if start <= progress < end:
                return phase
        return TimePhase.CLOSING  # If progress >= 1.0
    
    def _calculate_time_pressure(self, progress: float, remaining_minutes: float) -> str:
        """Calculate time pressure level."""
        if progress < 0.5:
            return "low"
        elif progress < 0.8:
            return "medium"
        else:
            return "high"
    
    def _generate_time_based_suggestions(self, phase: TimePhase, progress: float, remaining: float) -> List[str]:
        """Generate agentic suggestions based on current time context."""
        suggestions = []
        
        if phase == TimePhase.OPENING:
            suggestions.extend([
                "Focus on building rapport and understanding the candidate",
                "Ask broad questions to gauge overall experience",
                "Establish interview tone and candidate comfort level"
            ])
        elif phase == TimePhase.EXPLORATION:
            suggestions.extend([
                "Dive deeper into specific experiences and skills",
                "Explore technical competencies relevant to the role",
                "Ask behavioral questions using STAR method"
            ])
        elif phase == TimePhase.DEEPENING:
            suggestions.extend([
                "Focus on most critical competencies for the role",
                "Ask challenging scenario-based questions",
                "Evaluate problem-solving approaches in detail"
            ])
        elif phase == TimePhase.CLOSING:
            suggestions.extend([
                "Wrap up with final key questions",
                "Allow time for candidate questions",
                "Prepare for interview conclusion"
            ])
        
        # Add time-pressure specific suggestions
        if progress > 0.9:
            suggestions.append("Consider concluding the interview soon")
        elif progress > 0.8:
            suggestions.append("Begin transition to closing phase")
        elif remaining < 5:
            suggestions.append("Focus on essential questions only")
        
        return suggestions
    
    def _check_milestones(self, context: TimeContext) -> None:
        """Check and trigger milestone callbacks."""
        progress = context.progress_percentage / 100
        
        # Phase change detection
        if self._last_phase != context.current_phase:
            self._trigger_callbacks("phase_change", context)
            self._last_phase = context.current_phase
        
        # Milestone detection
        if progress >= 0.5 and "halfway" not in self._milestone_triggered:
            self._milestone_triggered.add("halfway")
            self._trigger_callbacks("halfway_point", context)
        
        if progress >= 0.8 and "final_warning" not in self._milestone_triggered:
            self._milestone_triggered.add("final_warning")
            self._trigger_callbacks("final_warning", context)
        
        if progress >= 0.9 and "time_warning" not in self._milestone_triggered:
            self._milestone_triggered.add("time_warning")
            self._trigger_callbacks("time_warning", context)
    
    def _trigger_callbacks(self, event_type: str, context: TimeContext) -> None:
        """Trigger registered callbacks for events."""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(context)
            except Exception as e:
                logger.error(f"Error in time manager callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable[[TimeContext], None]) -> None:
        """
        Register a callback for time events.
        
        Args:
            event_type: Type of event ("phase_change", "time_warning", "halfway_point", "final_warning")
            callback: Function to call when event occurs
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def stop_interview(self) -> TimeContext:
        """
        Stop the interview timer and return final context.
        
        Returns:
            Final time context
        """
        if self.is_active:
            final_context = self.get_time_context()
            self.is_active = False
            logger.info(f"Interview stopped. Duration: {final_context.elapsed_minutes:.1f} minutes")
            return final_context
        else:
            return self._create_inactive_context()
    
    def get_time_based_prompt_context(self) -> Dict[str, Any]:
        """
        Get time context formatted for LLM prompts.
        
        Returns:
            Dictionary with time information for prompt templates
        """
        context = self.get_time_context()
        
        return {
            "current_time_phase": context.current_phase.value,
            "time_progress_percentage": round(context.progress_percentage, 1),
            "remaining_minutes": round(context.remaining_minutes, 1),
            "time_pressure": context.time_pressure,
            "phase_progress": round(context.phase_progress * 100, 1),
            "time_based_suggestions": context.suggested_actions,
            "should_start_closing": context.progress_percentage > 80,
            "is_running_out_of_time": context.remaining_minutes < 5
        } 