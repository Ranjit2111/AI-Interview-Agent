"""
Text-to-Speech service using Amazon Polly with rate limiting and retry logic.
"""

import asyncio
import html
import logging
import os
from typing import Optional, Dict
import random
import hashlib

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from botocore.config import Config
from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

from backend.services.rate_limiting import get_rate_limiter

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using Amazon Polly with concurrency control and caching."""
    
    def __init__(self):
        self.polly_client = None
        self.rate_limiter = get_rate_limiter()
        # Simple in-memory cache for frequently used phrases
        self.audio_cache: Dict[str, bytes] = {}
        self.cache_max_size = 50  # Limit cache size
        
        # Load TTS configuration from environment variables
        self.polly_engine = os.environ.get("POLLY_ENGINE", "long-form")
        self.default_voice = os.environ.get("POLLY_DEFAULT_VOICE", "Patrick")
        
        self._initialize_polly()
    
    def _initialize_polly(self):
        """Initialize Amazon Polly client with retry configuration."""
        aws_region = os.environ.get("AWS_REGION")
        
        if not aws_region:
            logger.warning("AWS_REGION environment variable not set. AWS Polly TTS service will be unavailable.")
            return
        
        try:
            # Enhanced boto3 client configuration for Azure deployment
            polly_config = Config(
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                max_pool_connections=50,  # Increased for better connection reuse
                region_name=aws_region,
                # Azure-optimized timeout settings
                connect_timeout=30,  # Connection timeout
                read_timeout=60,     # Read timeout for large audio files
                # Enable TCP keepalive for persistent connections
                tcp_keepalive=True
            )
            
            self.polly_client = boto3.client(
                "polly",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                config=polly_config
            )
            logger.info(f"Successfully initialized AWS Polly client in region {aws_region} with Azure-optimized configuration.")
            logger.info(f"TTS Configuration - Engine: {self.polly_engine}, Default Voice: {self.default_voice}")
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
    
    async def _synthesize_speech_with_retry(self, ssml_text: str, voice_id: str, max_retries: int = 3) -> bytes:
        """
        Synthesize speech using Amazon Polly with exponential backoff retry logic.
        
        Args:
            ssml_text: SSML formatted text to synthesize
            voice_id: Voice ID for synthesis
            max_retries: Maximum number of retry attempts
            
        Returns:
            bytes: Audio data
        """
        if not self.polly_client:
            raise HTTPException(
                status_code=503,
                detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
            )
        
        # Acquire rate limiting slot
        if not await self.rate_limiter.acquire_polly():
            raise HTTPException(
                status_code=429,
                detail="TTS service temporarily unavailable due to rate limiting. Please try again later."
            )
        
        try:
            for attempt in range(max_retries):
                try:
                    response = await asyncio.to_thread(
                        self.polly_client.synthesize_speech,
                        Text=ssml_text,
                        OutputFormat="mp3",
                        VoiceId=voice_id,
                        TextType="ssml",
                        Engine=self.polly_engine
                    )
                    
                    audio_stream = response.get("AudioStream")
                    if not audio_stream:
                        raise HTTPException(status_code=500, detail="TTS server returned no audio data.")
                    
                    try:
                        audio_content = audio_stream.read()
                        return audio_content
                    finally:
                        audio_stream.close()
                        
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    error_message = e.response.get('Error', {}).get('Message', str(e))
                    
                    # Check if it's a retryable error
                    if error_code in ['ThrottlingException', 'ServiceUnavailable', 'InternalServerError']:
                        if attempt < max_retries - 1:
                            # Exponential backoff with jitter
                            delay = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(f"Polly API error (attempt {attempt + 1}/{max_retries}): {error_code}. Retrying in {delay:.2f}s")
                            await asyncio.sleep(delay)
                            continue
                    
                    logger.error(f"Amazon Polly service error during synthesis: {error_code} - {error_message}")
                    raise HTTPException(
                        status_code=int(error_code) if error_code.isdigit() else 503,
                        detail=f"Amazon Polly service error: {error_message}"
                    )
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"TTS synthesis error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.exception("Unexpected error during text-to-speech synthesis with Polly")
                        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
            
            raise HTTPException(status_code=500, detail="TTS synthesis failed after all retry attempts")
            
        finally:
            # Always release the rate limiting slot
            self.rate_limiter.release_polly()
    
    def _get_cache_key(self, text: str, voice_id: str, speed: float) -> str:
        """Generate cache key for TTS request."""
        content = f"{text}|{voice_id}|{speed}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _should_cache(self, text: str) -> bool:
        """Determine if text should be cached (short, common phrases)."""
        # Cache short phrases that are likely to be repeated
        return len(text) < 100 and any(phrase in text.lower() for phrase in [
            'hello', 'welcome', 'thank you', 'please', 'ready', 'starting', 
            'let me', 'can you', 'tell me', 'great', 'excellent', 'good'
        ])
    
    async def _get_cached_or_synthesize(self, ssml_text: str, voice_id: str, speed: float, text: str) -> bytes:
        """Get audio from cache or synthesize new."""
        # Check cache first for cacheable content
        if self._should_cache(text):
            cache_key = self._get_cache_key(text, voice_id, speed)
            
            if cache_key in self.audio_cache:
                logger.debug(f"TTS cache hit for: {text[:30]}...")
                return self.audio_cache[cache_key]
        
        # Synthesize new audio
        audio_content = await self._synthesize_speech_with_retry(ssml_text, voice_id)
        
        # Cache if appropriate
        if self._should_cache(text) and len(self.audio_cache) < self.cache_max_size:
            cache_key = self._get_cache_key(text, voice_id, speed)
            self.audio_cache[cache_key] = audio_content
            logger.debug(f"TTS cached: {text[:30]}...")
        
        return audio_content
    
    async def synthesize_text(self, text: str, voice_id: Optional[str] = None, speed: float = 1.0) -> Response:
        """
        Synthesize speech from text with rate limiting.
        
        Args:
            text: Text to synthesize.
            voice_id: IGNORED - Voice is controlled by environment variables only.
            speed: Speech speed (0.5 to 2.0).
            
        Returns:
            Audio data as an MP3 file response.
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
            )

        # Check if API is available before proceeding
        if not self.rate_limiter.is_api_available('polly'):
            raise HTTPException(
                status_code=429,
                detail="TTS service temporarily unavailable due to high demand. Please try again later."
            )

        # Always use environment variable voice - ignore any frontend input
        voice_id = self.default_voice

        ssml_text = self._prepare_ssml(text, speed)
        logger.debug(f"TTS request: voice={voice_id}, speed={speed}, engine={self.polly_engine}")

        try:
            audio_content = await self._get_cached_or_synthesize(ssml_text, voice_id, speed, text)
            return Response(content=audio_content, media_type="audio/mpeg")

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.exception("Unexpected error during text-to-speech synthesis")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def stream_text(self, text: str, voice_id: Optional[str] = None, speed: float = 1.0) -> StreamingResponse:
        """
        Synthesize speech from text and stream the audio with rate limiting.
        
        Args:
            text: Text to synthesize.
            voice_id: IGNORED - Voice is controlled by environment variables only.
            speed: Speech speed (0.5 to 2.0).
            
        Returns:
            StreamingResponse containing MP3 audio data.
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
            )

        # Check if API is available before proceeding
        if not self.rate_limiter.is_api_available('polly'):
            raise HTTPException(
                status_code=429,
                detail="TTS service temporarily unavailable due to high demand. Please try again later."
            )

        # Always use environment variable voice - ignore any frontend input
        voice_id = self.default_voice

        ssml_text = self._prepare_ssml(text, speed)
        logger.debug(f"Streaming TTS request: voice={voice_id}, speed={speed}, engine={self.polly_engine}")
        
        # Acquire rate limiting slot
        if not await self.rate_limiter.acquire_polly():
            raise HTTPException(
                status_code=429,
                detail="TTS service temporarily unavailable due to rate limiting. Please try again later."
            )
        
        try:
            # boto3's synthesize_speech is blocking, so run in thread for async handler
            response = await asyncio.to_thread(
                self.polly_client.synthesize_speech,
                Text=ssml_text,
                OutputFormat="mp3",
                VoiceId=voice_id,
                TextType="ssml",
                Engine=self.polly_engine
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
            error_code = e.response.get('Error', {}).get('Code', 500)
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Amazon Polly service error during streaming synthesis: {error_code} - {error_message}")
            raise HTTPException(
                status_code=int(error_code) if isinstance(error_code, str) and error_code.isdigit() else 503,
                detail=f"Amazon Polly service error: {error_message}"
            )
        except Exception as e:
            logger.exception("Unexpected error during streaming text-to-speech synthesis with Polly")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        finally:
            # Always release the rate limiting slot
            self.rate_limiter.release_polly() 