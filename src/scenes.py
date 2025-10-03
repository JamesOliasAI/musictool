"""Scene detection functionality for Keo Shortform Factory (V1 Enhancement)."""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np


def detect_scenes(
    video_path: str,
    threshold: float = 30.0,
    min_scene_len: float = 2.0
) -> List[float]:
    """
    Detect scene changes in video using FFmpeg scene detection.

    Args:
        video_path: Path to video file
        threshold: Scene change detection threshold (0-100)
        min_scene_len: Minimum scene length in seconds

    Returns:
        List of scene change timestamps in seconds
    """
    print(f"🎬 Detecting scenes in {Path(video_path).name}...")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "packet=pts_time,flags",
        "-select_streams", "v:0",
        "-of", "csv=p=0",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        scene_times = []
        lines = result.stdout.strip().split('\n')

        for line in lines:
            parts = line.split(',')
            if len(parts) >= 2:
                time_str, flags = parts[0], parts[1]
                try:
                    timestamp = float(time_str)
                    if 'K' in flags:
                        scene_times.append(timestamp)
                except (ValueError, IndexError):
                    continue

        filtered_scenes = filter_scenes_by_min_length(scene_times, min_scene_len)
        print(f"📊 Found {len(filtered_scenes)} scene changes")

        return filtered_scenes

    except subprocess.CalledProcessError as e:
        print(f"❌ Scene detection failed: {e}")
        return []


def filter_scenes_by_min_length(
    scene_times: List[float],
    min_length: float
) -> List[float]:
    """Filter out scenes that are too short."""
    if not scene_times:
        return []

    filtered = [scene_times[0]]

    for i in range(1, len(scene_times)):
        if scene_times[i] - filtered[-1] >= min_length:
            filtered.append(scene_times[i])

    return filtered


def merge_scenes_with_windows(
    scene_times: List[float],
    window_starts: List[float],
    clip_len: float,
    max_clips: int = None
) -> List[float]:
    """
    Merge scene detection times with fixed window starts.
    Prioritize scene boundaries for more natural cuts.

    Args:
        scene_times: Scene change timestamps
        window_starts: Fixed window start times
        clip_len: Clip length in seconds
        max_clips: Maximum number of clips to generate

    Returns:
        Merged list of optimal start times
    """
    if not scene_times:
        return window_starts[:max_clips] if max_clips else window_starts

    merged = []
    scene_idx = 0
    window_idx = 0

    while window_idx < len(window_starts) and (max_clips is None or len(merged) < max_clips):
        window_start = window_starts[window_idx]

        nearby_scene = None
        best_distance = float('inf')

        while scene_idx < len(scene_times):
            scene_time = scene_times[scene_idx]

            if scene_time < window_start - clip_len * 0.5:
                scene_idx += 1
                continue

            if scene_time > window_start + clip_len * 0.5:
                break

            distance = abs(scene_time - window_start)
            if distance < best_distance:
                best_distance = distance
                nearby_scene = scene_time

            scene_idx += 1

        if nearby_scene is not None and best_distance < clip_len * 0.3:
            merged.append(nearby_scene)
        else:
            merged.append(window_start)

        window_idx += 1

    return merged


def get_scene_info(
    video_path: str,
    scene_times: List[float]
) -> List[Dict[str, Any]]:
    """Get detailed information about each scene."""
    scenes = []

    for i, start_time in enumerate(scene_times):
        end_time = scene_times[i + 1] if i + 1 < len(scene_times) else None

        scene_info = {
            "index": i,
            "start_time": start_time,
            "end_time": end_time,
            "duration": (end_time - start_time) if end_time else None
        }

        scenes.append(scene_info)

    return scenes


def analyze_scene_complexity(
    video_path: str,
    start_time: float,
    duration: float = 5.0
) -> Dict[str, Any]:
    """
    Analyze scene complexity (motion, color variation) for hook detection.

    Returns complexity metrics that can help identify engaging segments.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "frame=pict_type,pkt_pts_time",
        "-read_intervals", f"{start_time}%{start_time + duration}",
        "-of", "csv=p=0",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        frame_types = {'I': 0, 'P': 0, 'B': 0}
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 1:
                frame_type = parts[0]
                if frame_type in frame_types:
                    frame_types[frame_type] += 1

        total_frames = sum(frame_types.values())

        motion_score = (frame_types['P'] + frame_types['B']) / total_frames if total_frames > 0 else 0

        return {
            "motion_score": motion_score,
            "frame_count": total_frames,
            "i_frames": frame_types['I'],
            "complexity": "high" if motion_score > 0.7 else "medium" if motion_score > 0.4 else "low"
        }

    except Exception as e:
        print(f"⚠️  Could not analyze scene complexity: {e}")
        return {"motion_score": 0, "complexity": "unknown"}
