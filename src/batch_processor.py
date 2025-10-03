"""Batch processing functionality for multiple videos (V2 Enhancement)."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .config import load_config
from .io_ops import validate_file_exists, probe_media
from .utils import ensure_dir


class BatchJob:
    """Represents a single batch processing job."""

    def __init__(
        self,
        base_video: str,
        overlay_video: str,
        overlay_audio: str,
        preset: str,
        output_dir: str,
        job_id: Optional[str] = None
    ):
        self.base_video = base_video
        self.overlay_video = overlay_video
        self.overlay_audio = overlay_audio
        self.preset = preset
        self.output_dir = output_dir
        self.job_id = job_id or f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.status = "pending"
        self.result = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "base_video": self.base_video,
            "overlay_video": self.overlay_video,
            "overlay_audio": self.overlay_audio,
            "preset": self.preset,
            "output_dir": self.output_dir,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }


class BatchProcessor:
    """Process multiple videos in batch with inheritance."""

    def __init__(
        self,
        base_preset: str,
        output_root: str,
        max_workers: int = 2
    ):
        self.base_preset = base_preset
        self.output_root = output_root
        self.max_workers = max_workers
        self.jobs: List[BatchJob] = []

    def add_job(
        self,
        base_video: str,
        overlay_video: str,
        overlay_audio: str,
        preset: Optional[str] = None
    ) -> str:
        """
        Add a job to the batch queue.

        Args:
            base_video: Path to base video
            overlay_video: Path to overlay video
            overlay_audio: Path to overlay audio
            preset: Optional preset override (uses base_preset if None)

        Returns:
            Job ID
        """
        preset = preset or self.base_preset

        job_id = f"job_{len(self.jobs) + 1}_{datetime.now().strftime('%H%M%S')}"
        output_dir = Path(self.output_root) / job_id

        job = BatchJob(
            base_video=base_video,
            overlay_video=overlay_video,
            overlay_audio=overlay_audio,
            preset=preset,
            output_dir=str(output_dir),
            job_id=job_id
        )

        self.jobs.append(job)
        return job_id

    def validate_jobs(self) -> Dict[str, Any]:
        """Validate all jobs before processing."""
        print(f"🔍 Validating {len(self.jobs)} jobs...")

        validation_results = {
            "valid": 0,
            "invalid": 0,
            "errors": []
        }

        for job in self.jobs:
            try:
                if not validate_file_exists(job.base_video, "base video"):
                    raise ValueError(f"Base video not found: {job.base_video}")

                if not validate_file_exists(job.overlay_video, "overlay video"):
                    raise ValueError(f"Overlay video not found: {job.overlay_video}")

                if not validate_file_exists(job.overlay_audio, "overlay audio"):
                    raise ValueError(f"Overlay audio not found: {job.overlay_audio}")

                if not Path(job.preset).exists():
                    raise ValueError(f"Preset not found: {job.preset}")

                validation_results["valid"] += 1

            except Exception as e:
                job.status = "validation_failed"
                job.error = str(e)
                validation_results["invalid"] += 1
                validation_results["errors"].append(f"{job.job_id}: {e}")

        return validation_results

    def process_single_job(self, job: BatchJob) -> Dict[str, Any]:
        """Process a single batch job."""
        from .cli import process_video

        try:
            job.status = "processing"

            result = process_video(
                base=job.base_video,
                overlay_video=job.overlay_video,
                overlay_audio=job.overlay_audio,
                out=job.output_dir,
                preset=job.preset,
                manifest=True
            )

            job.status = "completed"
            job.result = result

            return {
                "job_id": job.job_id,
                "status": "success",
                "result": result
            }

        except Exception as e:
            job.status = "failed"
            job.error = str(e)

            return {
                "job_id": job.job_id,
                "status": "error",
                "error": str(e)
            }

    def process_all(self) -> Dict[str, Any]:
        """Process all jobs in the batch."""
        validation = self.validate_jobs()

        if validation["invalid"] > 0:
            print(f"⚠️  {validation['invalid']} jobs failed validation")
            for error in validation["errors"]:
                print(f"   - {error}")

        valid_jobs = [j for j in self.jobs if j.status != "validation_failed"]

        if not valid_jobs:
            return {
                "total": len(self.jobs),
                "completed": 0,
                "failed": len(self.jobs),
                "validation": validation,
                "results": []
            }

        print(f"\n🚀 Processing {len(valid_jobs)} valid jobs with {self.max_workers} workers...")

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_single_job, job): job
                for job in valid_jobs
            }

            with tqdm(total=len(valid_jobs), desc="Batch processing") as pbar:
                for future in as_completed(futures):
                    job = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "job_id": job.job_id,
                            "status": "error",
                            "error": str(e)
                        })
                    finally:
                        pbar.update(1)

        completed = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "error")

        summary = {
            "total": len(self.jobs),
            "completed": completed,
            "failed": failed + validation["invalid"],
            "validation": validation,
            "results": results
        }

        manifest_path = Path(self.output_root) / f"batch_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ensure_dir(self.output_root)

        with open(manifest_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n✅ Batch complete: {completed} succeeded, {failed} failed")
        print(f"📄 Manifest: {manifest_path}")

        return summary

    def load_from_csv(self, csv_path: str, base_preset: Optional[str] = None) -> int:
        """
        Load batch jobs from CSV file.

        CSV format:
        base_video,overlay_video,overlay_audio,preset
        video1.mp4,overlay1.mov,audio1.wav,preset1.yaml
        video2.mp4,overlay2.mov,audio2.wav,

        Args:
            csv_path: Path to CSV file
            base_preset: Default preset if not specified in CSV

        Returns:
            Number of jobs loaded
        """
        import csv

        loaded = 0

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    base_video = row.get('base_video', '').strip()
                    overlay_video = row.get('overlay_video', '').strip()
                    overlay_audio = row.get('overlay_audio', '').strip()
                    preset = row.get('preset', '').strip() or base_preset or self.base_preset

                    if base_video and overlay_video and overlay_audio:
                        self.add_job(base_video, overlay_video, overlay_audio, preset)
                        loaded += 1

            print(f"📄 Loaded {loaded} jobs from {csv_path}")

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")

        return loaded


def discover_videos_in_folder(
    folder_path: str,
    extensions: List[str] = None
) -> List[str]:
    """
    Discover video files in a folder.

    Args:
        folder_path: Path to folder to scan
        extensions: List of video extensions to look for

    Returns:
        List of video file paths
    """
    if extensions is None:
        extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        print(f"❌ Folder not found: {folder_path}")
        return []

    videos = []

    for ext in extensions:
        videos.extend(folder.glob(f"*{ext}"))
        videos.extend(folder.glob(f"*{ext.upper()}"))

    return [str(v) for v in sorted(videos)]


def create_batch_from_folder(
    base_videos_folder: str,
    overlay_video: str,
    overlay_audio: str,
    preset: str,
    output_root: str
) -> BatchProcessor:
    """
    Create a batch processor from a folder of base videos.

    All videos in the folder will be processed with the same overlay and audio.

    Args:
        base_videos_folder: Folder containing base videos
        overlay_video: Single overlay video for all
        overlay_audio: Single overlay audio for all
        preset: Preset to use
        output_root: Root output directory

    Returns:
        Configured BatchProcessor
    """
    videos = discover_videos_in_folder(base_videos_folder)

    if not videos:
        print(f"⚠️  No videos found in {base_videos_folder}")

    processor = BatchProcessor(preset, output_root, max_workers=2)

    for video in videos:
        processor.add_job(video, overlay_video, overlay_audio, preset)

    print(f"📦 Created batch with {len(processor.jobs)} jobs")

    return processor
