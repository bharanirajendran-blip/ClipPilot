"""JWT authentication middleware using Supabase server-side verification."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


def _get_supabase():
    """Get Supabase client for auth verification."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token via Supabase and return user_id.

    Uses Supabase's auth.get_user() which verifies the token signature
    server-side — no need to manage JWT secrets or JWKS locally.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        user_id from verified token

    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    """
    token = credentials.credentials

    try:
        supabase = _get_supabase()
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        user_id = user_response.user.id
        logger.info(f"Verified token for user: {user_id}")
        return user_id

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_current_user(user_id: str = Depends(verify_jwt_token)) -> str:
    """Get current authenticated user ID.

    Args:
        user_id: User ID from token verification

    Returns:
        user_id
    """
    return user_id
