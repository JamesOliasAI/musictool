"""Input/Output operations and media validation for Keo Shortform Factory."""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from .utils import (
    run_ffprobe_command,
    validate_file_exists,
    get_video_info,
    get_audio_info,
    extract_audio_from_video,
    ensure_dir
)


def validate_inputs(base_path: str, overlay_video_path: str, overlay_audio_path: str) -> Dict[str, Any]:
    """Validate all input files exist and are accessible."""
    base_valid = validate_file_exists(base_path, "base video")
    overlay_video_valid = validate_file_exists(overlay_video_path, "overlay video")
    overlay_audio_valid = validate_file_exists(overlay_audio_path, "overlay audio")

    if not (base_valid and overlay_video_valid and overlay_audio_valid):
        raise ValueError("One or more input files are invalid")

    return {
        "base": base_path,
        "overlay_video": overlay_video_path,
        "overlay_audio": overlay_audio_path
    }


def probe_media(file_path: str) -> Dict[str, Any]:
    """Probe media file for detailed information."""
    if not validate_file_exists(file_path):
        raise ValueError(f"Cannot probe non-existent file: {file_path}")

    # Determine if it's audio or video
    info = get_video_info(file_path)
    if info and info.get("streams"):
        # Check if it has video streams
        has_video = any(stream.get("codec_type") == "video" for stream in info["streams"])
        has_audio = any(stream.get("codec_type") == "audio" for stream in info["streams"])

        if has_video and has_audio:
            # Video file with audio
            video_stream = next(s for s in info["streams"] if s.get("codec_type") == "video")
            audio_stream = next(s for s in info["streams"] if s.get("codec_type") == "audio")

            duration = float(info.get("format", {}).get("duration", 0))
            fps = eval(video_stream.get("r_frame_rate", "0/1"))

            return {
                "type": "video",
                "duration": duration,
                "fps": fps,
                "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                "video_codec": video_stream.get("codec_name", "unknown"),
                "audio_codec": audio_stream.get("codec_name", "unknown"),
                "audio_path": file_path  # For video files, audio is embedded
            }
        elif has_audio:
            # Audio-only file
            audio_stream = next(s for s in info["streams"] if s.get("codec_type") == "audio")
            duration = float(info.get("format", {}).get("duration", 0))

            return {
                "type": "audio",
                "duration": duration,
                "sample_rate": audio_stream.get("sample_rate", 48000),
                "channels": audio_stream.get("channels", 1),
                "audio_codec": audio_stream.get("codec_name", "unknown"),
                "audio_path": file_path
            }

    # Fallback: try to get basic info
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path
    ]

    basic_info = run_ffprobe_command(cmd)
    if basic_info:
        duration = float(basic_info.get("format", {}).get("duration", 0))
        return {
            "type": "unknown",
            "duration": duration,
            "audio_path": file_path
        }

    raise ValueError(f"Could not probe media file: {file_path}")


def extract_audio(base_video_path: str, output_dir: str) -> str:
    """Extract audio from base video for alignment."""
    ensure_dir(output_dir)

    base_name = Path(base_video_path).stem
    audio_path = Path(output_dir) / f"{base_name}_extracted.wav"

    success = extract_audio_from_video(base_video_path, str(audio_path))
    if not success:
        raise RuntimeError(f"Failed to extract audio from {base_video_path}")

    return str(audio_path)


def prepare_overlay_audio(overlay_audio_path: str, output_dir: str, target_lufs: float = -14) -> str:
    """Normalize overlay audio to target LUFS."""
    ensure_dir(output_dir)

    overlay_name = Path(overlay_audio_path).stem
    normalized_path = Path(output_dir) / f"{overlay_name}_normalized.wav"

    success = normalize_audio_loudness(overlay_audio_path, str(normalized_path), target_lufs)
    if not success:
        raise RuntimeError(f"Failed to normalize audio {overlay_audio_path}")

    return str(normalized_path)


def validate_media_compatibility(base_info: Dict[str, Any], overlay_info: Dict[str, Any]) -> None:
    """Validate that media files are compatible for processing."""
    # Check durations
    base_duration = base_info.get("duration", 0)
    overlay_duration = overlay_info.get("duration", 0)

    if base_duration == 0:
        raise ValueError("Base video has no duration")

    if overlay_duration == 0:
        raise ValueError("Overlay audio has no duration")

    # Warn if overlay is much longer than base
    if overlay_duration > base_duration * 1.5:
        print(f"⚠️  Warning: Overlay audio ({overlay_duration:.2f}s) is significantly longer than base video ({base_duration:.2f}s)")

    # Check sample rates for audio alignment
    base_sr = base_info.get("sample_rate", 48000)
    overlay_sr = overlay_info.get("sample_rate", 48000)

    if abs(base_sr - overlay_sr) > 1000:  # Allow small differences
        print(f"⚠️  Warning: Sample rate mismatch - base: {base_sr}Hz, overlay: {overlay_sr}Hz")


def get_optimal_audio_settings() -> Dict[str, Any]:
    """Get optimal audio settings for processing."""
    return {
        "sample_rate": 48000,
        "channels": 1,
        "format": "s16le",
        "target_lufs": -14
    }