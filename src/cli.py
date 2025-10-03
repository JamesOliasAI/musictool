"""Command-line interface for Keo Shortform Factory."""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml
from tqdm import tqdm

from .config import load_config, get_default_config
from .io_ops import validate_media_compatibility, probe_media, extract_audio, prepare_overlay_audio
from .utils import validate_file_exists
from .audio_align import align_audio
from .video_ops import replace_audio, composite_overlay
from .cutter import slice_video
from .exporter import export_clips

app = typer.Typer()


@app.command()
def main(
    base: str = typer.Option(..., "--base", "-b", help="Path to base long-form video"),
    overlay_video: str = typer.Option(..., "--overlay-video", "-ov", help="Path to overlay video"),
    overlay_audio: str = typer.Option(..., "--overlay-audio", "-oa", help="Path to overlay audio"),
    out: str = typer.Option(..., "--out", "-o", help="Output directory"),
    preset: str = typer.Option("presets/tiktok_vertical.yaml", "--preset", "-p", help="Path to preset config file"),
    clip_len: int = typer.Option(20, "--clip-len", "-l", help="Clip length in seconds"),
    clip_stride: int = typer.Option(18, "--clip-stride", "-s", help="Clip stride in seconds"),
    scene_detect: bool = typer.Option(False, "--scene-detect", help="Enable scene detection for better cuts"),
    min_conf: float = typer.Option(0.15, "--min-conf", "-c", help="Minimum alignment confidence threshold"),
    ratio: str = typer.Option("9:16", "--ratio", "-r", help="Export aspect ratio (9:16, 1:1, or 16:9)"),
    position: str = typer.Option("top-right", "--position", help="Overlay position"),
    opacity: float = typer.Option(0.9, "--opacity", help="Overlay opacity"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
    manifest: bool = typer.Option(True, "--manifest", help="Write manifest JSON"),
):
    """Create short-form videos from long-form content with overlay audio and video."""

    # Create output directory with timestamp
    session_dir = Path(str(out)) / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    clips_src_dir = session_dir / "clips_src"
    exports_dir = session_dir / "exports" / str(ratio).replace(":", "x")

    if not dry_run:
        session_dir.mkdir(parents=True, exist_ok=True)
        clips_src_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)

    # Load or create config
    if Path(str(preset)).exists():
        config = load_config(preset)
    else:
        typer.echo(f"Preset file {preset} not found, using defaults")
        config = get_default_config()

    # Override config with CLI args
    config["slicing"]["clip_len"] = clip_len
    config["slicing"]["stride"] = clip_stride
    config["slicing"]["min_conf"] = min_conf
    config["export"]["ratio"] = ratio
    config["overlay"]["position"] = position
    config["overlay"]["opacity"] = opacity

    # Validate inputs
    typer.echo("🔍 Validating inputs...")
    base_valid = validate_file_exists(str(base), "base video")
    overlay_video_valid = validate_file_exists(str(overlay_video), "overlay video")
    overlay_audio_valid = validate_file_exists(str(overlay_audio), "overlay audio")

    if not (base_valid and overlay_video_valid and overlay_audio_valid):
        raise ValueError("One or more input files are invalid")

    if dry_run:
        typer.echo(f"📋 Dry run plan for {base}:")
        typer.echo(f"  Output dir: {session_dir}")
        typer.echo(f"  Config: {clip_len}s clips, {clip_stride}s stride, {ratio} ratio")
        typer.echo(f"  Overlay: {position}, {opacity} opacity")
        return

    # Probe media for detailed info
    typer.echo("📊 Probing media files...")
    base_probe = probe_media(str(base))
    overlay_audio_probe = probe_media(str(overlay_audio))

    # Validate media compatibility
    validate_media_compatibility(base_probe, overlay_audio_probe)

    # Extract and prepare audio files
    typer.echo("🎵 Preparing audio files...")
    base_audio_path = extract_audio(str(base), str(session_dir))
    overlay_audio_path = prepare_overlay_audio(str(overlay_audio), str(session_dir), config.get("target_lufs", -14))

    # Align audio
    typer.echo("🎵 Aligning overlay audio with base video...")
    alignment_result = align_audio(
        base_audio_path=base_audio_path,
        overlay_audio_path=overlay_audio_path,
        config=config
    )

    # Replace audio in base video
    typer.echo("🎬 Replacing base audio with aligned overlay...")
    video_with_audio = session_dir / "video_with_audio.mp4"
    from .video_ops import replace_audio, composite_overlay
    replace_audio(
        video_path=str(base),
        audio_path=alignment_result["shifted_audio_path"],
        output_path=str(video_with_audio),
        config=config
    )

    # Composite overlay video
    typer.echo("🎭 Compositing overlay video...")
    master_video = session_dir / "master.mp4"
    composite_overlay(
        base_video_path=str(video_with_audio),
        overlay_video_path=str(overlay_video),
        output_path=str(master_video),
        config=config
    )

    # Slice into clips
    typer.echo("✂️  Slicing master video into clips...")
    from .cutter import slice_video
    clips = slice_video(
        video_path=str(master_video),
        output_dir=str(clips_src_dir),
        config=config
    )

    # Export in target ratio
    typer.echo(f"📤 Exporting {len(clips)} clips in {ratio} ratio...")
    exported_clips = []
    for clip in tqdm(clips, desc="Exporting"):
        exported_path = export_clips(
            clip_path=clip,
            output_dir=str(exports_dir),
            config=config
        )
        exported_clips.append(exported_path)

    # Write manifest
    if manifest:
        manifest_data = {
            "session_id": session_dir.name,
            "created_at": datetime.now().isoformat(),
            "inputs": {
                "base_video": base,
                "overlay_video": overlay_video,
                "overlay_audio": overlay_audio,
            },
            "config": config,
            "alignment": alignment_result,
            "processing": {
                "master_video": str(master_video),
                "clips_count": len(clips),
                "exports_count": len(exported_clips),
            },
            "outputs": {
                "clips_src": [str(c) for c in clips],
                "exports": [str(e) for e in exported_clips],
            }
        }

        manifest_path = session_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)

    typer.echo(f"✅ Complete! Processed into {len(exported_clips)} clips")
    typer.echo(f"📁 Output: {session_dir}")


if __name__ == "__main__":
    app()