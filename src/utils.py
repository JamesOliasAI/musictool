"""Utility functions for Keo Shortform Factory."""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


def run_ffmpeg_command(cmd: list, description: str = "Running FFmpeg") -> bool:
    """Run an FFmpeg command and return success status."""
    try:
        print(f"🎬 {description}...")
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg command failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        return False


def run_ffprobe_command(cmd: list) -> Optional[Dict[str, Any]]:
    """Run an ffprobe command and return JSON output."""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ ffprobe command failed: {e}")
        return None
    except FileNotFoundError:
        print("❌ ffprobe not found. Please install FFmpeg and ensure it's in your PATH.")
        return None
    except json.JSONDecodeError:
        print("❌ Failed to parse ffprobe output as JSON")
        return None


def ensure_dir(dir_path: str) -> Path:
    """Ensure directory exists and return Path object."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def calculate_overlay_position(
    base_width: int,
    base_height: int,
    overlay_width: int,
    overlay_height: int,
    position: str,
    margin: int = 24
) -> Tuple[int, int]:
    """Calculate overlay position coordinates based on position string."""
    if position == "top-left":
        return margin, margin
    elif position == "top-right":
        return base_width - overlay_width - margin, margin
    elif position == "bottom-left":
        return margin, base_height - overlay_height - margin
    elif position == "bottom-right":
        return base_width - overlay_width - margin, base_height - overlay_height - margin
    elif position == "center":
        return (base_width - overlay_width) // 2, (base_height - overlay_height) // 2
    else:
        # Try to parse as "x,y"
        try:
            x, y = map(int, position.split(","))
            return x, y
        except ValueError:
            print(f"⚠️  Invalid position '{position}', using top-right")
            return base_width - overlay_width - margin, margin


def validate_file_exists(file_path: str, file_type: str = "file") -> bool:
    """Validate that a file exists and is readable."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ {file_type.title()} file not found: {file_path}")
        return False

    if not path.is_file():
        print(f"❌ {file_path} is not a file")
        return False

    return True


def get_video_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Get basic video information using ffprobe."""
    if not validate_file_exists(file_path, "video"):
        return None

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]

    return run_ffprobe_command(cmd)


def get_audio_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Get basic audio information using ffprobe."""
    if not validate_file_exists(file_path, "audio"):
        return None

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-select_streams", "a",
        file_path
    ]

    return run_ffprobe_command(cmd)


def extract_audio_from_video(video_path: str, output_path: str) -> bool:
    """Extract audio from video file."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # PCM 16-bit
        "-ar", "48000",  # 48kHz sample rate
        "-ac", "1",  # Mono
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Extracting audio from {video_path}")


def normalize_audio_loudness(input_path: str, output_path: str, target_lufs: float = -14) -> bool:
    """Normalize audio to target LUFS using loudnorm filter."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-ar", "48000",
        "-ac", "1",
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Normalizing {input_path} to {target_lufs} LUFS")