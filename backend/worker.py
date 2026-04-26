"""ARQ worker entry point.

Usage: python worker.py
"""

from arq.connections import RedisSettings
from arq.worker import run_worker
from urllib.parse import urlparse
from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.worker.tasks import process_video_job

logger = get_logger(__name__)


def parse_redis_url(url: str) -> RedisSettings:
    """Parse a Redis URL into ARQ RedisSettings."""
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
    )


class WorkerSettings:
    """ARQ worker settings class — ARQ discovers this by convention."""
    functions = [process_video_job]
    redis_settings = parse_redis_url(settings.REDIS_URL)
    job_timeout = settings.JOB_TIMEOUT_SECONDS
    allow_abort_jobs = True
    poll_delay = 0.5


if __name__ == "__main__":
    setup_logging()
    logger.info("Starting ARQ worker")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Job timeout: {settings.JOB_TIMEOUT_SECONDS}s")
    run_worker(WorkerSettings)
