"""ARQ worker configuration."""

from arq.connections import RedisSettings
from urllib.parse import urlparse
from app.config import settings
from app.worker.tasks import process_video_job


def _parse_redis_url(url: str) -> RedisSettings:
    """Parse Redis URL to ARQ RedisSettings."""
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
    )


class WorkerSettings:
    """ARQ worker settings — arq CLI discovers this class by name."""

    functions = [process_video_job]
    redis_settings = _parse_redis_url(settings.REDIS_URL)
    job_timeout = settings.JOB_TIMEOUT_SECONDS
    allow_abort_jobs = True
    poll_delay_ms = 500
