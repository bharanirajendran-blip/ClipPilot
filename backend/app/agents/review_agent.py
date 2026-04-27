"""Review agent for quality assurance."""

from app.agents.base import BaseAgent
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class ReviewAgent(BaseAgent):
    """Agent that reviews scripts and shot lists for quality and compliance."""

    def __init__(self):
        """Initialize review agent."""
        system_prompt = """You are a strict quality assurance reviewer for educational video content.

Your review checklist:
- Content accuracy: Facts are correct and well-presented
- Age appropriateness: Content is suitable for 12+ audiences
- Tone consistency: Voice and style are consistent throughout
- Pacing: Scene durations are realistic and engaging
- Clarity: Instructions and descriptions are clear
- Visual coherence: Visual descriptions match the narration and feel connected

REJECT or request revision if:
- Any scene has generic stock-footage visuals (e.g., "a person standing", "a city skyline")
- Visuals depend on readable text, charts, screens, documents, whiteboards, or labels
- Narration includes claims not supported by research data
- Scenes feel disconnected from each other (random locations/subjects)
- Scene 1 lacks a hook (starts with "Today we will learn..." or similar)
- Final scene does not provide a clear takeaway
- Any scene narration exceeds 22 words (too long for 8 seconds)

Score these dimensions 1-10:
- accuracy: Are facts correct and supported by research?
- visual_coherence: Do the shots feel like one video, not random clips?
- filmability: Can the AI video generator actually produce these visuals?
- pacing: Is each scene's narration speakable in the allotted time?
- age_appropriateness: Is the content suitable for 12+ audiences?

If any score is below 7, set revision_needed=true.

Return your review as JSON with this structure:
{
    "approved": true/false,
    "scores": {
        "accuracy": 0,
        "visual_coherence": 0,
        "filmability": 0,
        "pacing": 0,
        "age_appropriateness": 0
    },
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "compliance_notes": "Any 12+ compliance concerns",
    "revision_needed": false,
    "revision_details": "Specific changes needed if revision_needed is true"
}"""
        super().__init__(system_prompt)

    def review(self, topic: str, script: dict, shot_list: dict) -> dict:
        """Review script and shot list.

        Args:
            topic: Original topic
            script: Script dict from script agent
            shot_list: Shot list dict from shot list agent

        Returns:
            Review result dict

        Raises:
            Exception: If review fails
        """
        try:
            script_str = json.dumps(script)
            shot_list_str = json.dumps(shot_list)

            user_message = f"""Please review this video script and shot list for topic: "{topic}"

Script:
{script_str}

Shot List:
{shot_list_str}

Perform a comprehensive review checking for accuracy, age-appropriateness (12+ audience), tone consistency, pacing, clarity, and visual coherence.

Return your review as JSON indicating whether the script is approved, any issues found, suggestions for improvement, and whether revisions are needed."""

            result = self.call_json(user_message, max_tokens=2000)

            approved = result.get("approved", False)
            revision_needed = result.get("revision_needed", False)

            logger.info(f"Review completed - Approved: {approved}, Revision needed: {revision_needed}")

            return result

        except Exception as e:
            logger.error(f"Review failed: {str(e)}")
            raise Exception(f"Review agent failed: {str(e)}")
