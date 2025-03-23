"""
API for resource tracking and feedback.
Provides endpoints for tracking resource usage and collecting user feedback.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.interview import ResourceTracking, ResourceFeedback
from backend.services import get_data_service, get_search_service


class ResourceAction(BaseModel):
    """Model for tracking resource actions."""
    session_id: str = Field(..., description="Session identifier")
    resource_id: str = Field(..., description="Resource identifier or URL")
    action: str = Field(..., description="Action taken (click, bookmark, etc.)")
    skill_name: str = Field(..., description="Skill name the resource is for")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ResourceFeedbackModel(BaseModel):
    """Model for resource feedback."""
    session_id: str = Field(..., description="Session identifier")
    resource_id: str = Field(..., description="Resource identifier or URL")
    feedback: str = Field(..., description="Feedback (helpful, not_helpful)")
    skill_name: str = Field(..., description="Skill name the resource is for")
    comments: Optional[str] = Field(None, description="User comments about the resource")


def create_resource_api(router: APIRouter):
    """
    Create API endpoints for resource tracking and feedback.
    
    Args:
        router: APIRouter instance
    """
    data_service = get_data_service()
    search_service = get_search_service()
    logger = logging.getLogger(__name__)
    
    @router.post("/api/interview/resource-tracking", response_model=Dict[str, Any])
    async def track_resource_action(
        action: ResourceAction,
        db: Session = Depends(get_db)
    ):
        """
        Track resource usage actions.
        
        Args:
            action: Resource action details
            db: Database session
            
        Returns:
            Success message
        """
        try:
            # Create tracking record
            tracking = ResourceTracking(
                session_id=action.session_id,
                resource_id=action.resource_id,
                action=action.action,
                skill_name=action.skill_name,
                timestamp=datetime.utcnow(),
                metadata=action.metadata
            )
            
            # Add to database
            db.add(tracking)
            db.commit()
            
            # Log the action (for analytics purposes)
            logger.info(f"Resource action tracked: {action.action} for {action.resource_id}")
            
            return {
                "success": True,
                "message": "Resource action tracked successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error tracking resource action: {str(e)}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error tracking resource action: {str(e)}"
            )
    
    @router.post("/api/interview/resource-feedback", response_model=Dict[str, Any])
    async def record_resource_feedback(
        feedback: ResourceFeedbackModel,
        db: Session = Depends(get_db)
    ):
        """
        Record feedback on a resource.
        
        Args:
            feedback: Resource feedback details
            db: Database session
            
        Returns:
            Success message
        """
        try:
            # Create feedback record
            feedback_record = ResourceFeedback(
                session_id=feedback.session_id,
                resource_id=feedback.resource_id,
                feedback=feedback.feedback,
                skill_name=feedback.skill_name,
                comments=feedback.comments,
                timestamp=datetime.utcnow()
            )
            
            # Add to database
            db.add(feedback_record)
            db.commit()
            
            # Log the feedback
            logger.info(
                f"Resource feedback recorded: {feedback.feedback} for {feedback.resource_id}"
            )
            
            # Update search service resource quality scoring (for future searches)
            if feedback.feedback == "helpful":
                # This would be implemented in a real system to improve future search results
                # search_service.update_resource_quality(feedback.resource_id, is_helpful=True)
                pass
            
            return {
                "success": True,
                "message": "Resource feedback recorded successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error recording resource feedback: {str(e)}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error recording resource feedback: {str(e)}"
            )
    
    @router.get("/api/interview/resource-effectiveness", response_model=Dict[str, Any])
    async def get_resource_effectiveness(
        session_id: str,
        skill_name: Optional[str] = None,
        db: Session = Depends(get_db)
    ):
        """
        Get resource effectiveness metrics.
        
        Args:
            session_id: Session identifier
            skill_name: Optional skill name to filter by
            db: Database session
            
        Returns:
            Resource effectiveness metrics
        """
        try:
            # Query tracking data
            tracking_query = db.query(ResourceTracking).filter(
                ResourceTracking.session_id == session_id
            )
            
            # Apply skill filter if provided
            if skill_name:
                tracking_query = tracking_query.filter(
                    ResourceTracking.skill_name == skill_name
                )
            
            # Get tracking records
            tracking_records = tracking_query.all()
            
            # Query feedback data
            feedback_query = db.query(ResourceFeedback).filter(
                ResourceFeedback.session_id == session_id
            )
            
            # Apply skill filter if provided
            if skill_name:
                feedback_query = feedback_query.filter(
                    ResourceFeedback.skill_name == skill_name
                )
            
            # Get feedback records
            feedback_records = feedback_query.all()
            
            # Calculate effectiveness metrics
            total_clicks = len([r for r in tracking_records if r.action == "click"])
            helpful_count = len([r for r in feedback_records if r.feedback == "helpful"])
            not_helpful_count = len([r for r in feedback_records if r.feedback == "not_helpful"])
            
            # Calculate effectiveness percentage
            effectiveness = 0
            if helpful_count + not_helpful_count > 0:
                effectiveness = (helpful_count / (helpful_count + not_helpful_count)) * 100
            
            # Organize by resource type
            resource_types = {}
            for record in tracking_records:
                # Extract resource type from metadata
                resource_type = record.metadata.get("resource_type", "unknown") if record.metadata else "unknown"
                
                if resource_type not in resource_types:
                    resource_types[resource_type] = {
                        "clicks": 0,
                        "helpful": 0,
                        "not_helpful": 0
                    }
                
                if record.action == "click":
                    resource_types[resource_type]["clicks"] += 1
            
            # Add feedback data to resource types
            for record in feedback_records:
                # Find the resource in tracking records to get the type
                matching_records = [r for r in tracking_records if r.resource_id == record.resource_id]
                if matching_records:
                    resource_type = matching_records[0].metadata.get("resource_type", "unknown") if matching_records[0].metadata else "unknown"
                    
                    if resource_type not in resource_types:
                        resource_types[resource_type] = {
                            "clicks": 0,
                            "helpful": 0,
                            "not_helpful": 0
                        }
                    
                    if record.feedback == "helpful":
                        resource_types[resource_type]["helpful"] += 1
                    else:
                        resource_types[resource_type]["not_helpful"] += 1
            
            return {
                "total_clicks": total_clicks,
                "helpful_count": helpful_count,
                "not_helpful_count": not_helpful_count,
                "effectiveness_percentage": effectiveness,
                "resource_types": resource_types,
                "skill_name": skill_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting resource effectiveness: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error getting resource effectiveness: {str(e)}"
            )
    
    return router 