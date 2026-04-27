"""Script agent for generating video scripts."""

from app.agents.base import BaseAgent
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class ScriptAgent(BaseAgent):
    """Agent that generates timed video scripts."""

    def __init__(self):
        """Initialize script agent."""
        system_prompt = """You are a video scriptwriter creating short-form educational video scripts. The visual descriptions you write will be sent to an AI video generator (Runway Gen-3) to create real video clips.

NARRATION RULES:
- Scene 1 must start with a strong hook, not an introduction like "Today we will learn..."
- Each 8-second scene should contain 15-22 spoken words.
- Each scene should explain exactly one main idea.
- Avoid filler phrases such as "in this video", "let's dive in", "did you know", "have you ever wondered".
- Do not mention unsupported statistics unless they appear in the research data.
- If the research includes "avoid_claims", do NOT include those claims in narration.
- End with a satisfying takeaway, not a generic call to action.
- Be engaging and appropriate for 12+ audiences.

VISUAL DESCRIPTION RULES:
Every visual_description MUST describe a REAL scene that a camera could actually film. The AI video generator will try to create realistic footage from your description.
- The visuals should form a coherent sequence, not unrelated stock footage.
- Reuse a consistent visual motif, subject, or setting across scenes when possible.
- For abstract topics, use concrete analogies that can be filmed.

MUST INCLUDE in every visual_description:
- A SPECIFIC subject: real person, animal, object, or place (e.g., "a young woman with dark hair" not "a person")
- A SPECIFIC environment: real location with details (e.g., "a modern chemistry lab with glass beakers on a steel table" not "a lab")
- ONE clear action or motion (e.g., "pouring blue liquid into a flask" not "doing science")
- Lighting and atmosphere (e.g., "soft fluorescent overhead lighting" or "golden sunset light")
- Camera framing (e.g., "close-up", "wide establishing shot", "medium shot from waist up")

NEVER INCLUDE in visual_description:
- Abstract concepts ("show the idea of freedom")
- Text, titles, charts, graphs, screens, documents, whiteboards, labels, maps, UI elements, equations, or readable text (the video generator cannot create text) — unless the style is animated
- Multiple rapid cuts or transitions (describe ONE continuous shot per scene)
- Named real people or celebrities
- Prefer physical metaphors: objects moving, people demonstrating, natural processes, lab actions, environments changing

GOOD: "Wide shot of a coral reef teeming with colorful tropical fish, sunlight filtering through turquoise water, a sea turtle gliding slowly through the frame, underwater camera gently tracking forward"
BAD: "Show marine biodiversity and ocean conservation concepts"

Return your script as JSON with this structure:
{
    "title": "Video title",
    "scenes": [
        {
            "scene_number": 1,
            "duration_seconds": 8,
            "narration": "Script text for narrator...",
            "visual_description": "A specific, filmable scene description..."
        }
    ],
    "total_duration": 30,
    "notes": "any special instructions"
}"""
        super().__init__(system_prompt)

    def generate_script(
        self, topic: str, style: str, duration: int, research: dict,
        revision_feedback: str | None = None,
    ) -> dict:
        """Generate a video script.

        Args:
            topic: Video topic
            style: Video style (educational, storytelling, explainer, documentary, animated)
            duration: Target duration in seconds (30, 60, or 90)
            research: Research data from research agent
            revision_feedback: Optional feedback from the review agent for revisions

        Returns:
            Script dict

        Raises:
            Exception: If script generation fails
        """
        try:
            research_str = json.dumps(research)

            user_message = f"""Create a {duration}-second {style} video script about: {topic}

Research data to use:
{research_str}

Write a clear, engaging script with visual descriptions for each scene. The script should be appropriate for a 12+ audience and fit exactly within {duration} seconds total.

IMPORTANT: Each scene MUST be exactly 8 seconds long (duration_seconds: 8). For a {duration}-second video, create exactly {duration // 8} scenes.
Keep narration for each scene under 20 words so it can be spoken naturally within 8 seconds.

Before returning JSON, verify:
1. Every scene has duration_seconds: 8
2. Number of scenes == {duration // 8} (so total = {duration} seconds)
3. Each scene's narration is 15-22 words
4. Every visual_description contains a real subject, real setting, one action, lighting, and camera framing
5. Every factual claim is supported by the research data above
6. The scenes feel connected as one coherent short video
7. No visual_description relies on readable text

Return as JSON with scenes array, each containing: scene_number, duration_seconds, narration, and visual_description."""

            if revision_feedback:
                user_message += f"""

IMPORTANT — REVISION REQUIRED:
A reviewer found issues with the previous draft. You MUST address every item below:

{revision_feedback}

Fix all issues listed above while keeping the same topic and style."""

            result = self.call_json(user_message, max_tokens=3000)

            # Validate scene durations sum to target duration
            if "scenes" in result:
                total = sum(s.get("duration_seconds", 0) for s in result["scenes"])
                logger.info(f"Script generated with {len(result['scenes'])} scenes, total {total}s (target {duration}s)")

            return result

        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise Exception(f"Script agent failed: {str(e)}")
