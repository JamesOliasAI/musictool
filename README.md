# Keo Shortform Factory

Automated short-form video creation tool with audio alignment and overlay compositing.

## Overview

Keo Shortform Factory takes long-form videos, overlay videos, and overlay audio, then automatically:
- Aligns overlay audio with base video using onset-based cross-correlation
- Replaces base audio with aligned overlay audio
- Composites overlay video at specified position and opacity
- Slices into fixed-length clips with configurable stride
- Exports in desired aspect ratios (9:16, 1:1, or 16:9)

## Features

- **Audio Alignment**: Onset-based cross-correlation with confidence scoring
- **Video Composition**: Overlay compositing with position and opacity control
- **Fixed-Window Slicing**: Configurable clip length and stride
- **Multi-Ratio Export**: Support for TikTok (9:16), Square (1:1), and Landscape (16:9)
- **Configurable Presets**: YAML-based configuration system
- **Batch Processing**: Process multiple videos with consistent settings
- **Quality Ladder**: Multiple quality settings for different use cases

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd keo-shortform-factory

# Install dependencies
pip install -e .

# Or for development
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- FFmpeg (with ffprobe)
- Required Python packages (see pyproject.toml)

## Quick Start

```bash
# Basic usage with default TikTok preset
shortform \
  --base "path/to/long_video.mp4" \
  --overlay-video "path/to/overlay.mov" \
  --overlay-audio "path/to/overlay_audio.wav" \
  --out "output/directory"

# Custom configuration
shortform \
  --base "input/long_video.mp4" \
  --overlay-video "input/overlay.mov" \
  --overlay-audio "input/music.wav" \
  --out "output/session_001" \
  --preset "presets/tiktok_vertical.yaml" \
  --clip-len 25 \
  --clip-stride 20 \
  --position "top-right" \
  --opacity 0.85
```

## Configuration

Create preset files in the `presets/` directory:

```yaml
# presets/tiktok_vertical.yaml
target_lufs: -14
overlay:
  position: top-right
  opacity: 0.9
  margin_px: 24
slicing:
  clip_len: 20
  stride: 18
  min_conf: 0.15
export:
  ratio: "9:16"
  quality_ladder:
    - codec: "libx264"
      crf: 20
      preset: "veryfast"
```

## Command Line Options

- `--base, -b`: Path to base long-form video (required)
- `--overlay-video, -ov`: Path to overlay video (required)
- `--overlay-audio, -oa`: Path to overlay audio (required)
- `--out, -o`: Output directory (required)
- `--preset, -p`: Path to preset config file (default: presets/tiktok_vertical.yaml)
- `--clip-len, -l`: Clip length in seconds (default: 20)
- `--clip-stride, -s`: Clip stride in seconds (default: 18)
- `--min-conf, -c`: Minimum alignment confidence threshold (default: 0.15)
- `--ratio, -r`: Export aspect ratio (default: 9:16)
- `--position`: Overlay position (default: top-right)
- `--opacity`: Overlay opacity (default: 0.9)
- `--dry-run`: Show plan without executing
- `--manifest`: Write manifest JSON (default: true)

## Output Structure

```
output/session_YYYYmmdd_HHMMSS/
├── manifest.json           # Processing summary and metadata
├── master.mp4             # Final video with audio + overlay
├── clips_src/             # Raw sliced clips
│   ├── clip_000000_000020.mp4
│   ├── clip_000018_000038.mp4
│   └── ...
└── exports/
    └── 9x16/              # Aspect ratio subdirectories
        ├── clip_000000_000020_9x16.mp4
        ├── clip_000018_000038_9x16.mp4
        └── ...
```

## Architecture

The tool is organized into modular components:

- **io_ops.py**: Input validation and media probing
- **audio_align.py**: Onset-based audio alignment with cross-correlation
- **video_ops.py**: Video composition and overlay handling
- **cutter.py**: Fixed-window video slicing
- **exporter.py**: Aspect ratio conversion and quality encoding
- **config.py**: YAML configuration management
- **cli.py**: Command-line interface with Typer

## Algorithm Details

### Audio Alignment
1. Extract audio from base video at 48kHz mono
2. Compute onset envelopes using Librosa
3. Z-score normalize envelopes
4. Cross-correlate to find optimal lag
5. Calculate confidence score
6. Apply time shift if confidence > threshold

### Video Composition
1. Replace base video audio with aligned overlay audio
2. Composite overlay video using FFmpeg overlay filter
3. Position overlay based on configuration
4. Apply opacity and safe area margins

## Performance

- Uses `ffmpeg -c copy` for fast slicing when possible
- Parallel export processing with concurrent.futures
- Configurable quality presets for speed vs. compression trade-offs
- Batch processing support for multiple videos

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, please [add contact information or issue tracker].

---

*Built with Python, FFmpeg, and Librosa for automated short-form video creation.*# musictool
