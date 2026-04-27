"""FFmpeg video processing service."""

import subprocess
import tempfile
import os
import re
from typing import Optional
import imageio_ffmpeg
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Get the bundled FFmpeg path
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()


class FFmpegService:
    """Service for video/audio processing using FFmpeg."""

    @staticmethod
    def combine_video_audio(video_bytes: bytes, audio_bytes: bytes) -> bytes:
        """Combine video and audio streams.

        Args:
            video_bytes: Video file bytes
            audio_bytes: Audio file bytes (MP3)

        Returns:
            Combined video bytes

        Raises:
            Exception: If FFmpeg operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            audio_path = os.path.join(tmpdir, "input_audio.mp3")
            output_path = os.path.join(tmpdir, "output_combined.mp4")

            try:
                # Write input files
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)

                # Combine streams
                cmd = [
                    FFMPEG_PATH,
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=120)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg combine failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Combined video and audio: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg combine operation timed out")
            except Exception as e:
                logger.error(f"Combine error: {str(e)}")
                raise

    @staticmethod
    def burn_captions(video_bytes: bytes, captions_srt: str) -> bytes:
        """Burn SRT captions into video.

        Args:
            video_bytes: Video file bytes
            captions_srt: SRT format subtitle content

        Returns:
            Video with burned captions

        Raises:
            Exception: If FFmpeg operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            srt_path = os.path.join(tmpdir, "captions.srt")
            output_path = os.path.join(tmpdir, "output_captions.mp4")

            try:
                # Write files
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(captions_srt)

                # Build filter — modern TikTok/Reels style captions:
                # White text, thin black outline, no background box, bold, centered lower-third
                filter_complex = (
                    f"subtitles={srt_path.replace(chr(92), '/')}"
                    ":force_style='FontName=Arial,FontSize=14,Bold=1,"
                    "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                    "BackColour=&H00000000,BorderStyle=1,Outline=2,"
                    "Shadow=1,ShadowColour=&H80000000,"
                    "Alignment=2,MarginV=40'"
                )

                cmd = [
                    FFMPEG_PATH,
                    "-i", video_path,
                    "-vf", filter_complex,
                    "-c:a", "aac",
                    "-c:v", "libx264",
                    "-crf", "23",
                    "-preset", "fast",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=180)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg caption burn failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Burned captions: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg caption operation timed out")
            except Exception as e:
                logger.error(f"Caption burn error: {str(e)}")
                raise

    @staticmethod
    def add_disclaimer(video_bytes: bytes, text: str) -> bytes:
        """Burn disclaimer text at bottom of video.

        Args:
            video_bytes: Video file bytes
            text: Disclaimer text

        Returns:
            Video with disclaimer

        Raises:
            Exception: If FFmpeg operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            output_path = os.path.join(tmpdir, "output_disclaimer.mp4")

            try:
                with open(video_path, "wb") as f:
                    f.write(video_bytes)

                # Escape special characters for drawtext
                escaped_text = text.replace(":", r"\:").replace("'", "'\\''")

                # Add text at bottom with semi-transparent background
                filter_complex = (
                    f"drawtext=text='{escaped_text}'"
                    ":fontsize=16"
                    ":fontcolor=white"
                    ":x=(w-text_w)/2"
                    ":y=h-60"
                    ":box=1"
                    ":boxcolor=black@0.7"
                    ":boxborderw=5"
                )

                cmd = [
                    FFMPEG_PATH,
                    "-i", video_path,
                    "-vf", filter_complex,
                    "-c:a", "aac",
                    "-c:v", "libx264",
                    "-crf", "23",
                    "-preset", "fast",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=180)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg disclaimer failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Added disclaimer: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg disclaimer operation timed out")
            except Exception as e:
                logger.error(f"Disclaimer error: {str(e)}")
                raise

    @staticmethod
    def create_thumbnail(video_bytes: bytes, timestamp: float = 1.0) -> bytes:
        """Extract frame from video as thumbnail.

        Args:
            video_bytes: Video file bytes
            timestamp: Frame timestamp in seconds

        Returns:
            PNG image bytes

        Raises:
            Exception: If FFmpeg operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            output_path = os.path.join(tmpdir, "thumbnail.png")

            try:
                with open(video_path, "wb") as f:
                    f.write(video_bytes)

                cmd = [
                    FFMPEG_PATH,
                    "-ss", str(timestamp),
                    "-i", video_path,
                    "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
                    "-vframes", "1",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=60)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg thumbnail failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Created thumbnail: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg thumbnail operation timed out")
            except Exception as e:
                logger.error(f"Thumbnail error: {str(e)}")
                raise

    @staticmethod
    def concatenate_videos(video_bytes_list: list) -> bytes:
        """Concatenate multiple video clips into one video.

        Args:
            video_bytes_list: List of video file bytes

        Returns:
            Concatenated video bytes

        Raises:
            Exception: If FFmpeg operation fails
        """
        if not video_bytes_list:
            raise Exception("No videos to concatenate")

        if len(video_bytes_list) == 1:
            return video_bytes_list[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Write all input videos to files
                input_paths = []
                for i, video_bytes in enumerate(video_bytes_list):
                    video_path = os.path.join(tmpdir, f"input_{i}.mp4")
                    with open(video_path, "wb") as f:
                        f.write(video_bytes)
                    input_paths.append(video_path)

                # Create concat demuxer file
                concat_file_path = os.path.join(tmpdir, "concat.txt")
                with open(concat_file_path, "w") as f:
                    for video_path in input_paths:
                        f.write(f"file '{video_path}'\n")

                output_path = os.path.join(tmpdir, "concatenated.mp4")

                # Concatenate videos
                cmd = [
                    FFMPEG_PATH,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file_path,
                    "-c", "copy",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=300)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg concatenation failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Concatenated {len(video_bytes_list)} videos: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg concatenation operation timed out")
            except Exception as e:
                logger.error(f"Concatenation error: {str(e)}")
                raise

    @staticmethod
    def mix_background_music(
        video_bytes: bytes, music_bytes: bytes, music_volume: float = 0.15
    ) -> bytes:
        """Mix background music into video at low volume under existing audio.

        Args:
            video_bytes: Video file bytes (should already have narration audio)
            music_bytes: Background music file bytes (MP3)
            music_volume: Volume level for music (0.0-1.0, default 0.15 = 15%)

        Returns:
            Video with background music mixed in

        Raises:
            Exception: If FFmpeg operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            music_path = os.path.join(tmpdir, "music.wav")
            output_path = os.path.join(tmpdir, "output_music.mp4")

            try:
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
                with open(music_path, "wb") as f:
                    f.write(music_bytes)

                # Get video duration for proper music fade-out
                probe_cmd = [
                    FFMPEG_PATH, "-i", video_path,
                    "-f", "null", "-"
                ]
                probe_result = subprocess.run(
                    probe_cmd, capture_output=True, timeout=30
                )
                # Default fade start if we can't determine duration
                fade_start = 47  # safe default for 50s videos (fade at 47s)

                # Parse duration from ffmpeg stderr
                stderr_text = probe_result.stderr.decode() if probe_result.stderr else ""
                dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr_text)
                if dur_match:
                    h, m, s, _ = dur_match.groups()
                    total_secs = int(h) * 3600 + int(m) * 60 + int(s)
                    fade_start = max(0, total_secs - 3)

                # Mix: keep narration at full volume, loop music at low volume,
                # fade music out over last 3 seconds
                cmd = [
                    FFMPEG_PATH,
                    "-i", video_path,
                    "-stream_loop", "-1",
                    "-i", music_path,
                    "-filter_complex",
                    f"[1:a]volume={music_volume},afade=t=out:st={fade_start}:d=3[bg];"
                    f"[0:a][bg]amix=inputs=2:duration=shortest:dropout_transition=3[aout]",
                    "-map", "0:v:0",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=180)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg music mix failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Mixed background music: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg music mix operation timed out")
            except Exception as e:
                logger.error(f"Music mix error: {str(e)}")
                raise

    @staticmethod
    def add_audio_track(video_bytes: bytes, audio_bytes: bytes, volume: float = 0.45) -> bytes:
        """Add an audio track to a video that has no existing audio.

        Used when narration is disabled but background music is enabled.

        Args:
            video_bytes: Video file bytes (no audio track)
            audio_bytes: Audio file bytes (WAV/MP3)
            volume: Volume level (0.0-1.0)

        Returns:
            Video with audio track

        Raises:
            Exception: If FFmpeg operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            audio_path = os.path.join(tmpdir, "music.wav")
            output_path = os.path.join(tmpdir, "output_with_audio.mp4")

            try:
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)

                # Get video duration for fade
                probe_cmd = [FFMPEG_PATH, "-i", video_path, "-f", "null", "-"]
                probe_result = subprocess.run(probe_cmd, capture_output=True, timeout=30)
                fade_start = 47
                stderr_text = probe_result.stderr.decode() if probe_result.stderr else ""
                dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr_text)
                if dur_match:
                    h, m, s, _ = dur_match.groups()
                    total_secs = int(h) * 3600 + int(m) * 60 + int(s)
                    fade_start = max(0, total_secs - 3)

                cmd = [
                    FFMPEG_PATH,
                    "-i", video_path,
                    "-stream_loop", "-1",
                    "-i", audio_path,
                    "-filter_complex",
                    f"[1:a]volume={volume},afade=t=out:st={fade_start}:d=3[aout]",
                    "-map", "0:v:0",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=180)
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"FFmpeg add audio failed: {error}")

                with open(output_path, "rb") as f:
                    output_bytes = f.read()

                logger.info(f"Added audio track to video: {len(output_bytes)} bytes")
                return output_bytes

            except subprocess.TimeoutExpired:
                raise Exception("FFmpeg add audio operation timed out")
            except Exception as e:
                logger.error(f"Add audio error: {str(e)}")
                raise

    @staticmethod
    def get_video_duration(video_bytes: bytes) -> float:
        """Get duration of video in seconds.

        Args:
            video_bytes: Video file bytes

        Returns:
            Duration in seconds

        Raises:
            Exception: If operation fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")

            try:
                with open(video_path, "wb") as f:
                    f.write(video_bytes)

                cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1:csv_list=s",
                    video_path,
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=10)
                if result.returncode != 0:
                    raise Exception("ffprobe failed")

                duration_str = result.stdout.decode().strip()
                duration = float(duration_str)

                logger.info(f"Video duration: {duration} seconds")
                return duration

            except (subprocess.TimeoutExpired, ValueError) as e:
                logger.error(f"Duration check error: {str(e)}")
                raise Exception(f"Failed to get video duration: {str(e)}")
