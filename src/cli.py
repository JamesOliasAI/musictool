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
from .cutter import slice_video, generate_clip_starts
from .exporter import export_clips
from .scenes import detect_scenes, merge_scenes_with_windows
from .hook_finder import find_hooks, bias_starts_to_hooks
from .captions import generate_captions_whisper, burn_captions

app = typer.Typer()


@app.command("process")
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
    hook_detect: bool = typer.Option(False, "--hook-detect", help="Enable hook detection for engaging clips"),
    captions: bool = typer.Option(False, "--captions", help="Generate and burn captions"),
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
    config["slicing"]["scene_detect"] = scene_detect
    config["slicing"]["hook_detect"] = hook_detect
    config["export"]["ratio"] = ratio
    config["overlay"]["position"] = position
    config["overlay"]["opacity"] = opacity
    config["captions"]["enabled"] = captions

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

    # Slice into clips with optional scene detection and hook finding
    typer.echo("✂️  Slicing master video into clips...")

    # Generate base clip starts
    duration = probe_media(str(master_video))["duration"]
    window_starts = generate_clip_starts(duration, clip_len, clip_stride)

    # Apply scene detection if enabled
    if scene_detect:
        typer.echo("🎬 Applying scene detection...")
        scene_times = detect_scenes(str(master_video), threshold=30.0, min_scene_len=2.0)
        window_starts = merge_scenes_with_windows(
            scene_times, window_starts, clip_len, max_clips=None
        )

    # Apply hook detection if enabled
    if hook_detect:
        typer.echo("🎯 Finding engaging hooks...")
        hooks = find_hooks(
            alignment_result["shifted_audio_path"],
            duration,
            clip_len=clip_len,
            num_hooks=len(window_starts)
        )
        window_starts = bias_starts_to_hooks(window_starts, hooks, attraction_radius=5.0)

    # Create clips from optimized start times
    from .cutter import create_clip
    clips = []
    for i, start_time in enumerate(window_starts):
        clip_path = create_clip(
            str(master_video),
            str(clips_src_dir),
            start_time,
            clip_len,
            i
        )
        if clip_path:
            clips.append(clip_path)

    # Generate captions if enabled
    captions_path = None
    if captions:
        typer.echo("🎤 Generating captions...")
        captions_path = generate_captions_whisper(
            alignment_result["shifted_audio_path"],
            str(session_dir),
            model_size="base",
            language="en"
        )
        if captions_path:
            typer.echo(f"✅ Captions generated: {captions_path}")

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
            "features": {
                "scene_detection": scene_detect,
                "hook_detection": hook_detect,
                "captions": captions
            },
            "alignment": alignment_result,
            "processing": {
                "master_video": str(master_video),
                "clips_count": len(clips),
                "exports_count": len(exported_clips),
                "captions_file": captions_path
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

    return manifest_data


@app.command("batch")
def batch_process(
    csv: str = typer.Option(None, "--csv", "-c", help="CSV file with batch jobs"),
    folder: str = typer.Option(None, "--folder", "-f", help="Folder with base videos"),
    overlay_video: str = typer.Option(None, "--overlay-video", "-ov", help="Overlay video (for folder mode)"),
    overlay_audio: str = typer.Option(None, "--overlay-audio", "-oa", help="Overlay audio (for folder mode)"),
    preset: str = typer.Option("presets/tiktok_vertical.yaml", "--preset", "-p", help="Default preset"),
    out: str = typer.Option(..., "--out", "-o", help="Output root directory"),
    workers: int = typer.Option(2, "--workers", "-w", help="Number of parallel workers"),
):
    """Process multiple videos in batch mode."""
    from .batch_processor import BatchProcessor, create_batch_from_folder

    if csv:
        typer.echo(f"📄 Loading batch jobs from CSV: {csv}")
        processor = BatchProcessor(preset, out, max_workers=workers)
        processor.load_from_csv(csv, base_preset=preset)

    elif folder and overlay_video and overlay_audio:
        typer.echo(f"📁 Creating batch from folder: {folder}")
        processor = create_batch_from_folder(
            folder, overlay_video, overlay_audio, preset, out
        )

    else:
        typer.echo("❌ Must provide either --csv or (--folder + --overlay-video + --overlay-audio)")
        raise typer.Exit(1)

    if len(processor.jobs) == 0:
        typer.echo("⚠️  No jobs to process")
        raise typer.Exit(0)

    typer.echo(f"\n🚀 Starting batch processing of {len(processor.jobs)} jobs...")

    summary = processor.process_all()

    typer.echo(f"\n✅ Batch complete!")
    typer.echo(f"   Completed: {summary['completed']}")
    typer.echo(f"   Failed: {summary['failed']}")
    typer.echo(f"   Output: {out}")


def process_video(
    base: str,
    overlay_video: str,
    overlay_audio: str,
    out: str,
    preset: str,
    manifest: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Helper function to process a single video.
    Used by batch processor and CLI.
    """
    return main(
        base=base,
        overlay_video=overlay_video,
        overlay_audio=overlay_audio,
        out=out,
        preset=preset,
        manifest=manifest,
        **kwargs
    )


if __name__ == "__main__":
    app()