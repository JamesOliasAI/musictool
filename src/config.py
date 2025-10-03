"""Configuration management for Keo Shortform Factory."""

import yaml
from pathlib import Path
from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """Get default configuration for the shortform factory."""
    return {
        "target_lufs": -14,
        "overlay": {
            "position": "top-right",
            "opacity": 0.9,
            "margin_px": 24
        },
        "slicing": {
            "clip_len": 20,
            "stride": 18,
            "min_conf": 0.15,
            "scene_detect": False,
            "hook_detect": False
        },
        "captions": {
            "enabled": False,
            "model": "base",
            "language": "en"
        },
        "export": {
            "ratio": "9:16",
            "quality_ladder": [
                {"codec": "libx264", "crf": 20, "preset": "veryfast"},
                {"codec": "prores_ks", "profile": 3}
            ]
        }
    }


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load config from {config_path}: {e}")


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """Save configuration to YAML file."""
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    except Exception as e:
        raise ValueError(f"Failed to save config to {config_path}: {e}")


def get_preset_path(preset_name: str) -> Path:
    """Get the full path to a preset file."""
    return Path(__file__).parent.parent / "presets" / preset_name


def list_presets() -> list:
    """List available preset files."""
    presets_dir = Path(__file__).parent.parent / "presets"
    if not presets_dir.exists():
        return []

    return [f.stem for f in presets_dir.glob("*.yaml")]