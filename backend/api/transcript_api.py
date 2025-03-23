"""
API endpoints for transcript management.
Includes routes for creating, retrieving, updating, deleting transcripts,
as well as searching and export/import functionality.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.models.transcript import TranscriptFormat
from backend.services.transcript_service import TranscriptService
from backend.schemas.transcripts import (
    TranscriptCreate, 
    TranscriptResponse, 
    TranscriptUpdate,
    TranscriptSearch,
    TranscriptList,
    TranscriptTagResponse
)

# Initialize router
router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize service
transcript_service = TranscriptService(logger=logger)

# Routes
@router.post("", response_model=TranscriptResponse)
async def create_transcript(
    transcript_data: TranscriptCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transcript.
    """
    transcript = transcript_service.create_transcript(
        db=db,
        title=transcript_data.title,
        content=transcript_data.content,
        session_id=transcript_data.session_id,
        user_id=transcript_data.user_id,
        summary=transcript_data.summary,
        metadata=transcript_data.metadata,
        tags=transcript_data.tags,
        is_imported=transcript_data.is_imported,
        is_public=transcript_data.is_public,
        generate_embeddings=transcript_data.generate_embeddings
    )
    
    if not transcript:
        raise HTTPException(status_code=500, detail="Failed to create transcript")
        
    return TranscriptResponse.from_orm(transcript)

@router.post("/from-session", response_model=TranscriptResponse)
async def create_transcript_from_session(
    session_id: str = Query(..., description="Interview session ID"),
    title: Optional[str] = Query(None, description="Optional title for the transcript"),
    summary: Optional[str] = Query(None, description="Optional summary for the transcript"),
    tags: Optional[List[str]] = Query(None, description="Optional tags for the transcript"),
    is_public: bool = Query(False, description="Whether the transcript is publicly accessible"),
    generate_embeddings: bool = Query(True, description="Whether to generate embeddings"),
    db: Session = Depends(get_db)
):
    """
    Create a transcript from an existing interview session.
    """
    transcript = transcript_service.create_transcript_from_session(
        db=db,
        session_id=session_id,
        title=title,
        summary=summary,
        tags=tags,
        is_public=is_public,
        generate_embeddings=generate_embeddings
    )
    
    if not transcript:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found or has no messages")
        
    return TranscriptResponse.from_orm(transcript)

@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a transcript by ID.
    """
    transcript = transcript_service.get_transcript(db, transcript_id)
    
    if not transcript:
        raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        
    return TranscriptResponse.from_orm(transcript)

@router.get("", response_model=TranscriptList)
async def list_transcripts(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_imported: Optional[bool] = Query(None, description="Filter by imported status"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    limit: int = Query(100, description="Maximum number of transcripts to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List transcripts with optional filtering.
    """
    transcripts = transcript_service.get_transcripts(
        db=db,
        user_id=user_id,
        session_id=session_id,
        tag_names=tags,
        is_imported=is_imported,
        is_public=is_public,
        limit=limit,
        offset=offset
    )
    
    return TranscriptList(
        total=len(transcripts),
        limit=limit,
        offset=offset,
        transcripts=[TranscriptResponse.from_orm(t) for t in transcripts]
    )

@router.put("/{transcript_id}", response_model=TranscriptResponse)
async def update_transcript(
    transcript_id: int,
    transcript_data: TranscriptUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a transcript.
    """
    transcript = transcript_service.update_transcript(
        db=db,
        transcript_id=transcript_id,
        title=transcript_data.title,
        content=transcript_data.content,
        summary=transcript_data.summary,
        metadata=transcript_data.metadata,
        tags=transcript_data.tags,
        is_public=transcript_data.is_public,
        regenerate_embeddings=transcript_data.regenerate_embeddings
    )
    
    if not transcript:
        raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        
    return TranscriptResponse.from_orm(transcript)

@router.delete("/{transcript_id}")
async def delete_transcript(
    transcript_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a transcript.
    """
    success = transcript_service.delete_transcript(db, transcript_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        
    return {"message": f"Transcript {transcript_id} deleted successfully"}

@router.get("/{transcript_id}/export")
async def export_transcript(
    transcript_id: int,
    format: TranscriptFormat = Query(TranscriptFormat.JSON, description="Export format"),
    db: Session = Depends(get_db)
):
    """
    Export a transcript in the specified format.
    """
    transcript = transcript_service.get_transcript(db, transcript_id)
    
    if not transcript:
        raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
    
    # Get the exported content
    content = transcript_service.export_transcript(db, transcript_id, format)
    
    if not content:
        raise HTTPException(status_code=500, detail="Failed to export transcript")
    
    # Set appropriate filename and headers based on format
    filename = f"transcript_{transcript_id}"
    media_type = "application/json"
    
    if format == TranscriptFormat.JSON:
        filename += ".json"
        media_type = "application/json"
    elif format == TranscriptFormat.TEXT:
        filename += ".txt"
        media_type = "text/plain"
    elif format == TranscriptFormat.MARKDOWN:
        filename += ".md"
        media_type = "text/markdown"
    elif format == TranscriptFormat.CSV:
        filename += ".csv"
        media_type = "text/csv"
    
    # Return the content with appropriate headers
    return JSONResponse(
        content={"content": content, "filename": filename},
        media_type=media_type
    )

@router.post("/import", response_model=TranscriptResponse)
async def import_transcript(
    file: UploadFile = File(...),
    format: TranscriptFormat = Query(TranscriptFormat.JSON, description="Import format"),
    user_id: Optional[str] = Query(None, description="User ID to associate with the transcript"),
    generate_embeddings: bool = Query(True, description="Whether to generate embeddings"),
    db: Session = Depends(get_db)
):
    """
    Import a transcript from a file.
    """
    # Read the file content
    content = await file.read()
    content_str = content.decode("utf-8")
    
    # Import the transcript
    transcript = transcript_service.import_transcript(
        db=db,
        content=content_str,
        format=format,
        user_id=user_id,
        generate_embeddings=generate_embeddings
    )
    
    if not transcript:
        raise HTTPException(status_code=500, detail="Failed to import transcript")
        
    return TranscriptResponse.from_orm(transcript)

@router.post("/search", response_model=List[TranscriptSearch])
async def search_transcripts(
    query: str = Query(..., description="Search query"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(5, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search for transcripts by semantic similarity.
    """
    results = transcript_service.search_transcripts(
        db=db,
        query=query,
        user_id=user_id,
        tag_names=tags,
        limit=limit
    )
    
    return results

@router.get("/tags", response_model=List[TranscriptTagResponse])
async def get_transcript_tags(
    db: Session = Depends(get_db)
):
    """
    Get all transcript tags.
    """
    tags = transcript_service.get_transcript_tags(db)
    
    return [TranscriptTagResponse.from_orm(tag) for tag in tags] 