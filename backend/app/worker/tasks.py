"""ARQ tasks for video generation pipeline."""

import json
import httpx
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from app.config import settings
from app.utils.logger import get_logger
from app.agents.research_agent import ResearchAgent
from app.agents.script_agent import ScriptAgent
from app.agents.shot_list_agent import ShotListAgent
from app.agents.review_agent import ReviewAgent
from app.agents.metadata_agent import MetadataAgent
from app.services.guardrails import check_output_safety

from app.services.elevenlabs_service import ElevenLabsService
from app.services.deepgram_service import DeepgramService
from app.services.ffmpeg_service import FFmpegService
from app.services.storage_service import StorageService
from app.services.vision_validator import (
    extract_frame_from_video,
    validate_video_frame,
    ValidationResult,
)
from app.mcp.client import mcp_client
from app.utils.srt import words_to_srt
from supabase import create_client

logger = get_logger(__name__)


class JobCancelledError(Exception):
    """Raised when a job has been cancelled by the user."""
    pass


async def process_video_job(ctx: Any, job_id: str) -> dict:
    """Process a video generation job - main orchestration task.

    Args:
        ctx: ARQ context
        job_id: Job ID to process

    Returns:
        Result dict with status and URLs

    Raises:
        Exception: If processing fails
    """
    try:
        import time as _time
        job_start_time = _time.time()
        metrics = {}  # Track per-step timing and costs

        # Initialize MCP client and services
        mcp_client.initialize()
        logger.info(f"MCP tools available: {[t['name'] for t in mcp_client.list_tools()]}")

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        storage_service = StorageService(supabase)

        # Get job details
        job_response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        job = job_response.data

        if not job:
            raise Exception(f"Job not found: {job_id}")

        # Check if job was already cancelled before we start
        if job["status"] == "failed":
            logger.info(f"Job {job_id} already failed/cancelled, skipping")
            return {"status": "cancelled", "message": "Job was cancelled before processing started"}

        topic = job["topic"]
        style = job["style"]
        duration = job["duration"]
        user_id = job["user_id"]
        include_narration = job.get("include_narration", True)
        include_captions = job.get("include_captions", True)
        include_music = job.get("include_music", True)
        custom_music_url = job.get("music_url")

        logger.info(f"Starting job processing: {job_id} for user {user_id}")

        # Step 1: Research
        await _update_job_step(supabase, job_id, "Researching topic", 10)
        step_start = _time.time()
        research_agent = ResearchAgent()
        research = research_agent.research(topic)
        metrics["research_seconds"] = round(_time.time() - step_start, 1)
        logger.info(f"Research completed for {job_id} in {metrics['research_seconds']}s")

        # Save research data to job record
        try:
            supabase.table("jobs").update({
                "research_data": research
            }).eq("id", job_id).execute()
        except Exception as e:
            logger.warning(f"Failed to save research data: {str(e)}")

        # Step 2: Script generation
        await _update_job_step(supabase, job_id, "Generating script", 25)
        step_start = _time.time()
        script_agent = ScriptAgent()
        script = script_agent.generate_script(topic, style, duration, research)
        metrics["script_seconds"] = round(_time.time() - step_start, 1)
        logger.info(f"Script generated for {job_id} in {metrics['script_seconds']}s")

        # Step 3: Review (with up to 2 revision loops)
        review_agent = ReviewAgent()
        shot_list_agent = ShotListAgent(style=style)
        revision_count = 0
        max_revisions = 2

        while revision_count < max_revisions:
            await _update_job_step(supabase, job_id, "Reviewing content", 35 + (revision_count * 5))

            # Generate shot list first
            shot_list = shot_list_agent.generate_shot_list(script)

            # Review
            review = review_agent.review(topic, script, shot_list)

            if review.get("approved", False):
                logger.info(f"Script approved for {job_id}")
                break

            if review.get("revision_needed", False) and revision_count < max_revisions - 1:
                revision_details = review.get("revision_details", "")
                issues = review.get("issues", [])
                suggestions = review.get("suggestions", [])

                # Build comprehensive feedback for the script agent
                feedback_parts = []
                if revision_details:
                    feedback_parts.append(f"Reviewer notes: {revision_details}")
                if issues:
                    feedback_parts.append("Issues found:\n" + "\n".join(f"- {i}" for i in issues))
                if suggestions:
                    feedback_parts.append("Suggestions:\n" + "\n".join(f"- {s}" for s in suggestions))

                full_feedback = "\n\n".join(feedback_parts)
                logger.info(f"Revising script for {job_id}: {full_feedback[:300]}")

                # Regenerate script WITH the review feedback
                script = script_agent.generate_script(
                    topic, style, duration, research,
                    revision_feedback=full_feedback,
                )
                revision_count += 1
            else:
                # If not approved after max revisions, log warning but continue
                logger.warning(f"Script not fully approved for {job_id}, proceeding anyway")
                break

        # Always save script and shot_list data (even if review didn't approve)
        try:
            supabase.table("jobs").update({
                "script_data": script,
                "shot_list_data": shot_list,
                "research_data": research,
            }).eq("id", job_id).execute()
        except Exception as e:
            logger.warning(f"Failed to save agent data: {str(e)}")

        # Step 4: Output safety check (hard/soft tiers)
        await _update_job_step(supabase, job_id, "Safety check", 50)
        script_text = _extract_script_text(script)
        safety_result = check_output_safety(script_text)

        if not safety_result.is_safe:
            await _fail_job(supabase, job_id, f"Output safety check failed: {safety_result.reason}")
            return {"status": "failed", "error": "Content failed safety check"}

        # Log soft warnings but continue
        if safety_result.warnings:
            metrics["safety_warnings"] = safety_result.warnings
            logger.warning(f"Output safety soft warnings for {job_id}: {safety_result.warnings}")

        # Step 5: Generate video clips via MCP tools/call → Runway
        # Uses tiered retry logic: each scene retries up to 3 times with
        # adjusted prompts. Vision validation inspects frames between retries.
        await _update_job_step(supabase, job_id, "Generating video", 60)
        video_clip_bytes_list = []
        vision_warnings = []  # Collect soft warnings across all scenes
        max_scene_retries = 3

        # Build a lookup of shot_list prompts by scene_number for Runway-optimized prompts
        shot_prompts = {}
        for shot in shot_list.get("shots", []):
            sn = shot.get("scene_number")
            if sn is not None:
                shot_prompts[sn] = shot

        scenes = script.get("scenes", [])
        for i, scene in enumerate(scenes):
            progress = 60 + (i * 10 / len(scenes))
            await _update_job_step(supabase, job_id, f"Generating scene {i+1}/{len(scenes)}", int(progress))

            scene_num = scene.get("scene_number", i + 1)
            shot = shot_prompts.get(scene_num, {})

            # Prefer the shot_list_agent's Runway-optimized prompt over raw visual_description
            runway_prompt = shot.get("prompt", "")
            if not runway_prompt:
                runway_prompt = scene.get("visual_description", "")

            # Append style descriptors from shot list if available
            style_tags = shot.get("style_descriptors", [])
            camera_dir = shot.get("camera_direction", "")
            style_suffix = ", ".join(style_tags) if style_tags else "cinematic, vibrant colors"
            camera_suffix = f", {camera_dir}" if camera_dir else ""

            if style == "animated":
                base_prompt = (
                    f"{runway_prompt}. "
                    f"{style_suffix}, colorful 3D animation, smooth motion, "
                    f"vibrant cartoon style{camera_suffix}, vertical format 9:16 aspect ratio"
                )
            else:
                base_prompt = (
                    f"{runway_prompt}. "
                    f"{style_suffix}, photorealistic 4K quality, professional lighting, "
                    f"smooth cinematic motion{camera_suffix}, vertical format 9:16 aspect ratio"
                )

            # Tiered retry loop per scene
            scene_success = False
            current_prompt = base_prompt
            _last_scene_error = ""
            for attempt in range(max_scene_retries):
                try:
                    logger.info(
                        f"MCP tools/call runway_generate_video scene {scene_num} "
                        f"(attempt {attempt+1}/{max_scene_retries}): {current_prompt[:200]}..."
                    )
                    video_bytes = mcp_client.generate_video(
                        current_prompt, duration=scene.get("duration_seconds", 10)
                    )

                    # Vision validation: extract a frame and inspect it
                    frame_png = extract_frame_from_video(video_bytes, timestamp=2.0)
                    if frame_png:
                        vr = validate_video_frame(frame_png, current_prompt, scene_num)
                        metrics[f"scene_{scene_num}_quality"] = vr.quality_score

                        if not vr.passed and vr.severity == "hard":
                            # Hard failure — retry with adjusted prompt
                            logger.warning(
                                f"Scene {scene_num} HARD validation failure (attempt {attempt+1}): "
                                f"{vr.issues}"
                            )
                            if vr.retry_hint and attempt < max_scene_retries - 1:
                                current_prompt = (
                                    f"{base_prompt}. "
                                    f"IMPORTANT: {vr.retry_hint}. "
                                    f"Avoid: {', '.join(vr.issues[:2])}"
                                )
                                continue  # Retry with adjusted prompt
                            else:
                                # Last attempt failed — skip this scene
                                logger.warning(f"Scene {scene_num} failed all validation attempts")
                                break

                        if vr.severity == "soft" and vr.issues:
                            vision_warnings.extend(
                                [f"Scene {scene_num}: {w}" for w in vr.issues]
                            )
                            logger.info(f"Scene {scene_num} soft warnings: {vr.issues}")

                    # Passed validation (or no frame to validate)
                    video_clip_bytes_list.append(video_bytes)
                    scene_success = True
                    break

                except Exception as e:
                    error_str = str(e).lower()
                    _last_scene_error = error_str
                    logger.warning(
                        f"Scene {i+1} generation failed (attempt {attempt+1}): {str(e)}"
                    )

                    # Non-retryable errors — fail fast instead of burning retries
                    non_retryable = ["credits", "billing", "unauthorized", "forbidden", "quota"]
                    if any(keyword in error_str for keyword in non_retryable):
                        logger.error(f"Non-retryable error for scene {scene_num}, skipping remaining retries")
                        break

                    if attempt < max_scene_retries - 1:
                        # Simplify prompt on retry — sometimes shorter prompts work better
                        current_prompt = (
                            f"{runway_prompt}. "
                            f"cinematic, photorealistic, professional lighting, vertical 9:16"
                        )
                    # Continue to next retry

            if not scene_success:
                logger.warning(f"Scene {scene_num} failed after {max_scene_retries} attempts, skipping")

                # If it's a billing/credits error, stop trying all remaining scenes
                if any(k in _last_scene_error for k in ["credits", "billing", "quota"]):
                    logger.error("Account-level error detected, skipping remaining scenes")
                    break

        if not video_clip_bytes_list:
            await _fail_job(supabase, job_id, "Failed to generate any video clips")
            return {"status": "failed", "error": "Video generation failed"}

        # Fail if fewer than half the expected scenes succeeded
        expected_scenes = len(scenes)
        actual_scenes = len(video_clip_bytes_list)
        if actual_scenes < expected_scenes / 2:
            await _fail_job(
                supabase, job_id,
                f"Too many scenes failed: only {actual_scenes}/{expected_scenes} generated. Please try again."
            )
            return {"status": "failed", "error": f"Only {actual_scenes}/{expected_scenes} scenes generated"}

        # Log vision warnings summary
        if vision_warnings:
            metrics["vision_warnings"] = vision_warnings[:10]  # Cap at 10 for storage
            logger.info(f"Vision validation warnings: {vision_warnings}")

        # Concatenate all video clips
        ffmpeg_service = FFmpegService()
        try:
            combined_video = ffmpeg_service.concatenate_videos(video_clip_bytes_list)
            logger.info(f"Concatenated {len(video_clip_bytes_list)} video clips for {job_id}")
        except Exception as e:
            logger.warning(f"Video concatenation failed: {str(e)}, using first clip only")
            combined_video = video_clip_bytes_list[0]

        # Step 6: Generate narration (skip if user disabled narration)
        audio_bytes = None
        narration_text = _extract_narration_text(script)

        if include_narration:
            await _update_job_step(supabase, job_id, "Generating narration", 75)
            audio_bytes = _generate_tts_audio(narration_text, job_id)
        else:
            logger.info(f"Narration disabled for {job_id}, skipping TTS")

        # Step 7: Transcribe audio for captions via MCP tools/call → Deepgram
        captions_srt = ""
        if audio_bytes and include_captions:
            await _update_job_step(supabase, job_id, "Generating captions", 80)

            try:
                words = mcp_client.transcribe(audio_bytes)
                captions_srt = words_to_srt(words, narration_text)
            except Exception as e:
                logger.warning(f"MCP transcription failed: {str(e)}, continuing without captions")
        elif not include_captions:
            logger.info(f"Captions disabled for {job_id}, skipping transcription")

        # Step 8: Assemble video with FFmpeg
        await _update_job_step(supabase, job_id, "Assembling video", 85)

        final_video = combined_video

        # Combine with narration audio if available
        if audio_bytes:
            try:
                final_video = ffmpeg_service.combine_video_audio(final_video, audio_bytes)
            except Exception as e:
                logger.warning(f"Audio combination failed: {str(e)}, using video only")

        # Burn captions if available and enabled
        if captions_srt and include_captions:
            try:
                final_video = ffmpeg_service.burn_captions(final_video, captions_srt)
            except Exception as e:
                logger.warning(f"Caption burn failed: {str(e)}")

        # Add disclaimer
        disclaimer_text = "Generated by ClipPilot based on user input. Verify claims independently."
        try:
            final_video = ffmpeg_service.add_disclaimer(final_video, disclaimer_text)
        except Exception as e:
            logger.warning(f"Disclaimer burn failed: {str(e)}")

        # Add background music if enabled
        if include_music:
            await _update_job_step(supabase, job_id, "Adding background music", 87)
            try:
                music_bytes = None

                # Use custom music if user uploaded one
                if custom_music_url:
                    parsed = urlparse(custom_music_url)
                    supabase_host = urlparse(settings.SUPABASE_URL).hostname
                    trusted_path = "/storage/v1/object/public/audio/"

                    if parsed.hostname == supabase_host and parsed.path.startswith(trusted_path):
                        logger.info(f"Downloading custom music for {job_id}")
                        with httpx.Client(timeout=60.0) as client:
                            resp = client.get(custom_music_url)
                            resp.raise_for_status()
                            music_bytes = resp.content
                        logger.info(f"Custom music downloaded: {len(music_bytes)} bytes")
                    else:
                        logger.warning(f"Invalid music URL for {job_id}, falling back to generated")

                # Fall back to generated ambient music
                if not music_bytes:
                    from app.services.music_service import get_background_music_sync
                    music_bytes = get_background_music_sync(style=style, duration=duration)

                if audio_bytes:
                    # Video has narration — mix music underneath at low volume
                    final_video = ffmpeg_service.mix_background_music(
                        final_video, music_bytes, music_volume=0.15
                    )
                else:
                    # No narration — music is the star, play louder
                    final_video = ffmpeg_service.add_audio_track(
                        final_video, music_bytes, volume=0.50
                    )
                logger.info(f"Added background music for {job_id}")
            except Exception as e:
                logger.warning(f"Background music failed: {str(e)}, continuing without")

        # Create thumbnail
        try:
            thumbnail_bytes = ffmpeg_service.create_thumbnail(final_video, timestamp=1.0)
        except Exception as e:
            logger.warning(f"Thumbnail creation failed: {str(e)}")
            thumbnail_bytes = None

        # Step 9: Upload to storage
        await _update_job_step(supabase, job_id, "Uploading files", 90)
        try:
            video_url = storage_service.upload_video(job_id, final_video)
        except Exception as e:
            await _fail_job(supabase, job_id, f"Video upload failed: {str(e)}")
            return {"status": "failed", "error": "Upload failed"}

        thumbnail_url = None
        if thumbnail_bytes:
            try:
                thumbnail_url = storage_service.upload_thumbnail(job_id, thumbnail_bytes)
            except Exception as e:
                logger.warning(f"Thumbnail upload failed: {str(e)}")

        # Step 10: Generate metadata
        await _update_job_step(supabase, job_id, "Generating metadata", 95)
        metadata_agent = MetadataAgent()
        metadata = metadata_agent.generate_metadata(topic, script)

        # Step 11: Update job with results + evaluation metrics
        await _update_job_step(supabase, job_id, "Finalizing", 99)

        # Calculate total time and cost estimates
        total_seconds = round(_time.time() - job_start_time, 1)
        metrics["total_seconds"] = total_seconds
        metrics["scenes_generated"] = len(video_clip_bytes_list)
        metrics["scenes_total"] = len(scenes)

        # Cost estimates (approximate per-API pricing)
        num_scenes = len(video_clip_bytes_list)
        metrics["cost_estimate"] = {
            "claude_agents": round(0.005 * 5, 3),       # ~$0.005 per Haiku call × 5 agents
            "runway_video": round(0.05 * num_scenes, 2), # ~$0.05 per 10s clip
            "elevenlabs_tts": 0.01,                       # ~$0.01 per narration
            "deepgram_stt": 0.005,                        # ~$0.005 per transcription
            "total": round(0.005 * 5 + 0.05 * num_scenes + 0.01 + 0.005, 3),
        }

        logger.info(f"Job metrics: {json.dumps(metrics)}")

        result_data = {
            "status": "completed",
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "title": metadata.get("title", "Untitled"),
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "completed_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
        }

        result_data["current_step"] = "Complete"
        result_data["progress"] = 100
        supabase.table("jobs").update(result_data).eq("id", job_id).execute()

        logger.info(f"Job completed successfully: {job_id} in {total_seconds}s")
        return {
            "status": "completed",
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
        }

    except JobCancelledError:
        logger.info(f"Job {job_id} cancelled — pipeline stopped cleanly")
        return {"status": "cancelled", "message": "Job cancelled by user"}

    except Exception as e:
        logger.error(f"Job processing failed: {str(e)}")
        await _fail_job(supabase, job_id, str(e))
        return {"status": "failed", "error": str(e)}


async def _update_job_step(supabase: Any, job_id: str, step: str, progress: int) -> None:
    """Update job progress and current step.

    Checks if the job was cancelled before updating. If the job status
    is 'failed' (set by the cancel endpoint), raises JobCancelledError
    to stop the pipeline immediately.

    Args:
        supabase: Supabase client
        job_id: Job ID
        step: Current step description
        progress: Progress percentage (0-100)

    Raises:
        JobCancelledError: If the job has been cancelled by the user
    """
    try:
        # Check current status before overwriting
        current = supabase.table("jobs").select("status, error_message").eq("id", job_id).single().execute()
        if current.data and current.data["status"] == "failed":
            logger.info(f"Job {job_id} was cancelled, stopping pipeline")
            raise JobCancelledError(f"Job {job_id} cancelled by user")

        supabase.table("jobs").update({
            "status": "processing",
            "current_step": step,
            "progress": progress,
        }).eq("id", job_id).execute()
        logger.info(f"Job {job_id}: {step} ({progress}%)")
    except JobCancelledError:
        raise  # Re-raise cancellation — don't swallow it
    except Exception as e:
        logger.error(f"Failed to update job step: {str(e)}")


async def _fail_job(supabase: Any, job_id: str, error_message: str) -> None:
    """Mark job as failed with error message.

    Args:
        supabase: Supabase client
        job_id: Job ID
        error_message: Error message
    """
    try:
        supabase.table("jobs").update({
            "status": "failed",
            "error_message": error_message,
        }).eq("id", job_id).execute()
        logger.error(f"Job marked failed: {job_id} - {error_message}")
    except Exception as e:
        logger.error(f"Failed to update job failure: {str(e)}")


def _extract_script_text(script: dict) -> str:
    """Extract all narration text from script.

    Args:
        script: Script dict

    Returns:
        Combined narration text
    """
    scenes = script.get("scenes", [])
    text_parts = [scene.get("narration", "") for scene in scenes]
    return " ".join(text_parts)


def _extract_narration_text(script: dict) -> str:
    """Extract narration for TTS.

    Args:
        script: Script dict

    Returns:
        Full narration text
    """
    return _extract_script_text(script)


def _generate_tts_audio(narration_text: str, job_id: str) -> bytes | None:
    """Generate narration audio via MCP tools/call → ElevenLabs.

    Args:
        narration_text: Narration text to synthesize
        job_id: Job ID for logging

    Returns:
        Audio bytes if generation succeeds, otherwise None
    """
    try:
        audio_bytes = mcp_client.text_to_speech(narration_text)
        logger.info(f"MCP tools/call elevenlabs_text_to_speech for {job_id}: {len(audio_bytes)} bytes")
        return audio_bytes
    except Exception as e:
        logger.warning(f"MCP TTS failed: {str(e)}, continuing without audio")
        return None
