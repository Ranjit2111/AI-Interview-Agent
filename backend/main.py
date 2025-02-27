import base64
import io
import os
from typing import Dict, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Interview Coach API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini AI
GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5flash')

class InterviewInput(BaseModel):
    """Pydantic model for interview input data."""
    question: str
    user_response: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "Tell me about yourself",
                "user_response": "I am a software engineer with 5 years of experience..."
            }
        }
    }

SYSTEM_PROMPT = """You are an expert AI Interview Coach. Analyze the candidate's response to the interview question and provide detailed feedback in the following JSON structure:
{
    "overall_score": 1-10,
    "strengths": ["point1", "point2"],
    "areas_for_improvement": ["point1", "point2"],
    "technical_analysis": "detailed analysis of technical aspects",
    "communication_analysis": "analysis of communication style",
    "suggested_improvement": "specific advice for improvement"
}"""

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint to check if API is running."""
    return {"message": "AI Interview Coach API is running"}

@app.post("/evaluate")
async def evaluate_response(data: InterviewInput) -> Dict[str, str]:
    """
    Evaluate interview response and provide feedback with audio.
    
    Args:
        data: InterviewInput object containing question and user_response
        
    Returns:
        Dict containing feedback text and audio in base64 format
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Prepare prompt for Gemini
        prompt = f"Question: {data.question}\nCandidate's Response: {data.user_response}\n\nProvide feedback following the structure specified."
        
        # Get response from Gemini
        response = model.generate_content([SYSTEM_PROMPT, prompt])
        feedback = response.text

        # Generate speech from feedback using gTTS
        speech_output = io.BytesIO()
        tts = gTTS(text=feedback, lang='en')
        tts.write_to_fp(speech_output)
        speech_output.seek(0)  # Reset buffer position to start
        audio_base64 = base64.b64encode(speech_output.getvalue()).decode()

        return {
            "feedback": feedback,
            "audio": audio_base64
        }

    except Exception as e:
        # Log the error (you might want to use proper logging)
        print(f"Error in evaluate_response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 