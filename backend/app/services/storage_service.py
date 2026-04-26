"""Supabase Storage service for video uploads."""

from supabase import Client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StorageService:
    """Service for managing video and thumbnail storage in Supabase."""

    BUCKET_NAME = "videos"

    def __init__(self, supabase_client: Client):
        """Initialize storage service.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client

    def upload_video(self, job_id: str, video_bytes: bytes) -> str:
        """Upload video to Supabase Storage.

        Args:
            job_id: Job ID for file path
            video_bytes: Video file bytes

        Returns:
            Public URL of uploaded video

        Raises:
            Exception: If upload fails
        """
        try:
            file_path = f"{job_id}/video.mp4"

            self.supabase.storage.from_(self.BUCKET_NAME).upload(
                file_path,
                video_bytes,
                {
                    "contentType": "video/mp4",
                },
            )

            # Get public URL
            public_url = self.supabase.storage.from_(self.BUCKET_NAME).get_public_url(file_path)

            logger.info(f"Uploaded video: {file_path} -> {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Video upload failed: {str(e)}")
            raise Exception(f"Failed to upload video: {str(e)}")

    def upload_thumbnail(self, job_id: str, thumbnail_bytes: bytes) -> str:
        """Upload thumbnail to Supabase Storage.

        Args:
            job_id: Job ID for file path
            thumbnail_bytes: PNG thumbnail bytes

        Returns:
            Public URL of uploaded thumbnail

        Raises:
            Exception: If upload fails
        """
        try:
            file_path = f"{job_id}/thumbnail.png"

            self.supabase.storage.from_(self.BUCKET_NAME).upload(
                file_path,
                thumbnail_bytes,
                {
                    "contentType": "image/png",
                },
            )

            # Get public URL
            public_url = self.supabase.storage.from_(self.BUCKET_NAME).get_public_url(file_path)

            logger.info(f"Uploaded thumbnail: {file_path} -> {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Thumbnail upload failed: {str(e)}")
            raise Exception(f"Failed to upload thumbnail: {str(e)}")

    def delete_job_files(self, job_id: str) -> None:
        """Delete all files for a job.

        Args:
            job_id: Job ID to delete

        Raises:
            Exception: If deletion fails
        """
        try:
            files_to_delete = [f"{job_id}/video.mp4", f"{job_id}/thumbnail.png"]

            for file_path in files_to_delete:
                try:
                    self.supabase.storage.from_(self.BUCKET_NAME).remove([file_path])
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {str(e)}")

            logger.info(f"Deleted files for job: {job_id}")

        except Exception as e:
            logger.error(f"Job deletion failed: {str(e)}")
            raise Exception(f"Failed to delete job files: {str(e)}")
