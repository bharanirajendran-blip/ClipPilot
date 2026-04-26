"""Shot list agent for generating visual prompts."""

from app.agents.base import BaseAgent
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class ShotListAgent(BaseAgent):
    """Agent that creates shot-by-shot visual prompts for video generation."""

    def __init__(self):
        """Initialize shot list agent."""
        system_prompt = """You are an expert cinematographer writing prompts for Runway Gen-3 Alpha Turbo AI video generation.

Your prompts will be sent DIRECTLY to Runway's API to generate real video clips. Runway works best with:
- REAL-WORLD scenes featuring REAL subjects (people, animals, objects, landscapes)
- Specific physical descriptions: "a woman with curly brown hair in a blue lab coat" NOT "a scientist"
- Concrete environments: "a sunlit greenhouse with rows of tomato plants" NOT "a nature setting"
- Camera motion: "slow dolly forward", "steady tracking shot left to right", "gentle push-in zoom"
- Lighting: "warm golden hour sunlight", "soft diffused overhead lighting", "dramatic side-lit"
- NO text, charts, diagrams, UI elements, or abstract concepts — Runway cannot generate these
- NO narration or dialogue text in the prompt — only visual descriptions
- Keep each prompt under 500 characters for best results

CRITICAL RULES for Runway Gen-3:
1. Every prompt must describe something a real camera could film
2. Describe ONE continuous shot per prompt (no cuts or transitions)
3. Include exactly ONE clear subject doing ONE action
4. Specify the environment/background explicitly
5. Include at least one type of motion (camera or subject movement)
6. Use photographic language: depth of field, lens type, exposure feel

GOOD example: "Close-up of honey dripping slowly from a wooden dipper into a glass jar, warm amber backlight, shallow depth of field, kitchen counter with herbs in background, slow motion, cinematic"
BAD example: "Show the concept of sweetness and natural food production processes"

Return your shot list as JSON with this structure:
{
    "shots": [
        {
            "scene_number": 1,
            "prompt": "Runway-ready visual prompt describing a real filmable scene...",
            "style_descriptors": ["cinematic", "warm lighting", "shallow DOF"],
            "camera_direction": "Close-up, slow push-in"
        }
    ]
}"""
        super().__init__(system_prompt)

    def generate_shot_list(self, script: dict) -> dict:
        """Generate shot-by-shot prompts from script.

        Args:
            script: Script dict from script agent

        Returns:
            Shot list dict with optimized prompts

        Raises:
            Exception: If generation fails
        """
        try:
            script_str = json.dumps(script)

            user_message = f"""Convert this video script into shot-by-shot visual prompts optimized for Runway Gen-3 video generation:

{script_str}

For each scene, create a detailed, specific visual prompt that captures the essence of the scene and the narration. Include camera angles, lighting, mood, and visual style information.

Return as JSON with "shots" array containing scene_number, prompt, style_descriptors, and camera_direction for each scene."""

            result = self.call_json(user_message, max_tokens=3000)

            if "shots" in result:
                logger.info(f"Shot list generated with {len(result['shots'])} shots")

            return result

        except Exception as e:
            logger.error(f"Shot list generation failed: {str(e)}")
            raise Exception(f"Shot list agent failed: {str(e)}")
