"""Research agent for gathering topic information."""

from app.agents.base import BaseAgent
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class ResearchAgent(BaseAgent):
    """Agent that researches topics and returns structured information."""

    def __init__(self):
        """Initialize research agent."""
        system_prompt = """You are a research specialist for educational video content creation.

Your task is to research topics and provide well-structured, factual information suitable for 12+ audiences.

Always:
- Focus on accurate, verifiable information
- Identify the 3-5 most important key facts
- Find compelling narrative angles
- Suggest relevant statistics (with sources when possible)
- Maintain a respectful, educational tone
- Ensure all content is appropriate for young audiences

Return your research as JSON with this structure:
{
    "key_facts": ["fact1", "fact2", "fact3"],
    "statistics": [{"stat": "...", "source": "..."}, ...],
    "narrative_angles": ["angle1", "angle2", "angle3"],
    "interesting_details": ["detail1", "detail2"],
    "credibility_notes": "any important caveats or context"
}"""
        super().__init__(system_prompt)

    def research(self, topic: str) -> dict:
        """Research a topic.

        Args:
            topic: Topic to research

        Returns:
            Research data dict

        Raises:
            Exception: If research fails
        """
        try:
            user_message = f"""Please research this topic: "{topic}"

Provide structured research data in JSON format with key facts, statistics, narrative angles, and interesting details suitable for an educational video about this topic."""

            result = self.call_json(user_message, max_tokens=2000)

            logger.info(f"Research completed for: {topic}")
            return result

        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise Exception(f"Research agent failed: {str(e)}")
