"""Video cutting and slicing functionality for Keo Shortform Factory."""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from .utils import run_ffmpeg_command, ensure_dir


def slice_video(
    video_path: str,
    output_dir: str,
    config: Dict[str, Any]
) -> List[str]:
    """Slice video into fixed-length clips based on configuration."""

    # Get slicing configuration
    slicing_config = config.get("slicing", {})
    clip_len = slicing_config.get("clip_len", 20)
    stride = slicing_config.get("stride", 18)

    # Get video duration
    duration = get_video_duration(video_path)
    if duration == 0:
        raise ValueError(f"Could not determine duration of {video_path}")

    print(f"🎬 Slicing {duration:.2f}s video into {clip_len}s clips with {stride}s stride")

    # Generate clip start times
    start_times = generate_clip_starts(duration, clip_len, stride)

    if not start_times:
        print("⚠️  No clips to generate")
        return []

    print(f"📋 Will generate {len(start_times)} clips")

    # Create clips
    output_paths = []
    for i, start_time in enumerate(start_times):
        output_path = create_clip(
            video_path,
            output_dir,
            start_time,
            clip_len,
            i
        )
        if output_path:
            output_paths.append(output_path)

    print(f"✅ Generated {len(output_paths)} clips")
    return output_paths


def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"❌ Error getting video duration: {e}")
        return 0.0


def generate_clip_starts(duration: float, clip_len: float, stride: float) -> List[float]:
    """Generate start times for clips based on duration and stride."""

    if duration < clip_len:
        print(f"⚠️  Video duration ({duration:.2f}s) is shorter than clip length ({clip_len}s)")
        return []

    # Generate start times
    start_times = []
    current_time = 0.0

    while current_time + clip_len <= duration:
        start_times.append(current_time)
        current_time += stride

        # Ensure we don't go beyond video duration
        if current_time + clip_len > duration and current_time < duration:
            # Add a final clip from current position if there's enough remaining
            remaining = duration - current_time
            if remaining >= clip_len * 0.5:  # At least half the desired length
                start_times.append(current_time)
            break

    return start_times


def create_clip(
    video_path: str,
    output_dir: str,
    start_time: float,
    duration: float,
    clip_index: int
) -> str:
    """Create a single clip from video."""

    ensure_dir(output_dir)

    # Format start time for filename
    start_str = f"{int(start_time):06d}"
    end_time = start_time + duration
    end_str = f"{int(end_time):06d}"

    # Create output filename
    base_name = Path(video_path).stem
    output_filename = f"clip_{start_str}_{end_str}.mp4"
    output_path = Path(output_dir) / output_filename

    # FFmpeg command for cutting
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",  # Copy streams for speed
        "-avoid_negative_ts", "make_zero",
        str(output_path)
    ]

    success = run_ffmpeg_command(
        cmd,
        f"Creating clip {clip_index + 1}: {start_time:.2f}s to {end_time:.2f}s"
    )

    if success:
        return str(output_path)
    else:
        print(f"❌ Failed to create clip {clip_index + 1}")
        return ""


def validate_clip(
    clip_path: str,
    expected_duration: float,
    tolerance: float = 0.1
) -> bool:
    """Validate that a clip was created correctly."""

    if not Path(clip_path).exists():
        print(f"❌ Clip file does not exist: {clip_path}")
        return False

    # Check actual duration
    actual_duration = get_video_duration(clip_path)

    if abs(actual_duration - expected_duration) > tolerance:
        print(f"❌ Clip duration mismatch: expected {expected_duration:.2f}s, got {actual_duration:.2f}s")
        return False

    # Check file size (should be > 0)
    file_size = Path(clip_path).stat().st_size
    if file_size == 0:
        print(f"❌ Clip file is empty: {clip_path}")
        return False

    return True


def cleanup_failed_clips(output_dir: str) -> None:
    """Clean up any incomplete or failed clip files."""

    output_path = Path(output_dir)

    if not output_path.exists():
        return

    # Look for incomplete/empty clip files
    for clip_file in output_path.glob("clip_*.mp4"):
        file_size = clip_file.stat().st_size

        # Remove very small files (likely failed)
        if file_size < 1024:  # Less than 1KB
            print(f"🗑️  Removing incomplete clip: {clip_file.name}")
            try:
                clip_file.unlink()
            except Exception as e:
                print(f"❌ Error removing {clip_file}: {e}")


def get_clip_info(clip_path: str) -> Dict[str, Any]:
    """Get detailed information about a clip."""

    duration = get_video_duration(clip_path)

    if duration == 0:
        return {"error": "Could not determine clip duration"}

    # Get more detailed info using ffprobe
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        clip_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)

        # Extract basic info
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

        return {
            "duration": duration,
            "file_size": format_info.get("size", 0),
            "bitrate": format_info.get("bit_rate", 0),
            "video_codec": video_stream.get("codec_name", "unknown"),
            "audio_codec": audio_stream.get("codec_name", "unknown"),
            "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}"
        }

    except Exception as e:
        return {
            "duration": duration,
            "error": f"Could not get detailed info: {e}"
        }