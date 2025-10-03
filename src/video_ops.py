"""Video operations for Keo Shortform Factory."""

import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple

from .utils import run_ffmpeg_command, calculate_overlay_position, ensure_dir


def replace_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    config: Dict[str, Any]
) -> bool:
    """Replace audio in video with new audio track."""

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v",  # Take video from first input
        "-map", "1:a",  # Take audio from second input
        "-c:v", "copy",  # Copy video codec
        "-c:a", "aac",   # Re-encode audio as AAC
        "-shortest",     # Match shortest stream
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Replacing audio in {Path(video_path).name}")


def get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """Get video dimensions using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        width, height = map(int, result.stdout.strip().split('x'))
        return width, height
    except Exception as e:
        print(f"❌ Error getting video dimensions: {e}")
        return 1920, 1080  # Fallback to HD


def get_overlay_dimensions(overlay_path: str) -> Tuple[int, int]:
    """Get overlay video dimensions using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        overlay_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        width, height = map(int, result.stdout.strip().split('x'))
        return width, height
    except Exception as e:
        print(f"❌ Error getting overlay dimensions: {e}")
        return 480, 360  # Fallback to small overlay


def composite_overlay(
    base_video_path: str,
    overlay_video_path: str,
    output_path: str,
    config: Dict[str, Any]
) -> bool:
    """Composite overlay video onto base video."""

    # Get dimensions
    base_width, base_height = get_video_dimensions(base_video_path)
    overlay_width, overlay_height = get_overlay_dimensions(overlay_video_path)

    # Get overlay configuration
    overlay_config = config.get("overlay", {})
    position = overlay_config.get("position", "top-right")
    opacity = overlay_config.get("opacity", 0.9)
    margin = overlay_config.get("margin_px", 24)

    # Calculate overlay position
    x_pos, y_pos = calculate_overlay_position(
        base_width, base_height, overlay_width, overlay_height, position, margin
    )

    print(f"🎭 Compositing {overlay_width}x{overlay_height} overlay at ({x_pos}, {y_pos}) with {opacity} opacity")

    # Build FFmpeg filter for overlay composition
    # First, ensure overlay has alpha or create it
    overlay_filter = "[1:v]format=rgba,colorchannelmixer=aa={opacity}[overlay];"

    # Then composite
    overlay_filter += f"[0:v][overlay]overlay={x_pos}:{y_pos}"

    cmd = [
        "ffmpeg", "-y",
        "-i", base_video_path,
        "-i", overlay_video_path,
        "-filter_complex", overlay_filter,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-preset", "veryfast",
        "-crf", "20",
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Compositing overlay onto {Path(base_video_path).name}")


def validate_video_composition(
    base_path: str,
    overlay_path: str,
    output_path: str
) -> bool:
    """Validate that video composition was successful."""

    if not Path(output_path).exists():
        print("❌ Composited video file does not exist")
        return False

    # Check if output has both video and audio streams
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)

        streams = data.get("streams", [])
        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        if not has_video:
            print("❌ Composited video missing video stream")
            return False

        if not has_audio:
            print("❌ Composited video missing audio stream")
            return False

        print("✅ Video composition validation passed")
        return True

    except Exception as e:
        print(f"❌ Error validating video composition: {e}")
        return False


def create_safe_area_overlay(
    width: int,
    height: int,
    margin: int = 24,
    color: str = "black@0.3"
) -> str:
    """Create a safe area overlay filter for platform UI avoidance."""

    # Calculate safe area (common social media safe zones)
    safe_left = margin
    safe_top = margin
    safe_right = width - margin
    safe_bottom = height - margin

    # Create drawbox filter for safe areas
    # Top safe area
    top_box = f"drawbox=x=0:y=0:width={width}:height={safe_top}:color={color}:t=fill"

    # Bottom safe area
    bottom_box = f"drawbox=x=0:y={safe_bottom}:width={width}:height={margin}:color={color}:t=fill"

    return f"{top_box},{bottom_box}"


def apply_safe_area_padding(
    input_path: str,
    output_path: str,
    config: Dict[str, Any]
) -> bool:
    """Apply safe area padding to avoid platform UI elements."""

    overlay_config = config.get("overlay", {})
    margin = overlay_config.get("margin_px", 24)

    # Get video dimensions
    width, height = get_video_dimensions(input_path)

    # Create padding filter
    pad_filter = create_safe_area_overlay(width, height, margin)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", pad_filter,
        "-c:a", "copy",
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Applying safe area padding to {Path(input_path).name}")