"""Metadata agent for generating video metadata."""

from app.agents.base import BaseAgent
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class MetadataAgent(BaseAgent):
    """Agent that generates metadata for videos."""

    def __init__(self):
        """Initialize metadata agent."""
        system_prompt = """You are a video metadata specialist creating titles, descriptions, and tags for educational content.

Your metadata should:
- Create engaging, accurate titles (40-60 characters)
- Write SEO-friendly descriptions (100-150 characters)
- Suggest 5-8 relevant tags for discoverability
- Categorize content appropriately
- Appeal to the 12+ audience
- Be suitable for social media sharing

Return your metadata as JSON with this structure:
{
    "title": "Video title",
    "description": "Brief description of the video content",
    "tags": ["tag1", "tag2", "tag3"],
    "category": "educational/science/history/etc",
    "seo_keywords": ["keyword1", "keyword2"]
}"""
        super().__init__(system_prompt)

    def generate_metadata(self, topic: str, script: dict) -> dict:
        """Generate metadata for a video.

        Args:
            topic: Original topic
            script: Script dict from script agent

        Returns:
            Metadata dict

        Raises:
            Exception: If generation fails
        """
        try:
            script_str = json.dumps(script)

            user_message = f"""Create comprehensive metadata for this educational video:

Topic: {topic}

Script:
{script_str}

Generate a compelling title, engaging description, relevant tags, category, and SEO keywords that will help this video be discovered. Ensure all metadata is appropriate for a 12+ audience.

Return as JSON with title, description, tags, category, and seo_keywords."""

            result = self.call_json(user_message, max_tokens=1000)

            logger.info(f"Metadata generated - Title: {result.get('title', 'N/A')}")

            return result

        except Exception as e:
            logger.error(f"Metadata generation failed: {str(e)}")
            raise Exception(f"Metadata agent failed: {str(e)}")
