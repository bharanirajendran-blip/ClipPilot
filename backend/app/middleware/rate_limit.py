"""Rate limiting middleware."""

from fastapi import HTTPException, status
from app.config import settings
from app.utils.logger import get_logger
from supabase import Client
from redis import Redis
from datetime import datetime, timedelta

logger = get_logger(__name__)


async def check_user_lifetime_limit(user_id: str, supabase_client: Client) -> None:
    """Check if user has exceeded lifetime video limit.

    Args:
        user_id: User ID
        supabase_client: Supabase client

    Raises:
        HTTPException: If limit exceeded
    """
    try:
        response = supabase_client.table("jobs").select("COUNT(*)").eq("user_id", user_id).execute()

        if response.data and len(response.data) > 0:
            count = response.data[0].get("count", 0)
        else:
            count = 0

        if count >= settings.MAX_VIDEOS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"You have reached the maximum lifetime limit of {settings.MAX_VIDEOS_PER_USER} videos.",
            )

        logger.info(f"User {user_id} has created {count} videos (limit: {settings.MAX_VIDEOS_PER_USER})")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking user lifetime limit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limit check failed",
        )


async def check_global_daily_limit(redis_client: Redis) -> None:
    """Check if global daily video limit has been reached.

    Args:
        redis_client: Redis client

    Raises:
        HTTPException: If limit exceeded
    """
    try:
        key = f"videos:daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
        current_count = redis_client.get(key)

        if current_count is None:
            current_count = 0
            redis_client.setex(key, 86400, 0)  # 24 hour TTL
        else:
            current_count = int(current_count)

        if current_count >= settings.MAX_VIDEOS_PER_DAY_GLOBAL:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Global daily limit of {settings.MAX_VIDEOS_PER_DAY_GLOBAL} videos reached. Please try again tomorrow.",
            )

        logger.info(f"Global daily video count: {current_count}/{settings.MAX_VIDEOS_PER_DAY_GLOBAL}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking global daily limit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limit check failed",
        )


def increment_global_daily_count(redis_client: Redis) -> None:
    """Increment global daily video counter.

    Args:
        redis_client: Redis client
    """
    try:
        key = f"videos:daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
        redis_client.incr(key)
        redis_client.expire(key, 86400)  # Refresh 24 hour TTL
        logger.info(f"Incremented global daily counter: {key}")
    except Exception as e:
        logger.error(f"Error incrementing global daily counter: {str(e)}")
