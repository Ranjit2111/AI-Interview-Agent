"""
Email API for handling feedback form submissions using Resend.
"""

import os
import logging
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
import resend

logger = logging.getLogger(__name__)

class FeedbackRequest(BaseModel):
    """Schema for feedback form submissions."""
    name: str = Field(..., min_length=1, max_length=100, description="Sender's name")
    email: EmailStr = Field(..., description="Sender's email address")
    message: str = Field(..., min_length=10, max_length=2000, description="Feedback message")

def create_email_api(app: FastAPI):
    """Create and register email API routes."""
    
    @app.post("/api/send-feedback")
    async def send_feedback(feedback: FeedbackRequest):
        """Send feedback email using Resend."""
        try:
            # Get Resend API key from environment
            resend_api_key = os.getenv("RESEND_API_KEY")
            if not resend_api_key:
                logger.error("RESEND_API_KEY not found in environment variables")
                raise HTTPException(
                    status_code=500,
                    detail="Email service not configured. Please contact support."
                )
            
            # Initialize Resend
            resend.api_key = resend_api_key
            
            # Prepare email content
            recipient_email = "ranjitnagaraj2131@gmail.com"
            subject = f"AI Interviewer Feedback from {feedback.name}"
            
            # Create HTML email content
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0; color: white;">
                        <h1 style="margin: 0; font-size: 24px;">🎯 AI Interviewer Feedback</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">New feedback received from a user</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                            <h3 style="color: #495057; margin-top: 0;">User Information</h3>
                            <p><strong>Name:</strong> {feedback.name}</p>
                            <p><strong>Email:</strong> {feedback.email}</p>
                            <p><strong>Submitted:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        </div>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px;">
                            <h3 style="color: #495057; margin-top: 0;">Feedback Message</h3>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                                <p style="margin: 0; line-height: 1.6; white-space: pre-wrap;">{feedback.message}</p>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #e8f4ff; border-radius: 8px; border: 1px solid #b3d9ff;">
                            <p style="margin: 0; font-size: 14px; color: #0066cc;">
                                <strong>💡 Quick Response:</strong> You can reply directly to this email to respond to {feedback.name} at {feedback.email}
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Create plain text version for email clients that don't support HTML
            text_content = f"""
AI Interviewer Feedback

User Information:
Name: {feedback.name}
Email: {feedback.email}
Submitted: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Feedback Message:
{feedback.message}

You can reply directly to this email to respond to the user.
            """
            
            # Send email using Resend
            email_response = resend.Emails.send({
                "from": "AI Interviewer <noreply@resend.dev>",
                "to": [recipient_email],
                "reply_to": feedback.email,  # Allow direct reply to user
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "tags": [
                    {"name": "category", "value": "feedback"},
                    {"name": "source", "value": "ai-interviewer"}
                ]
            })
            
            logger.info(f"Feedback email sent successfully. Email ID: {email_response.get('id', 'unknown')}")
            
            return {
                "success": True,
                "message": "Thank you for your feedback! We'll review it and get back to you soon.",
                "email_id": email_response.get("id")
            }
            
        except Exception as e:
            logger.error(f"Failed to send feedback email: {str(e)}", exc_info=True)
            
            # Return user-friendly error message
            if "API key" in str(e).lower():
                error_message = "Email service configuration error. Please contact support."
            elif "rate limit" in str(e).lower():
                error_message = "Too many emails sent recently. Please try again in a few minutes."
            else:
                error_message = "Failed to send feedback. Please try again later or contact support directly."
            
            raise HTTPException(
                status_code=500,
                detail=error_message
            )
    
    logger.info("Email API routes registered") 