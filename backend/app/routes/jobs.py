"""Video job management routes."""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Optional
import uuid
from datetime import datetime
from app.models.schemas import (
    CreateJobRequest,
    JobStatusResponse,
    JobResultResponse,
    JobListResponse,
)
from app.middleware.auth import get_current_user
from app.services.guardrails import check_input_safety
from app.utils.logger import get_logger
from supabase import create_client
from redis import Redis
from arq.connections import RedisSettings, create_pool
from urllib.parse import urlparse
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def get_supabase():
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_redis():
    """Get Redis client."""
    return Redis.from_url(settings.REDIS_URL)


def _parse_redis_url(url: str) -> RedisSettings:
    """Parse Redis URL to ARQ RedisSettings."""
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
    )


def _friendly_job_error(error_detail: str) -> str:
    """Convert technical error messages to user-friendly text."""
    error_lower = error_detail.lower()
    if "queue" in error_lower:
        return "Our servers are busy. Please try again in a few minutes."
    if "daily limit" in error_lower or "global" in error_lower:
        return "We've reached our daily video limit. Please try again tomorrow."
    # Default safe message that doesn't expose internals
    return "Something went wrong. Please try again."


@router.post("", response_model=dict)
async def create_job(
    request: CreateJobRequest,
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
    redis_client: Redis = Depends(get_redis),
) -> dict:
    """Create a new video generation job."""
    try:
        # Input safety check
        logger.info(f"Checking input safety for topic: {request.topic}")
        safety_result = check_input_safety(request.topic)

        if not safety_result.is_safe:
            logger.warning(f"Topic rejected - Category: {safety_result.category}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Topic not appropriate for 12+ audience: {safety_result.reason}",
            )

        # Determine per-user limit (testers get higher limit)
        tester_emails = [e.strip() for e in settings.TESTER_EMAILS.split(",") if e.strip()]
        profile_response = supabase.table("profiles").select("email").eq("id", user_id).execute()
        user_email = profile_response.data[0].get("email", "") if profile_response.data else ""
        user_limit = settings.TESTER_VIDEO_LIMIT if user_email in tester_emails else settings.MAX_VIDEOS_PER_USER

        # Check user lifetime limit (only count completed jobs)
        jobs_response = (
            supabase.table("jobs")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .execute()
        )
        user_video_count = jobs_response.count if jobs_response.count is not None else 0

        if user_video_count >= user_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="You've reached your video limit. Each account can create up to 2 videos.",
            )
        logger.info(f"User {user_id} ({user_email}): {user_video_count}/{user_limit} videos used")

        # Check global daily limit
        daily_key = f"videos:daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
        daily_count = redis_client.get(daily_key)
        daily_count = int(daily_count) if daily_count else 0

        if daily_count >= settings.MAX_VIDEOS_PER_DAY_GLOBAL:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="We've reached our daily video limit. Please try again tomorrow.",
            )

        # Create job record
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "user_id": user_id,
            "topic": request.topic.strip(),
            "style": request.style.value,
            "duration": request.duration.value,
            "status": "queued",
            "progress": 0,
            "current_step": "Queued",
            "include_narration": request.include_narration,
            "include_captions": request.include_captions,
            "include_music": request.include_music,
        }

        if request.music_url:
            # Validate music URL points to our Supabase storage
            from urllib.parse import urlparse
            parsed_music = urlparse(request.music_url)
            supabase_host = urlparse(settings.SUPABASE_URL).hostname
            if not (parsed_music.hostname == supabase_host):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Music URL must be from our storage. Please upload via the music upload button.",
                )
            job_data["music_url"] = request.music_url

        supabase.table("jobs").insert(job_data).execute()
        logger.info(f"Created job: {job_id}")

        # Enqueue ARQ task — if this fails, mark job as failed and return error
        try:
            redis_settings = _parse_redis_url(settings.REDIS_URL)
            pool = await create_pool(redis_settings)
            await pool.enqueue_job("process_video_job", job_id, _job_id=job_id)
            logger.info(f"Enqueued task for job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to enqueue task: {str(e)}")
            # Mark job as failed so it doesn't sit in 'queued' forever
            supabase.table("jobs").update({
                "status": "failed",
                "error_message": "Failed to queue job for processing. Please try again.",
            }).eq("id", job_id).execute()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Our servers are busy. Please try again in a few minutes.",
            )

        # Increment global daily counter only after successful enqueue
        redis_client.incr(daily_key)
        redis_client.expire(daily_key, 86400)

        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Video generation queued",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Please try again.",
        )


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> dict:
    """Get job status."""
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        job = response.data

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return {
            "status": job["status"],
            "progress": job.get("progress", 0),
            "current_step": job.get("current_step", ""),
            "error_message": job.get("error_message"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job status")


@router.get("/{job_id}/result")
async def get_job_result(
    job_id: str,
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> dict:
    """Get job result with video URL."""
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        job = response.data

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")

        return {
            "video_url": job.get("video_url", ""),
            "thumbnail_url": job.get("thumbnail_url", ""),
            "title": job.get("title", "Untitled"),
            "description": job.get("description", ""),
            "tags": job.get("tags", []),
            "research_data": job.get("research_data"),
            "script_data": job.get("script_data"),
            "shot_list_data": job.get("shot_list_data"),
            "metrics": job.get("metrics"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job result: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job result")


@router.post("/upload-music")
async def upload_music(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> dict:
    """Upload custom background music file to Supabase Storage."""
    try:
        # Validate file type
        allowed_types = {"audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/ogg"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: MP3, WAV, M4A, WebM. Got: {file.content_type}"
            )

        # Read file content
        file_content = await file.read()

        # Validate file size (max 20MB)
        max_size = 20 * 1024 * 1024  # 20MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: 20MB, got: {len(file_content) / 1024 / 1024:.1f}MB"
            )

        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if file.filename else "mp3"
        unique_filename = f"{user_id}/{uuid.uuid4()}.{file_ext}"

        # Upload to Supabase Storage (audio bucket)
        response = supabase.storage.from_("audio").upload(
            unique_filename,
            file_content,
            {"content-type": file.content_type}
        )
        logger.info(f"Uploaded music file: {unique_filename}")

        # Get public URL
        music_url = supabase.storage.from_("audio").get_public_url(unique_filename)

        return {
            "music_url": music_url,
            "filename": file.filename,
            "size": len(file_content),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Music upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Music upload failed: {str(e)}"
        )


@router.get("")
async def list_user_jobs(
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> dict:
    """List user's jobs."""
    try:
        response = (
            supabase.table("jobs")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        jobs = [
            {
                "id": job["id"],
                "topic": job["topic"],
                "style": job["style"],
                "duration": job["duration"],
                "status": job["status"],
                "progress": job.get("progress", 0),
                "current_step": job.get("current_step", ""),
                "video_url": job.get("video_url"),
                "thumbnail_url": job.get("thumbnail_url"),
                "title": job.get("title"),
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
            }
            for job in response.data
        ]

        return {"jobs": jobs, "total": len(jobs)}

    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> dict:
    """Cancel a running or queued job.

    Sets the DB status to 'failed' so the worker's _update_job_step
    detects the cancellation and stops the pipeline. Also attempts to
    abort the ARQ job in Redis so it won't be re-picked on restart.
    """
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        job = response.data

        if not job:
            raise HTTPException(status_code=404, detail="Video not found.")

        if job["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if job["status"] in ("completed", "failed"):
            raise HTTPException(status_code=400, detail="Job already finished")

        # Mark as failed in DB — worker checks this at every step
        supabase.table("jobs").update({
            "status": "failed",
            "error_message": "Cancelled by user",
            "current_step": "Cancelled",
        }).eq("id", job_id).execute()

        # Also abort the ARQ job in Redis so it won't retry on restart
        try:
            redis_settings = _parse_redis_url(settings.REDIS_URL)
            pool = await create_pool(redis_settings)
            await pool.abort_job(job_id)
            logger.info(f"ARQ job aborted in Redis: {job_id}")
        except Exception as abort_err:
            # Non-fatal — the DB flag will still stop the worker
            logger.warning(f"Could not abort ARQ job (non-fatal): {abort_err}")

        logger.info(f"Job cancelled by user: {job_id}")
        return {"status": "cancelled", "job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> dict:
    """Delete a job and its associated storage files."""
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        job = response.data

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Block deletion of active jobs — must cancel first
        if job["status"] in ("queued", "processing"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This video is still being generated. Cancel it first before deleting.",
            )

        # Delete storage files if they exist (paths match StorageService)
        try:
            supabase.storage.from_("videos").remove([
                f"{job_id}/video.mp4",
                f"{job_id}/thumbnail.png",
            ])
        except Exception as e:
            logger.warning(f"Failed to delete storage files: {str(e)}")

        # Delete uploaded music if it exists
        if job.get("music_url"):
            try:
                from urllib.parse import urlparse
                music_path = urlparse(job["music_url"]).path.split("/audio/")[-1]
                if music_path:
                    supabase.storage.from_("audio").remove([music_path])
            except Exception as e:
                logger.warning(f"Failed to delete music file: {str(e)}")

        # Delete job record
        supabase.table("jobs").delete().eq("id", job_id).execute()

        logger.info(f"Job deleted by user: {job_id}")
        return {"status": "deleted", "job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete job")


@router.get("/{job_id}/share")
async def get_shared_result(
    job_id: str,
    supabase=Depends(get_supabase),
) -> dict:
    """Get public share data for a completed video. No auth required."""
    try:
        response = supabase.table("jobs").select(
            "video_url, thumbnail_url, title, description, tags, status"
        ).eq("id", job_id).single().execute()
        job = response.data

        if not job:
            raise HTTPException(status_code=404, detail="Video not found")

        if job["status"] != "completed":
            raise HTTPException(status_code=404, detail="Video not available")

        return {
            "video_url": job.get("video_url", ""),
            "thumbnail_url": job.get("thumbnail_url", ""),
            "title": job.get("title", "Untitled"),
            "description": job.get("description", ""),
            "tags": job.get("tags", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get shared result: {str(e)}")
        raise HTTPException(status_code=404, detail="Video not found")
