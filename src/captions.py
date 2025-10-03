"""Caption generation and burn-in functionality (V1 Enhancement)."""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import timedelta


def format_timestamp_srt(seconds: float) -> str:
    """Format timestamp for SRT subtitle format."""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_captions_whisper(
    audio_path: str,
    output_dir: str,
    model_size: str = "base",
    language: str = "en"
) -> Optional[str]:
    """
    Generate captions using OpenAI Whisper.

    Args:
        audio_path: Path to audio file
        output_dir: Output directory for caption files
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code

    Returns:
        Path to generated SRT file
    """
    try:
        import whisper

        print(f"🎤 Transcribing audio with Whisper ({model_size} model)...")

        model = whisper.load_model(model_size)

        result = model.transcribe(
            audio_path,
            language=language,
            verbose=False,
            word_timestamps=True
        )

        output_path = Path(output_dir) / f"{Path(audio_path).stem}.srt"

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result['segments'], 1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp_srt(segment['start'])} --> {format_timestamp_srt(segment['end'])}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        print(f"✅ Generated captions: {output_path}")

        return str(output_path)

    except ImportError:
        print("❌ Whisper not installed. Install with: pip install openai-whisper")
        return None
    except Exception as e:
        print(f"❌ Error generating captions: {e}")
        return None


def create_caption_style(config: Dict[str, Any]) -> str:
    """
    Create FFmpeg subtitle style from configuration.

    Returns:
        FFmpeg subtitle filter string
    """
    brand = config.get("brand", {})
    fonts = brand.get("fonts", {})
    colors = brand.get("colors", {})

    font_name = fonts.get("primary", "Arial-Bold")
    primary_color = colors.get("primary", "#FFFFFF")
    stroke_color = colors.get("stroke", "#000000")
    stroke_width = colors.get("stroke_width", 2)

    primary_hex = primary_color.lstrip('#')
    stroke_hex = stroke_color.lstrip('#')

    style = (
        f"FontName={font_name},"
        f"FontSize=48,"
        f"PrimaryColour=&H{primary_hex[::-1]}&,"
        f"OutlineColour=&H{stroke_hex[::-1]}&,"
        f"BorderStyle=3,"
        f"Outline={stroke_width},"
        f"Shadow=0,"
        f"Alignment=2,"
        f"MarginV=80"
    )

    return style


def burn_captions(
    video_path: str,
    srt_path: str,
    output_path: str,
    config: Dict[str, Any]
) -> bool:
    """
    Burn captions into video using FFmpeg.

    Args:
        video_path: Input video path
        srt_path: SRT subtitle file path
        output_path: Output video path
        config: Configuration dictionary

    Returns:
        Success status
    """
    from .utils import run_ffmpeg_command

    style = create_caption_style(config)

    subtitle_filter = f"subtitles={srt_path}:force_style='{style}'"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", subtitle_filter,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-preset", "veryfast",
        "-crf", "20",
        output_path
    ]

    return run_ffmpeg_command(cmd, f"Burning captions into {Path(video_path).name}")


def generate_word_level_captions(
    audio_path: str,
    output_dir: str,
    model_size: str = "base",
    language: str = "en"
) -> Optional[List[Dict[str, Any]]]:
    """
    Generate word-level timestamps for dynamic captions.

    Returns:
        List of word dictionaries with timestamps
    """
    try:
        import whisper

        print(f"🎤 Generating word-level captions...")

        model = whisper.load_model(model_size)

        result = model.transcribe(
            audio_path,
            language=language,
            verbose=False,
            word_timestamps=True
        )

        words = []
        for segment in result['segments']:
            if 'words' in segment:
                for word in segment['words']:
                    words.append({
                        "word": word.get('word', '').strip(),
                        "start": word.get('start', 0),
                        "end": word.get('end', 0),
                        "confidence": word.get('probability', 1.0)
                    })

        output_path = Path(output_dir) / f"{Path(audio_path).stem}_words.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(words, f, indent=2)

        print(f"✅ Generated {len(words)} word-level timestamps")

        return words

    except ImportError:
        print("❌ Whisper not installed")
        return None
    except Exception as e:
        print(f"❌ Error generating word-level captions: {e}")
        return None


def create_animated_captions(
    video_path: str,
    words: List[Dict[str, Any]],
    output_path: str,
    config: Dict[str, Any],
    style: str = "karaoke"
) -> bool:
    """
    Create animated captions with word-by-word highlighting.

    Styles:
        - karaoke: Classic karaoke-style highlighting
        - bounce: Words bounce as they appear
        - fade: Words fade in individually

    This is a placeholder for advanced caption animation.
    Full implementation would require drawtext filters with complex timing.
    """
    print(f"⚠️  Animated captions not yet fully implemented")
    print(f"   Falling back to standard caption burn-in")

    return False


def extract_caption_snippets(
    srt_path: str,
    start_time: float,
    end_time: float
) -> str:
    """
    Extract caption snippets for a specific time range.

    Args:
        srt_path: Path to SRT file
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        New SRT content for the time range
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        segments = content.strip().split('\n\n')

        relevant_segments = []
        segment_index = 1

        for segment in segments:
            lines = segment.split('\n')
            if len(lines) < 3:
                continue

            time_line = lines[1]
            if '-->' not in time_line:
                continue

            start_str, end_str = time_line.split('-->')

            def parse_srt_time(time_str):
                time_str = time_str.strip()
                h, m, rest = time_str.split(':')
                s, ms = rest.split(',')
                return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

            seg_start = parse_srt_time(start_str)
            seg_end = parse_srt_time(end_str)

            if seg_end >= start_time and seg_start <= end_time:
                adjusted_start = max(0, seg_start - start_time)
                adjusted_end = min(end_time - start_time, seg_end - start_time)

                new_segment = f"{segment_index}\n"
                new_segment += f"{format_timestamp_srt(adjusted_start)} --> {format_timestamp_srt(adjusted_end)}\n"
                new_segment += '\n'.join(lines[2:])

                relevant_segments.append(new_segment)
                segment_index += 1

        return '\n\n'.join(relevant_segments)

    except Exception as e:
        print(f"⚠️  Error extracting caption snippets: {e}")
        return ""
