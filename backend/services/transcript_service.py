"""
Transcript management service for interview transcripts.
Handles creating, retrieving, updating, and deleting transcripts,
as well as generating embeddings for RAG.
"""

import json
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func

from backend.models.interview import InterviewSession, Message
from backend.models.transcript import Transcript, TranscriptTag, TranscriptEmbedding, TranscriptFragment, TranscriptFormat
from backend.utils.event_bus import Event, EventBus
from backend.utils.vector_store import VectorStore

# Define a cache TTL (time to live) in seconds
CACHE_TTL = 300  # 5 minute cache expiration

class TranscriptService:
    """
    Service for managing interview transcripts and their embeddings.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
        vector_store: Optional[VectorStore] = None,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        vector_store_dir: str = "./data/vector_store"
    ):
        """
        Initialize the transcript service.
        
        Args:
            event_bus: Event bus for subscribing to session events
            logger: Logger instance
            vector_store: Vector store for embeddings
            embedding_model_name: Name of the embedding model to use
            vector_store_dir: Directory for storing vector embeddings
        """
        self.event_bus = event_bus or EventBus()
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize vector store if not provided
        if vector_store is None:
            self.logger.info(f"Initializing vector store with model {embedding_model_name}")
            self.vector_store = VectorStore(
                embedding_model_name=embedding_model_name,
                index_dir=vector_store_dir
            )
        else:
            self.vector_store = vector_store
        
        # Initialize caches
        self._transcript_cache = {}
        self._transcript_cache_timestamps = {}
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe("interview_end", self._handle_interview_end)
            
    def create_transcript(
        self, 
        db: Session, 
        title: str, 
        content: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_imported: bool = False,
        is_public: bool = False,
        generate_embeddings: bool = True
    ) -> Optional[Transcript]:
        """
        Create a new transcript in the database.
        
        Args:
            db: Database session
            title: Transcript title
            content: Transcript content as list of message dictionaries
            session_id: Optional interview session ID
            user_id: Optional user ID
            summary: Optional transcript summary
            metadata: Optional metadata dictionary
            tags: Optional list of tag names
            is_imported: Whether this transcript was imported
            is_public: Whether this transcript is publicly accessible
            generate_embeddings: Whether to generate embeddings for this transcript
            
        Returns:
            Created transcript or None if there was an error
        """
        try:
            # Create transcript
            transcript = Transcript(
                title=title,
                interview_session_id=session_id,
                user_id=user_id,
                content=content,
                summary=summary,
                metadata=metadata or {},
                is_imported=is_imported,
                is_public=is_public,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add tags if provided
            if tags:
                for tag_name in tags:
                    # Find or create tag
                    tag = db.query(TranscriptTag).filter(TranscriptTag.name == tag_name).first()
                    if not tag:
                        tag = TranscriptTag(name=tag_name)
                        db.add(tag)
                    transcript.tags.append(tag)
            
            # Add to database
            db.add(transcript)
            db.flush()  # Get ID without committing
            
            # Generate embeddings if requested
            if generate_embeddings:
                self._generate_transcript_embeddings(db, transcript)
            
            # Commit changes
            db.commit()
            self.logger.info(f"Created transcript {transcript.id}: {title}")
            
            # Publish event
            self.event_bus.publish(Event(
                event_type="transcript_created",
                source="transcript_service",
                data={"transcript_id": transcript.id}
            ))
            
            return transcript
            
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error creating transcript: {str(e)}")
            return None
    
    def get_transcript(self, db: Session, transcript_id: int) -> Optional[Transcript]:
        """
        Get a transcript by ID.
        
        Args:
            db: Database session
            transcript_id: Transcript ID
            
        Returns:
            Transcript or None if not found
        """
        # Check cache first
        cache_key = f"transcript_{transcript_id}"
        now = datetime.utcnow()
        
        if (cache_key in self._transcript_cache and 
            cache_key in self._transcript_cache_timestamps and
            (now - self._transcript_cache_timestamps[cache_key]).total_seconds() < CACHE_TTL):
            return self._transcript_cache[cache_key]
        
        # Cache miss - query database
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        
        # Update cache
        if transcript:
            self._transcript_cache[cache_key] = transcript
            self._transcript_cache_timestamps[cache_key] = now
        
        return transcript
    
    def get_transcripts(
        self, 
        db: Session, 
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        is_imported: Optional[bool] = None,
        is_public: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transcript]:
        """
        Get transcripts with optional filtering.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by
            session_id: Optional session ID to filter by
            tag_names: Optional list of tag names to filter by
            is_imported: Optional filter for imported transcripts
            is_public: Optional filter for public transcripts
            limit: Maximum number of transcripts to return
            offset: Offset for pagination
            
        Returns:
            List of transcripts
        """
        query = db.query(Transcript)
        
        # Apply filters
        if user_id:
            query = query.filter(Transcript.user_id == user_id)
        if session_id:
            query = query.filter(Transcript.interview_session_id == session_id)
        if is_imported is not None:
            query = query.filter(Transcript.is_imported == is_imported)
        if is_public is not None:
            query = query.filter(Transcript.is_public == is_public)
            
        # Filter by tags if provided
        if tag_names:
            query = query.join(Transcript.tags).filter(
                TranscriptTag.name.in_(tag_names)
            ).group_by(Transcript.id).having(
                func.count(TranscriptTag.id) == len(tag_names)
            )
        
        # Apply pagination
        query = query.order_by(Transcript.created_at.desc()).limit(limit).offset(offset)
        
        return query.all()
    
    def update_transcript(
        self, 
        db: Session, 
        transcript_id: int,
        title: Optional[str] = None,
        content: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        regenerate_embeddings: bool = False
    ) -> Optional[Transcript]:
        """
        Update a transcript.
        
        Args:
            db: Database session
            transcript_id: Transcript ID
            title: Optional new title
            content: Optional new content
            summary: Optional new summary
            metadata: Optional new metadata
            tags: Optional new tags
            is_public: Optional new public status
            regenerate_embeddings: Whether to regenerate embeddings
            
        Returns:
            Updated transcript or None if not found
        """
        try:
            transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
            if not transcript:
                return None
            
            # Update fields if provided
            if title is not None:
                transcript.title = title
            if content is not None:
                transcript.content = content
            if summary is not None:
                transcript.summary = summary
            if metadata is not None:
                transcript.metadata = metadata
            if is_public is not None:
                transcript.is_public = is_public
                
            # Update timestamps
            transcript.updated_at = datetime.utcnow()
            
            # Update tags if provided
            if tags is not None:
                # Remove existing tags
                transcript.tags = []
                
                # Add new tags
                for tag_name in tags:
                    tag = db.query(TranscriptTag).filter(TranscriptTag.name == tag_name).first()
                    if not tag:
                        tag = TranscriptTag(name=tag_name)
                        db.add(tag)
                    transcript.tags.append(tag)
            
            # Regenerate embeddings if requested and content changed
            if regenerate_embeddings or content is not None:
                # Remove existing embeddings and fragments
                db.query(TranscriptEmbedding).filter(
                    TranscriptEmbedding.transcript_id == transcript.id
                ).delete()
                db.query(TranscriptFragment).filter(
                    TranscriptFragment.transcript_id == transcript.id
                ).delete()
                
                # Generate new embeddings
                self._generate_transcript_embeddings(db, transcript)
            
            # Commit changes
            db.commit()
            
            # Update cache
            cache_key = f"transcript_{transcript_id}"
            self._transcript_cache[cache_key] = transcript
            self._transcript_cache_timestamps[cache_key] = datetime.utcnow()
            
            # Publish event
            self.event_bus.publish(Event(
                event_type="transcript_updated",
                source="transcript_service",
                data={"transcript_id": transcript.id}
            ))
            
            return transcript
            
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error updating transcript {transcript_id}: {str(e)}")
            return None
    
    def delete_transcript(self, db: Session, transcript_id: int) -> bool:
        """
        Delete a transcript.
        
        Args:
            db: Database session
            transcript_id: Transcript ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
            if not transcript:
                return False
            
            # Delete transcript
            db.delete(transcript)
            db.commit()
            
            # Remove from cache
            cache_key = f"transcript_{transcript_id}"
            if cache_key in self._transcript_cache:
                del self._transcript_cache[cache_key]
            if cache_key in self._transcript_cache_timestamps:
                del self._transcript_cache_timestamps[cache_key]
            
            # Publish event
            self.event_bus.publish(Event(
                event_type="transcript_deleted",
                source="transcript_service",
                data={"transcript_id": transcript_id}
            ))
            
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error deleting transcript {transcript_id}: {str(e)}")
            return False
    
    def create_transcript_from_session(
        self, 
        db: Session, 
        session_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False,
        generate_embeddings: bool = True
    ) -> Optional[Transcript]:
        """
        Create a transcript from an interview session.
        
        Args:
            db: Database session
            session_id: Interview session ID
            title: Optional transcript title
            summary: Optional transcript summary
            tags: Optional list of tag names
            is_public: Whether this transcript is publicly accessible
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            Created transcript or None if there was an error
        """
        try:
            # Get session
            session = db.query(InterviewSession).filter(
                InterviewSession.session_id == session_id
            ).first()
            
            if not session:
                self.logger.warning(f"Session {session_id} not found")
                return None
            
            # Get messages
            messages = db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.timestamp).all()
            
            if not messages:
                self.logger.warning(f"No messages found for session {session_id}")
                return None
            
            # Convert messages to content format
            content = [message.to_dict() for message in messages]
            
            # Generate title if not provided
            if not title:
                title = f"Interview for {session.job_role} - {session.created_at.strftime('%Y-%m-%d')}"
            
            # Create metadata
            metadata = {
                "job_role": session.job_role,
                "interview_style": session.style.value if session.style else None,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "session_id": session_id
            }
            
            # Create transcript
            return self.create_transcript(
                db=db,
                title=title,
                content=content,
                session_id=session_id,
                user_id=session.user_id,
                summary=summary,
                metadata=metadata,
                tags=tags,
                is_imported=False,
                is_public=is_public,
                generate_embeddings=generate_embeddings
            )
            
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error creating transcript from session {session_id}: {str(e)}")
            return None
    
    def export_transcript(
        self, 
        db: Session, 
        transcript_id: int, 
        format: TranscriptFormat = TranscriptFormat.JSON
    ) -> Optional[str]:
        """
        Export a transcript in the specified format.
        
        Args:
            db: Database session
            transcript_id: Transcript ID
            format: Export format
            
        Returns:
            Exported transcript as string or None if there was an error
        """
        transcript = self.get_transcript(db, transcript_id)
        if not transcript:
            return None
        
        try:
            if format == TranscriptFormat.JSON:
                export_data = {
                    "transcript_id": transcript.id,
                    "title": transcript.title,
                    "content": transcript.content,
                    "summary": transcript.summary,
                    "metadata": transcript.metadata,
                    "tags": [tag.name for tag in transcript.tags],
                    "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                    "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None
                }
                return json.dumps(export_data, indent=2)
                
            elif format == TranscriptFormat.TEXT:
                # Convert to plain text format
                lines = [f"# {transcript.title}"]
                
                if transcript.summary:
                    lines.append("\n## Summary")
                    lines.append(transcript.summary)
                
                lines.append("\n## Conversation")
                
                for message in transcript.content:
                    role = message.get("role", "unknown")
                    agent = message.get("agent", "")
                    content = message.get("content", "")
                    
                    if role == "assistant":
                        speaker = f"{agent}" if agent else "Assistant"
                    else:
                        speaker = "User"
                    
                    lines.append(f"\n{speaker}: {content}")
                
                return "\n".join(lines)
                
            elif format == TranscriptFormat.MARKDOWN:
                # Convert to markdown format
                lines = [f"# {transcript.title}"]
                
                if transcript.metadata:
                    lines.append("\n## Metadata")
                    for key, value in transcript.metadata.items():
                        lines.append(f"- **{key}**: {value}")
                
                if transcript.summary:
                    lines.append("\n## Summary")
                    lines.append(transcript.summary)
                
                if transcript.tags:
                    lines.append("\n## Tags")
                    tag_list = ", ".join([tag.name for tag in transcript.tags])
                    lines.append(tag_list)
                
                lines.append("\n## Conversation")
                
                for message in transcript.content:
                    role = message.get("role", "unknown")
                    agent = message.get("agent", "")
                    content = message.get("content", "")
                    timestamp = message.get("timestamp", "")
                    
                    if role == "assistant":
                        speaker = f"**{agent}**" if agent else "**Assistant**"
                    else:
                        speaker = "**User**"
                    
                    time_str = f" _{timestamp}_" if timestamp else ""
                    lines.append(f"\n### {speaker}{time_str}")
                    lines.append(content)
                
                return "\n".join(lines)
                
            elif format == TranscriptFormat.CSV:
                # Convert to CSV format
                lines = ["role,agent,content,timestamp"]
                
                for message in transcript.content:
                    role = message.get("role", "")
                    agent = message.get("agent", "")
                    content = message.get("content", "").replace('"', '""')  # Escape quotes
                    timestamp = message.get("timestamp", "")
                    
                    lines.append(f'"{role}","{agent}","{content}","{timestamp}"')
                
                return "\n".join(lines)
            
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error exporting transcript {transcript_id}: {str(e)}")
            return None
    
    def import_transcript(
        self, 
        db: Session, 
        content: str, 
        format: TranscriptFormat = TranscriptFormat.JSON,
        user_id: Optional[str] = None,
        generate_embeddings: bool = True
    ) -> Optional[Transcript]:
        """
        Import a transcript from a string.
        
        Args:
            db: Database session
            content: Transcript content as string
            format: Import format
            user_id: User ID to associate with the transcript
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            Imported transcript or None if there was an error
        """
        try:
            if format == TranscriptFormat.JSON:
                # Parse JSON
                data = json.loads(content)
                
                # Create transcript
                return self.create_transcript(
                    db=db,
                    title=data.get("title", "Imported Transcript"),
                    content=data.get("content", []),
                    session_id=None,  # Imported transcripts are not tied to a session
                    user_id=user_id,
                    summary=data.get("summary"),
                    metadata=data.get("metadata", {}),
                    tags=data.get("tags", []),
                    is_imported=True,
                    is_public=False,
                    generate_embeddings=generate_embeddings
                )
                
            else:
                self.logger.error(f"Unsupported import format: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error importing transcript: {str(e)}")
            return None
    
    def search_transcripts(
        self, 
        db: Session, 
        query: str,
        user_id: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for transcripts by semantic similarity.
        
        Args:
            db: Database session
            query: Search query
            user_id: Optional user ID to filter by
            tag_names: Optional list of tag names to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of transcript fragments with relevance scores
        """
        try:
            # Generate query embedding
            query_embedding = self.vector_store.generate_embedding(query)
            
            # Get search results from vector store
            results = self.vector_store.similarity_search(query, k=limit * 3)
            
            # Filter results by user_id and tags if provided
            filtered_results = []
            transcript_ids = set()
            
            for result in results:
                # Extract transcript ID from metadata
                metadata = result.get("metadata", {})
                transcript_id = metadata.get("transcript_id")
                
                if not transcript_id:
                    continue
                
                # Get transcript
                transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
                
                if not transcript:
                    continue
                
                # Filter by user_id if provided
                if user_id and transcript.user_id != user_id:
                    continue
                
                # Filter by tags if provided
                if tag_names:
                    transcript_tag_names = [tag.name for tag in transcript.tags]
                    if not all(tag_name in transcript_tag_names for tag_name in tag_names):
                        continue
                
                # Include in results if it passes filters
                filtered_results.append({
                    "transcript_id": transcript_id,
                    "fragment_id": metadata.get("fragment_id"),
                    "title": transcript.title,
                    "content": result.get("text", ""),
                    "relevance_score": result.get("score", 0.0),
                    "created_at": transcript.created_at.isoformat() if transcript.created_at else None
                })
                
                # Keep track of transcript IDs to avoid duplicates
                transcript_ids.add(transcript_id)
                
                # Stop if we have enough results
                if len(filtered_results) >= limit:
                    break
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error searching transcripts: {str(e)}")
            return []
    
    def get_transcript_tags(self, db: Session) -> List[TranscriptTag]:
        """
        Get all transcript tags.
        
        Args:
            db: Database session
            
        Returns:
            List of transcript tags
        """
        return db.query(TranscriptTag).all()
    
    def _generate_transcript_embeddings(self, db: Session, transcript: Transcript) -> bool:
        """
        Generate embeddings for a transcript.
        
        Args:
            db: Database session
            transcript: Transcript to generate embeddings for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract text content from transcript
            content = transcript.content
            if not content:
                return False
            
            # Generate fragments for more granular retrieval
            fragments = self._generate_transcript_fragments(content)
            
            # Prepare texts for batch embedding
            texts = [fragment["text"] for fragment in fragments]
            
            # Generate embeddings
            embeddings = self.vector_store.generate_embeddings(texts)
            
            # Prepare metadata for vector store
            metadatas = []
            for i, fragment in enumerate(fragments):
                metadatas.append({
                    "transcript_id": transcript.id,
                    "fragment_id": i,
                    "position": fragment["position"],
                    "timestamp": fragment["timestamp"]
                })
            
            # Add to vector store
            ids = self.vector_store.add_texts(texts, metadatas)
            
            # Create embedding record
            embedding = TranscriptEmbedding(
                transcript_id=transcript.id,
                model_name=self.vector_store.embedding_model_name,
                embedding_file=f"transcript_{transcript.id}_embedding.pkl",
                dimensions=self.vector_store.dimension,
                created_at=datetime.utcnow()
            )
            db.add(embedding)
            
            # Create fragment records
            for i, fragment in enumerate(fragments):
                fragment_record = TranscriptFragment(
                    transcript_id=transcript.id,
                    content=fragment["text"],
                    start_index=fragment["start_index"],
                    end_index=fragment["end_index"],
                    embedding_vector=str(ids[i]) if ids else None,
                    created_at=datetime.utcnow()
                )
                db.add(fragment_record)
            
            # Update transcript with vector ID
            transcript.vector_id = f"transcript_{transcript.id}"
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings for transcript {transcript.id}: {str(e)}")
            return False
    
    def _generate_transcript_fragments(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate fragments from transcript content for embeddings.
        
        Args:
            content: Transcript content
            
        Returns:
            List of fragment dictionaries
        """
        fragments = []
        
        # Process each message as an individual fragment
        for i, message in enumerate(content):
            role = message.get("role", "unknown")
            agent = message.get("agent", "")
            text = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            # Skip empty messages
            if not text:
                continue
            
            # Create fragment
            prefix = f"{agent}: " if agent and role == "assistant" else f"{role.capitalize()}: "
            fragment_text = prefix + text
            
            fragments.append({
                "text": fragment_text,
                "position": i,
                "timestamp": timestamp,
                "start_index": i,
                "end_index": i
            })
        
        # Create context windows (sliding window of 3 messages)
        if len(content) >= 3:
            for i in range(len(content) - 2):
                window = content[i:i+3]
                
                # Skip windows with empty messages
                if any(not message.get("content", "") for message in window):
                    continue
                
                # Format messages in the window
                texts = []
                for msg in window:
                    role = msg.get("role", "unknown")
                    agent = msg.get("agent", "")
                    text = msg.get("content", "")
                    
                    prefix = f"{agent}: " if agent and role == "assistant" else f"{role.capitalize()}: "
                    texts.append(prefix + text)
                
                # Create fragment
                fragment_text = "\n".join(texts)
                
                fragments.append({
                    "text": fragment_text,
                    "position": i + 0.5,  # Position between messages
                    "timestamp": window[-1].get("timestamp", ""),
                    "start_index": i,
                    "end_index": i + 2
                })
        
        return fragments
        
    def _handle_interview_end(self, event: Event) -> None:
        """
        Handle interview end events to create transcripts.
        
        Args:
            event: The interview end event
        """
        session_id = event.data.get("session_id")
        self.logger.info(f"Received interview_end event for session {session_id}")
        
        # Don't create transcript here - this is handled by API calls 