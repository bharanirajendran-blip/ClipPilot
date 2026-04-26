"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class StyleEnum(str, Enum):
    """Video style options."""
    educational = "educational"
    storytelling = "storytelling"
    explainer = "explainer"
    news = "news"


class DurationEnum(int, Enum):
    """Video duration options in seconds."""
    thirty = 30
    sixty = 60
    ninety = 90


class CreateJobRequest(BaseModel):
    """Request to create a new video generation job."""
    topic: str = Field(..., min_length=3, max_length=500, description="Topic for the video")
    style: StyleEnum = Field(default=StyleEnum.educational, description="Video style")
    duration: DurationEnum = Field(default=DurationEnum.thirty, description="Video duration in seconds")
    audio_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "How solar panels convert sunlight into electricity",
                "style": "educational",
                "duration": 30
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status."""
    job_id: str
    status: str
    progress: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "status": "processing",
                "progress": 45,
                "current_step": "Generating video",
                "created_at": "2024-04-21T10:00:00Z",
                "updated_at": "2024-04-21T10:02:30Z",
                "error_message": None
            }
        }


class JobResultResponse(BaseModel):
    """Response for completed job with video result."""
    job_id: str
    status: str
    video_url: str
    thumbnail_url: str
    title: str
    description: str
    tags: List[str]
    category: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "status": "completed",
                "video_url": "https://bucket.com/videos/job_123abc/video.mp4",
                "thumbnail_url": "https://bucket.com/videos/job_123abc/thumb.png",
                "title": "Solar Power Explained",
                "description": "Learn how solar panels work",
                "tags": ["energy", "science", "renewable"],
                "category": "educational",
                "created_at": "2024-04-21T10:00:00Z",
                "completed_at": "2024-04-21T10:15:00Z",
                "metadata": {}
            }
        }


class UserProfile(BaseModel):
    """User profile information."""
    user_id: str
    email: str
    videos_created: int
    videos_remaining: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "email": "user@example.com",
                "videos_created": 1,
                "videos_remaining": 1,
                "created_at": "2024-04-20T12:00:00Z",
                "updated_at": "2024-04-21T10:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "1.0.0"
            }
        }


class JobListResponse(BaseModel):
    """List of user jobs."""
    jobs: List[JobStatusResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "jobs": [],
                "total": 0
            }
        }


class GuardrailResult(BaseModel):
    """Result of guardrail check."""
    is_safe: bool
    reason: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None  # "hard" = block, "soft" = warn only
    warnings: List[str] = []  # Soft warnings that don't block execution
