"""Authentication and user profile routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from app.models.schemas import UserProfile
from app.middleware.auth import get_current_user
from app.utils.logger import get_logger
from supabase import create_client
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])


def get_supabase():
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase),
) -> UserProfile:
    """Get user profile with video quota info.

    Args:
        user_id: Current user ID
        supabase: Supabase client

    Returns:
        User profile with video limits
    """
    try:
        # Get profile from profiles table
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()

        if response.data and len(response.data) > 0:
            profile = response.data[0]
            logger.info(f"Found profile for user: {user_id}")
        else:
            # Profile should be auto-created by trigger, but handle edge case
            profile = {
                "id": user_id,
                "email": "",
                "videos_created": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            logger.warning(f"No profile found for user: {user_id}, using defaults")

        # Count user's completed jobs only (failed jobs don't count)
        jobs_response = (
            supabase.table("jobs")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .execute()
        )
        videos_created = jobs_response.count if jobs_response.count is not None else 0

        # Testers get higher limit
        tester_emails = [e.strip() for e in settings.TESTER_EMAILS.split(",") if e.strip()]
        user_email = profile.get("email", "")
        user_limit = settings.TESTER_VIDEO_LIMIT if user_email in tester_emails else settings.MAX_VIDEOS_PER_USER
        videos_remaining = max(0, user_limit - videos_created)

        return UserProfile(
            user_id=user_id,
            email=profile.get("email", ""),
            videos_created=videos_created,
            videos_remaining=videos_remaining,
            created_at=datetime.fromisoformat(
                profile.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
                if "Z" in profile.get("created_at", "")
                else profile.get("created_at", datetime.utcnow().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                profile.get("updated_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
                if "Z" in profile.get("updated_at", "")
                else profile.get("updated_at", datetime.utcnow().isoformat())
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}",
        )
