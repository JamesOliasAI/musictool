"""Video export functionality for Keo Shortform Factory."""

import subprocess
from pathlib import Path
from typing import Dict, Any, List

from .utils import run_ffmpeg_command, ensure_dir


def export_clips(
    clip_path: str,
    output_dir: str,
    config: Dict[str, Any]
) -> str:
    """Export a clip in the specified aspect ratio."""

    # Get export configuration
    export_config = config.get("export", {})
    target_ratio = export_config.get("ratio", "9:16")

    # Parse ratio
    try:
        width, height = map(int, target_ratio.split(":"))
    except ValueError:
        print(f"❌ Invalid ratio format: {target_ratio}, using 9:16")
        width, height = 9, 16

    # Get quality settings
    quality_ladder = export_config.get("quality_ladder", [
        {"codec": "libx264", "crf": 20, "preset": "veryfast"}
    ])

    # Use first quality setting for now (could be extended for multiple qualities)
    quality_settings = quality_ladder[0] if quality_ladder else {
        "codec": "libx264", "crf": 20, "preset": "veryfast"
    }

    # Create output path
    ensure_dir(output_dir)
    clip_name = Path(clip_path).stem
    output_path = Path(output_dir) / f"{clip_name}_{target_ratio.replace(':', 'x')}.mp4"

    # Export with aspect ratio conversion
    success = export_single_clip(
        clip_path,
        str(output_path),
        width,
        height,
        quality_settings
    )

    if success:
        return str(output_path)
    else:
        print(f"❌ Failed to export {clip_path}")
        return ""


def export_single_clip(
    input_path: str,
    output_path: str,
    target_width: int,
    target_height: int,
    quality_settings: Dict[str, Any]
) -> bool:
    """Export a single clip with aspect ratio conversion."""

    # Get input video dimensions
    input_width, input_height = get_video_dimensions(input_path)

    # Calculate scaling and cropping for target aspect ratio
    scale_filter = build_scale_filter(
        input_width, input_height,
        target_width, target_height
    )

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", scale_filter,
        "-c:v", quality_settings.get("codec", "libx264"),
        "-c:a", "aac",
        "-preset", quality_settings.get("preset", "veryfast"),
        "-crf", str(quality_settings.get("crf", 20)),
    ]

    # Add codec-specific options
    if quality_settings.get("codec") == "prores_ks":
        cmd.extend([
            "-profile:v", str(quality_settings.get("profile", 3))
        ])

    cmd.append(output_path)

    return run_ffmpeg_command(
        cmd,
        f"Exporting {Path(input_path).name} to {target_width}:{target_height}"
    )


def get_video_dimensions(video_path: str) -> tuple:
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
        return 1920, 1080  # Fallback


def build_scale_filter(
    input_width: int,
    input_height: int,
    target_width: int,
    target_height: int
) -> str:
    """Build FFmpeg scale filter for aspect ratio conversion."""

    # Calculate target aspect ratio
    target_aspect = target_width / target_height
    input_aspect = input_width / input_height

    if abs(input_aspect - target_aspect) < 0.01:
        # Aspect ratios are very close, just scale
        return f"scale={target_width}:{target_height}"

    elif input_aspect > target_aspect:
        # Input is wider, scale height and crop width
        scale_height = target_height
        scale_width = int(scale_height * input_aspect)
        return f"scale={scale_width}:{scale_height},crop={target_width}:{target_height}"

    else:
        # Input is taller, scale width and crop height
        scale_width = target_width
        scale_height = int(scale_width / input_aspect)
        return f"scale={scale_width}:{scale_height},crop={target_width}:{target_height}"

    # Fallback to simple scaling
    return f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:-1:-1:black"


def export_multiple_clips(
    clip_paths: List[str],
    output_dir: str,
    config: Dict[str, Any]
) -> List[str]:
    """Export multiple clips with aspect ratio conversion."""

    exported_paths = []

    for clip_path in clip_paths:
        exported_path = export_clips(clip_path, output_dir, config)
        if exported_path:
            exported_paths.append(exported_path)

    return exported_paths


def validate_export(
    exported_path: str,
    target_ratio: str
) -> bool:
    """Validate that an exported video meets requirements."""

    if not Path(exported_path).exists():
        print(f"❌ Exported file does not exist: {exported_path}")
        return False

    # Check target aspect ratio
    width, height = get_video_dimensions(exported_path)
    expected_width, expected_height = map(int, target_ratio.split(":"))

    # Allow for small variations in dimensions due to encoding
    tolerance = 10

    if abs(width - expected_width) > tolerance or abs(height - expected_height) > tolerance:
        print(f"❌ Exported video dimensions {width}x{height} don't match target {expected_width}x{expected_height}")
        return False

    # Check file size (should be reasonable)
    file_size = Path(exported_path).stat().st_size
    if file_size < 1024:  # Less than 1KB
        print(f"❌ Exported file is too small: {file_size} bytes")
        return False

    print(f"✅ Export validation passed: {width}x{height}, {file_size / 1024:.1f}KB")
    return True


def create_export_preview(
    clip_path: str,
    output_path: str,
    config: Dict[str, Any],
    duration: float = 5.0
) -> bool:
    """Create a short preview of the export for validation."""

    # Get export configuration
    export_config = config.get("export", {})
    target_ratio = export_config.get("ratio", "9:16")

    try:
        width, height = map(int, target_ratio.split(":"))
    except ValueError:
        width, height = 9, 16

    # Create short preview
    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-t", str(duration),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "ultrafast",
        "-crf", "25",
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Creating preview for {Path(clip_path).name}")


def batch_export_validation(
    exported_paths: List[str],
    target_ratio: str
) -> Dict[str, Any]:
    """Validate multiple exported clips and return summary."""

    results = {
        "total": len(exported_paths),
        "valid": 0,
        "invalid": 0,
        "errors": []
    }

    for path in exported_paths:
        if validate_export(path, target_ratio):
            results["valid"] += 1
        else:
            results["invalid"] += 1
            results["errors"].append(f"Failed validation: {Path(path).name}")

    return results