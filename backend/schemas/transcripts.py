"""
Pydantic schemas for transcript data validation.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

# Tag schemas
class TranscriptTagBase(BaseModel):
    """Base model for transcript tags."""
    name: str = Field(..., description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")
    color: Optional[str] = Field(None, description="Color for the tag (hex code)")

class TranscriptTagCreate(TranscriptTagBase):
    """Schema for creating a transcript tag."""
    pass

class TranscriptTagUpdate(BaseModel):
    """Schema for updating a transcript tag."""
    name: Optional[str] = Field(None, description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")
    color: Optional[str] = Field(None, description="Color for the tag (hex code)")

class TranscriptTagResponse(TranscriptTagBase):
    """Schema for transcript tag response."""
    id: int = Field(..., description="Tag ID")
    
    class Config:
        orm_mode = True
        from_attributes = True

# Transcript schemas
class TranscriptBase(BaseModel):
    """Base model for transcripts."""
    title: str = Field(..., description="Transcript title")
    content: List[Dict[str, Any]] = Field(..., description="Transcript content as list of message dictionaries")
    summary: Optional[str] = Field(None, description="Transcript summary")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Transcript metadata")

class TranscriptCreate(TranscriptBase):
    """Schema for creating a transcript."""
    session_id: Optional[str] = Field(None, description="Interview session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    tags: Optional[List[str]] = Field(None, description="List of tag names")
    is_imported: bool = Field(False, description="Whether this transcript was imported")
    is_public: bool = Field(False, description="Whether this transcript is publicly accessible")
    generate_embeddings: bool = Field(True, description="Whether to generate embeddings for this transcript")

class TranscriptUpdate(BaseModel):
    """Schema for updating a transcript."""
    title: Optional[str] = Field(None, description="Transcript title")
    content: Optional[List[Dict[str, Any]]] = Field(None, description="Transcript content")
    summary: Optional[str] = Field(None, description="Transcript summary")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Transcript metadata")
    tags: Optional[List[str]] = Field(None, description="List of tag names")
    is_public: Optional[bool] = Field(None, description="Whether this transcript is publicly accessible")
    regenerate_embeddings: bool = Field(False, description="Whether to regenerate embeddings")

class TranscriptResponse(TranscriptBase):
    """Schema for transcript response."""
    id: int = Field(..., description="Transcript ID")
    interview_session_id: Optional[str] = Field(None, description="Interview session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    tags: List[TranscriptTagResponse] = Field([], description="List of tags")
    is_imported: bool = Field(False, description="Whether this transcript was imported")
    is_public: bool = Field(False, description="Whether this transcript is publicly accessible")
    vector_id: Optional[str] = Field(None, description="Vector ID for this transcript")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        orm_mode = True
        from_attributes = True

class TranscriptList(BaseModel):
    """Schema for list of transcripts."""
    total: int = Field(..., description="Total number of transcripts")
    limit: int = Field(..., description="Maximum number of transcripts per page")
    offset: int = Field(..., description="Offset for pagination")
    transcripts: List[TranscriptResponse] = Field(..., description="List of transcripts")

# Fragment schemas
class TranscriptFragmentBase(BaseModel):
    """Base model for transcript fragments."""
    content: str = Field(..., description="Fragment content")
    start_index: int = Field(..., description="Start index in the transcript")
    end_index: int = Field(..., description="End index in the transcript")

class TranscriptFragmentResponse(TranscriptFragmentBase):
    """Schema for transcript fragment response."""
    id: int = Field(..., description="Fragment ID")
    transcript_id: int = Field(..., description="Transcript ID")
    embedding_vector: Optional[str] = Field(None, description="Embedding vector ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        orm_mode = True
        from_attributes = True

# Embedding schemas
class TranscriptEmbeddingBase(BaseModel):
    """Base model for transcript embeddings."""
    model_name: str = Field(..., description="Embedding model name")
    embedding_file: str = Field(..., description="File path for embeddings")
    dimensions: int = Field(..., description="Number of dimensions")

class TranscriptEmbeddingResponse(TranscriptEmbeddingBase):
    """Schema for transcript embedding response."""
    id: int = Field(..., description="Embedding ID")
    transcript_id: int = Field(..., description="Transcript ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        orm_mode = True
        from_attributes = True

# Search schemas
class TranscriptSearch(BaseModel):
    """Schema for transcript search results."""
    transcript_id: int = Field(..., description="Transcript ID")
    fragment_id: Optional[int] = Field(None, description="Fragment ID")
    title: str = Field(..., description="Transcript title")
    content: str = Field(..., description="Fragment content")
    relevance_score: float = Field(..., description="Relevance score")
    created_at: Optional[str] = Field(None, description="Creation timestamp") 