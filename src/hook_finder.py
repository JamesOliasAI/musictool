"""Hook finder functionality for identifying engaging segments (V1 Enhancement)."""

import subprocess
import librosa
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple


def extract_audio_energy(
    audio_path: str,
    hop_length: int = 512,
    sr: int = 48000
) -> Tuple[np.ndarray, float]:
    """
    Extract short-term energy envelope from audio.

    Returns:
        Tuple of (energy_envelope, duration_seconds)
    """
    try:
        y, sr = librosa.load(audio_path, sr=sr, mono=True)

        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

        rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-10)

        duration = len(y) / sr

        return rms_normalized, duration

    except Exception as e:
        print(f"❌ Error extracting audio energy: {e}")
        return np.array([]), 0.0


def detect_voice_activity(
    audio_path: str,
    frame_length: int = 2048,
    hop_length: int = 512,
    sr: int = 48000,
    threshold: float = 0.3
) -> List[Tuple[float, float]]:
    """
    Detect voice activity regions in audio.

    Returns:
        List of (start_time, end_time) tuples for voice segments
    """
    try:
        y, sr = librosa.load(audio_path, sr=sr, mono=True)

        zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        zcr_norm = (zcr - np.min(zcr)) / (np.max(zcr) - np.min(zcr) + 1e-10)
        rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-10)

        voice_prob = (0.3 * zcr_norm + 0.7 * rms_norm)

        is_voice = voice_prob > threshold

        times = librosa.frames_to_time(np.arange(len(is_voice)), sr=sr, hop_length=hop_length)

        voice_segments = []
        in_segment = False
        segment_start = 0

        for i, (active, time) in enumerate(zip(is_voice, times)):
            if active and not in_segment:
                segment_start = time
                in_segment = True
            elif not active and in_segment:
                voice_segments.append((segment_start, time))
                in_segment = False

        if in_segment:
            voice_segments.append((segment_start, times[-1]))

        return voice_segments

    except Exception as e:
        print(f"❌ Error detecting voice activity: {e}")
        return []


def find_energy_peaks(
    energy_envelope: np.ndarray,
    sr: int = 48000,
    hop_length: int = 512,
    prominence: float = 0.3,
    distance: int = 100
) -> List[float]:
    """
    Find peaks in energy envelope that indicate engaging moments.

    Args:
        energy_envelope: Normalized energy values
        sr: Sample rate
        hop_length: Hop length used for energy extraction
        prominence: Minimum prominence for peak detection
        distance: Minimum distance between peaks in frames

    Returns:
        List of peak timestamps in seconds
    """
    from scipy.signal import find_peaks

    peaks, properties = find_peaks(
        energy_envelope,
        prominence=prominence,
        distance=distance
    )

    peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)

    return peak_times.tolist()


def score_hook_potential(
    audio_path: str,
    start_time: float,
    window_size: float = 5.0
) -> Dict[str, Any]:
    """
    Score the 'hook potential' of a segment based on audio features.

    High hook potential = high energy + voice activity + dynamic range

    Returns:
        Dictionary with hook score and breakdown
    """
    try:
        y, sr = librosa.load(audio_path, sr=48000, mono=True, offset=start_time, duration=window_size)

        if len(y) == 0:
            return {"hook_score": 0, "breakdown": {}}

        rms = librosa.feature.rms(y=y)[0]
        energy_mean = np.mean(rms)
        energy_std = np.std(rms)

        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = np.mean(zcr)

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        brightness = np.mean(spectral_centroid) / sr

        energy_score = np.clip(energy_mean * 10, 0, 1)
        dynamic_score = np.clip(energy_std * 5, 0, 1)
        voice_score = np.clip(zcr_mean * 2, 0, 1)
        brightness_score = np.clip(brightness * 2, 0, 1)

        hook_score = (
            0.4 * energy_score +
            0.3 * dynamic_score +
            0.2 * voice_score +
            0.1 * brightness_score
        )

        return {
            "hook_score": float(hook_score),
            "breakdown": {
                "energy": float(energy_score),
                "dynamics": float(dynamic_score),
                "voice": float(voice_score),
                "brightness": float(brightness_score)
            },
            "recommendation": "strong" if hook_score > 0.7 else "good" if hook_score > 0.5 else "weak"
        }

    except Exception as e:
        print(f"⚠️  Error scoring hook potential: {e}")
        return {"hook_score": 0, "breakdown": {}, "recommendation": "unknown"}


def find_hooks(
    audio_path: str,
    video_duration: float,
    clip_len: float = 20,
    num_hooks: int = 10
) -> List[Dict[str, Any]]:
    """
    Find the most engaging hook points in audio for clip starts.

    Args:
        audio_path: Path to audio file
        video_duration: Total video duration
        clip_len: Desired clip length
        num_hooks: Number of hooks to find

    Returns:
        List of hook dictionaries with timestamps and scores
    """
    print(f"🎯 Finding {num_hooks} engaging hooks in audio...")

    energy_envelope, duration = extract_audio_energy(audio_path)

    if len(energy_envelope) == 0:
        print("⚠️  Could not extract energy, falling back to uniform distribution")
        stride = duration / (num_hooks + 1)
        return [
            {
                "timestamp": i * stride,
                "hook_score": 0.5,
                "breakdown": {},
                "recommendation": "unknown"
            }
            for i in range(1, num_hooks + 1)
        ]

    peak_times = find_energy_peaks(energy_envelope)

    candidate_times = []
    for peak_time in peak_times:
        if clip_len / 2 < peak_time < duration - clip_len / 2:
            hook_analysis = score_hook_potential(audio_path, peak_time - clip_len / 4, clip_len / 2)
            candidate_times.append({
                "timestamp": peak_time,
                **hook_analysis
            })

    candidate_times.sort(key=lambda x: x["hook_score"], reverse=True)

    selected_hooks = []
    for candidate in candidate_times:
        if len(selected_hooks) >= num_hooks:
            break

        too_close = False
        for existing in selected_hooks:
            if abs(candidate["timestamp"] - existing["timestamp"]) < clip_len * 0.5:
                too_close = True
                break

        if not too_close:
            selected_hooks.append(candidate)

    while len(selected_hooks) < num_hooks and len(selected_hooks) < duration / clip_len:
        candidates_set = set(h["timestamp"] for h in selected_hooks)

        best_time = None
        best_gap = 0
        for t in np.linspace(clip_len, duration - clip_len, int(duration / clip_len)):
            if t not in candidates_set:
                min_distance = min((abs(t - h["timestamp"]) for h in selected_hooks), default=float('inf'))
                if min_distance > best_gap:
                    best_gap = min_distance
                    best_time = t

        if best_time:
            hook_analysis = score_hook_potential(audio_path, best_time, clip_len / 2)
            selected_hooks.append({
                "timestamp": best_time,
                **hook_analysis
            })
        else:
            break

    selected_hooks.sort(key=lambda x: x["timestamp"])

    print(f"✅ Found {len(selected_hooks)} hook points (avg score: {np.mean([h['hook_score'] for h in selected_hooks]):.2f})")

    return selected_hooks


def bias_starts_to_hooks(
    window_starts: List[float],
    hooks: List[Dict[str, Any]],
    attraction_radius: float = 5.0
) -> List[float]:
    """
    Adjust window start times to align with nearby hooks.

    Args:
        window_starts: Original fixed window start times
        hooks: Hook points from find_hooks
        attraction_radius: How far to look for nearby hooks (seconds)

    Returns:
        Adjusted start times biased toward hooks
    """
    if not hooks:
        return window_starts

    hook_times = [h["timestamp"] for h in hooks]
    adjusted_starts = []

    for start in window_starts:
        nearby_hooks = [h for h in hook_times if abs(h - start) < attraction_radius]

        if nearby_hooks:
            nearest_hook = min(nearby_hooks, key=lambda h: abs(h - start))
            adjusted_starts.append(nearest_hook)
        else:
            adjusted_starts.append(start)

    return adjusted_starts
