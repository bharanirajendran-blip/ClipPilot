"""Shot list agent for generating visual prompts."""

from app.agents.base import BaseAgent
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class ShotListAgent(BaseAgent):
    """Agent that creates shot-by-shot visual prompts for video generation."""

    CINEMATIC_PROMPT = """You are an expert cinematographer writing prompts for AI video generation.

Your prompts will be sent DIRECTLY to an AI video API to generate real video clips. It works best with:
- REAL-WORLD scenes featuring REAL subjects (people, animals, objects, landscapes)
- Specific physical descriptions: "a woman with curly brown hair in a blue lab coat" NOT "a scientist"
- Concrete environments: "a sunlit greenhouse with rows of tomato plants" NOT "a nature setting"
- Camera motion: "slow dolly forward", "steady tracking shot left to right", "gentle push-in zoom"
- Lighting: "warm golden hour sunlight", "soft diffused overhead lighting", "dramatic side-lit"
- NO text, charts, diagrams, UI elements, or abstract concepts — the AI cannot generate these
- NO narration or dialogue text in the prompt — only visual descriptions
- Keep each prompt under 500 characters for best results

CRITICAL RULES:
1. Every prompt must describe something a real camera could film
2. Describe ONE continuous shot per prompt (no cuts or transitions)
3. Include exactly ONE clear subject doing ONE action
4. Specify the environment/background explicitly
5. Include at least one type of motion (camera or subject movement)
6. Use photographic language: depth of field, lens type, exposure feel

VISUAL CONTINUITY — make the shot list feel like one coherent video:
- Keep a consistent color mood across the whole video
- Avoid random unrelated people or locations between scenes
- Use one recurring object, place, or subject when the topic allows
- Do not include readable text, signs, documents, charts, maps, labels, interfaces, or floating words
- If the script mentions an abstract concept, convert it into a physical scene or metaphor
- Prefer close-up actions and medium shots over generic wide stock footage

GOOD example: "Close-up of honey dripping slowly from a wooden dipper into a glass jar, warm amber backlight, shallow depth of field, kitchen counter with herbs in background, slow motion, cinematic"
BAD example: "Show the concept of sweetness and natural food production processes"

Return your shot list as JSON with this structure:
{
    "shots": [
        {
            "scene_number": 1,
            "prompt": "Visual prompt describing a real filmable scene...",
            "style_descriptors": ["cinematic", "warm lighting", "shallow DOF"],
            "camera_direction": "Close-up, slow push-in"
        }
    ]
}"""

    ANIMATED_PROMPT = """You are an expert animation director writing prompts for AI video generation in ANIMATED style.

Your prompts will generate colorful, engaging ANIMATED video clips (like Pixar, educational animations, or motion graphics). The AI supports cartoon and animated styles when prompted correctly.

ANIMATED STYLE RULES:
- Every prompt MUST start with "In colorful 3D animated style:" or "In vibrant cartoon animation style:"
- Use bright, saturated colors and clean shapes
- Characters should be stylized and expressive (big eyes, exaggerated features, friendly)
- Environments should be colorful, simplified, and inviting
- Great for abstract concepts: show equations as floating glowing objects, ideas as characters, processes as visual metaphors
- Motion should be playful: bouncing, floating, spinning, morphing
- NO photorealistic descriptions — everything should feel animated and fun
- Keep each prompt under 500 characters

CRITICAL RULES for animated:
1. ALWAYS prefix with animation style instruction
2. Make abstract concepts VISUAL — numbers can float, letters can dance, concepts become characters
3. Use bright backgrounds: colorful gradients, starry skies, cheerful classrooms
4. Include expressive motion: bouncing, growing, shrinking, transforming
5. One scene per prompt, one clear visual idea
6. Avoid readable text unless absolutely necessary. If showing numbers, letters, or equations, describe them as simple symbolic shapes rather than exact readable text. Prefer animated objects, characters, glowing paths, particles, and transformations over written explanations.
7. Keep shots visually connected — reuse the same character or setting across scenes when possible

GOOD example: "In colorful 3D animated style: a friendly cartoon robot with big blue eyes points at a glowing equation 'x + 3 = 7' floating in the air, the number 3 bounces away and a sparkling 4 slides into place next to x, bright teal classroom background with floating stars"
BAD example: "Show an algebra equation being solved on a whiteboard"

Return your shot list as JSON with this structure:
{
    "shots": [
        {
            "scene_number": 1,
            "prompt": "In colorful 3D animated style: description of animated scene...",
            "style_descriptors": ["3D animated", "colorful", "cartoon"],
            "camera_direction": "Medium shot, gentle zoom in"
        }
    ]
}"""

    def __init__(self, style: str = "educational"):
        """Initialize shot list agent.

        Args:
            style: Video style — uses animated prompt for 'animated', cinematic for all others
        """
        system_prompt = self.ANIMATED_PROMPT if style == "animated" else self.CINEMATIC_PROMPT
        self.style = style
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

Before returning JSON, check that the shots do not feel like unrelated stock clips. The viewer should feel they are watching one coherent short video.

Return as JSON with "shots" array containing scene_number, prompt, style_descriptors, and camera_direction for each scene."""

            result = self.call_json(user_message, max_tokens=3000)

            if "shots" in result:
                logger.info(f"Shot list generated with {len(result['shots'])} shots")

            return result

        except Exception as e:
            logger.error(f"Shot list generation failed: {str(e)}")
            raise Exception(f"Shot list agent failed: {str(e)}")
