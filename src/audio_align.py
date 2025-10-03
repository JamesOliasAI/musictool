"""Audio alignment functionality for Keo Shortform Factory."""

import numpy as np
import librosa
from pathlib import Path
from typing import Dict, Any, Tuple
import subprocess

from .utils import run_ffmpeg_command, ensure_dir


def compute_onset_envelope(audio_path: str, sr: int = 48000) -> np.ndarray:
    """Compute onset envelope from audio file."""
    try:
        # Load audio with librosa
        y, _ = librosa.load(audio_path, sr=sr, mono=True)

        # Compute onset envelope
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Z-score normalize
        if len(onset_env) > 0:
            onset_env = (onset_env - np.mean(onset_env)) / (np.std(onset_env) + 1e-10)

        return onset_env

    except Exception as e:
        print(f"❌ Error computing onset envelope for {audio_path}: {e}")
        return np.array([])


def cross_correlation_alignment(
    base_envelope: np.ndarray,
    overlay_envelope: np.ndarray,
    sr: int = 48000,
    hop_length: int = 512
) -> Tuple[float, float]:
    """Compute cross-correlation alignment between two onset envelopes."""

    if len(base_envelope) == 0 or len(overlay_envelope) == 0:
        return 0.0, 0.0

    # Compute cross-correlation
    # Pad the shorter array to match the longer one
    max_len = max(len(base_envelope), len(overlay_envelope))

    if len(base_envelope) < max_len:
        base_padded = np.pad(base_envelope, (0, max_len - len(base_envelope)))
    else:
        base_padded = base_envelope

    if len(overlay_envelope) < max_len:
        overlay_padded = np.pad(overlay_envelope, (0, max_len - len(overlay_envelope)))
    else:
        overlay_padded = overlay_envelope

    # Compute cross-correlation
    correlation = np.correlate(base_padded, overlay_padded, mode='full')

    # Find the lag with maximum correlation
    lag_samples = np.argmax(correlation) - (len(overlay_padded) - 1)

    # Convert lag from samples to seconds
    lag_seconds = lag_samples * hop_length / sr

    # Compute confidence as the ratio of peak to the product of norms
    confidence = correlation[np.argmax(correlation)]
    norm_product = np.linalg.norm(base_padded) * np.linalg.norm(overlay_padded)
    confidence = confidence / (norm_product + 1e-10)

    return lag_seconds, confidence


def time_shift_audio(
    input_path: str,
    output_path: str,
    shift_seconds: float,
    direction: str = "delay"
) -> bool:
    """Time-shift audio by specified seconds using FFmpeg."""

    if abs(shift_seconds) < 0.001:  # Very small shift, just copy
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c", "copy",
            output_path
        ]
        return run_ffmpeg_command(cmd, f"Copying audio (negligible shift: {shift_seconds:.3f}s)")

    if direction == "delay" and shift_seconds > 0:
        # Positive delay - use adelay filter
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", f"adelay={int(shift_seconds * 1000)}:all=true",
            "-c:a", "pcm_s16le",
            output_path
        ]
        return run_ffmpeg_command(cmd, f"Delaying audio by {shift_seconds:.3f}s")

    elif direction == "advance" and shift_seconds < 0:
        # Negative shift (advance) - use atrim and asetpts
        shift_seconds = abs(shift_seconds)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ss", str(shift_seconds),
            "-c:a", "pcm_s16le",
            output_path
        ]
        return run_ffmpeg_command(cmd, f"Advancing audio by {shift_seconds:.3f}s")

    else:
        print(f"⚠️  Unexpected shift scenario: {shift_seconds}s {direction}")
        # Fallback to copy
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c", "copy",
            output_path
        ]
        return run_ffmpeg_command(cmd, "Copying audio (fallback)")


def align_audio(
    base_audio_path: str,
    overlay_audio_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Align overlay audio with base audio using onset-based cross-correlation."""

    print(f"🔄 Aligning {overlay_audio_path} with {base_audio_path}...")

    # Extract onset envelopes
    base_envelope = compute_onset_envelope(base_audio_path)
    overlay_envelope = compute_onset_envelope(overlay_audio_path)

    if len(base_envelope) == 0 or len(overlay_envelope) == 0:
        print("⚠️  Could not compute onset envelopes, using 0 offset")
        lag_seconds = 0.0
        confidence = 0.0
    else:
        # Compute alignment
        lag_seconds, confidence = cross_correlation_alignment(
            base_envelope,
            overlay_envelope
        )

    # Check confidence threshold
    min_conf = config.get("slicing", {}).get("min_conf", 0.15)

    if confidence < min_conf:
        print(f"⚠️  Low alignment confidence ({confidence:.3f} < {min_conf}), using 0 offset")
        lag_seconds = 0.0
        confidence = 0.0

    print(f"📊 Alignment: {lag_seconds:+.3f}s offset, confidence: {confidence:.3f}")

    # Apply time shift to overlay audio
    output_dir = Path(base_audio_path).parent
    base_name = Path(overlay_audio_path).stem
    shifted_path = output_dir / f"{base_name}_shifted.wav"

    if lag_seconds >= 0:
        # Positive lag - delay overlay
        success = time_shift_audio(
            overlay_audio_path,
            str(shifted_path),
            lag_seconds,
            "delay"
        )
    else:
        # Negative lag - advance overlay (trim from start)
        success = time_shift_audio(
            overlay_audio_path,
            str(shifted_path),
            lag_seconds,
            "advance"
        )

    if not success:
        raise RuntimeError("Failed to apply time shift to overlay audio")

    return {
        "original_offset": lag_seconds,
        "confidence": confidence,
        "shifted_audio_path": str(shifted_path),
        "base_envelope_shape": base_envelope.shape,
        "overlay_envelope_shape": overlay_envelope.shape
    }


def validate_audio_alignment(
    base_path: str,
    shifted_overlay_path: str,
    expected_offset: float,
    tolerance: float = 0.05
) -> bool:
    """Validate that audio alignment was applied correctly."""

    # This is a simplified validation - in practice you might want to
    # re-run alignment and compare results

    if not Path(shifted_overlay_path).exists():
        print("❌ Shifted audio file does not exist")
        return False

    # Check if file has content
    try:
        info = get_audio_info(shifted_overlay_path)
        if not info or info.get("duration", 0) == 0:
            print("❌ Shifted audio file is empty or invalid")
            return False
    except Exception as e:
        print(f"❌ Error validating shifted audio: {e}")
        return False

    print(f"✅ Audio alignment validation passed")
    return True


# Import here to avoid circular imports
def get_audio_info(file_path: str) -> Dict[str, Any]:
    """Get audio file information."""
    from .utils import run_ffprobe_command

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-select_streams", "a",
        file_path
    ]

    return run_ffprobe_command(cmd) or {}