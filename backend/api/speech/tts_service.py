"""
Text-to-Speech service using Amazon Polly.
"""

import asyncio
import html
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using Amazon Polly."""
    
    def __init__(self):
        self.polly_client = None
        self._initialize_polly()
    
    def _initialize_polly(self):
        """Initialize Amazon Polly client."""
        aws_region = os.environ.get("AWS_REGION")
        
        if not aws_region:
            logger.warning("AWS_REGION environment variable not set. AWS Polly TTS service will be unavailable.")
            return
        
        try:
            self.polly_client = boto3.client(
                "polly",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=aws_region
            )
            logger.info(f"Successfully initialized AWS Polly client in region {aws_region}.")
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials not found or incomplete. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. Error: {e}")
        except ClientError as e:
            logger.error(f"AWS ClientError initializing Polly client: {e}. Check AWS permissions and region.")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Polly client: {e}")
    
    def is_available(self) -> bool:
        """Check if TTS service is available."""
        return self.polly_client is not None
    
    def _prepare_ssml(self, text: str, speed: float) -> str:
        """Prepare SSML text for TTS synthesis."""
        escaped_text = html.escape(text)
        speed_percentage = int(speed * 100)
        
        # Add a brief initial pause using <break> tag to prevent the first words from being cut off
        return f'<speak><break time="250ms"/><prosody rate="{speed_percentage}%">{escaped_text}</prosody></speak>'
    
    async def _synthesize_speech(self, ssml_text: str, voice_id: str) -> bytes:
        """Synthesize speech using Amazon Polly."""
        if not self.polly_client:
            raise HTTPException(
                status_code=503,
                detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
            )
        
        response = await asyncio.to_thread(
            self.polly_client.synthesize_speech,
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            TextType="ssml",
            Engine="generative"
        )
        
        audio_stream = response.get("AudioStream")
        if not audio_stream:
            raise HTTPException(status_code=500, detail="TTS server returned no audio data.")
        
        try:
            audio_content = audio_stream.read()
            return audio_content
        finally:
            audio_stream.close()
    
    async def synthesize_text(self, text: str, voice_id: str = "Matthew", speed: float = 1.0) -> Response:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize.
            voice_id: ID (name) of the Polly voice to use.
            speed: Speech speed (0.5 to 2.0).
            
        Returns:
            Audio data as an MP3 file response.
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
            )

        ssml_text = self._prepare_ssml(text, speed)
        logger.debug(f"TTS request: voice={voice_id}, speed={speed}")

        try:
            audio_content = await self._synthesize_speech(ssml_text, voice_id)
            return Response(content=audio_content, media_type="audio/mpeg")

        except ClientError as e:
            error_code = getattr(e.response, 'get', lambda x, y: y)('Error', {}).get('Code', 500)
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Amazon Polly service error during synthesis: {error_code} - {error_message}")
            raise HTTPException(
                status_code=int(error_code) if isinstance(error_code, str) and error_code.isdigit() else 503,
                detail=f"Amazon Polly service error: {error_message}"
            )
        except Exception as e:
            logger.exception("Unexpected error during text-to-speech synthesis with Polly")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def stream_text(self, text: str, voice_id: str = "Matthew", speed: float = 1.0) -> StreamingResponse:
        """
        Synthesize speech from text and stream the audio.
        
        Args:
            text: Text to synthesize.
            voice_id: ID (name) of the voice to use.
            speed: Speech speed (0.5 to 2.0).
            
        Returns:
            StreamingResponse containing MP3 audio data.
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
            )

        ssml_text = self._prepare_ssml(text, speed)
        logger.debug(f"Streaming TTS request: voice={voice_id}, speed={speed}")
        
        try:
            # boto3's synthesize_speech is blocking, so run in thread for async handler
            # However, its AudioStream is iterable, suitable for StreamingResponse
            response = await asyncio.to_thread(
                self.polly_client.synthesize_speech,
                Text=ssml_text,
                OutputFormat="mp3",
                VoiceId=voice_id,
                TextType="ssml",
                Engine="generative"
            )

            audio_stream = response.get("AudioStream")

            if not audio_stream:
                logger.error(f"No AudioStream in Polly streaming response: {response}")
                raise HTTPException(status_code=500, detail="TTS server returned no audio data for streaming.")

            async def generator(stream):
                try:
                    for chunk in stream:
                        yield chunk
                finally:
                    stream.close()

            return StreamingResponse(generator(audio_stream), media_type="audio/mpeg")

        except ClientError as e:
            error_code = getattr(e.response, 'get', lambda x, y: y)('Error', {}).get('Code', 500)
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Amazon Polly service error during streaming synthesis: {error_code} - {error_message}")
            raise HTTPException(
                status_code=int(error_code) if isinstance(error_code, str) and error_code.isdigit() else 503,
                detail=f"Amazon Polly service error: {error_message}"
            )
        except Exception as e:
            logger.exception("Unexpected error during streaming text-to-speech synthesis with Polly")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 