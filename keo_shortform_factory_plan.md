# Keo Shortform Factory -- Build Plan

## 0) Outcome & Constraints

-   **Goal:** Given (A) long-form video, (B) overlay video, (C) overlay
    audio → auto-align audio → replace base audio → composite overlay →
    slice to many clips → export in desired aspect ratio (9:16, 1:1, or
    16:9).
-   **Constraints:** Local/offline; deterministic; fast enough for batch
    runs; reproducible via config.

------------------------------------------------------------------------

## 1) Architecture (MVP → Pro)

**Core stack:** Python + `ffmpeg/ffprobe`, `librosa` (alignment),
`numpy`, `whisper` (optional captions), `pyscenedetect` (optional
scenes).

**Modules** 1. `io/`\
- loaders, path validation, media probe (duration, fps, resolution). 2.
`audio/`\
- extract base audio (ffmpeg), normalize overlay to target LUFS,
onset-based cross-correlation alignment, time-shift. 3. `video/`\
- audio replacement (map new AAC), overlay composite (position,
opacity), safe-area padding. 4. `cutting/`\
- fixed-window slicer (len/stride), optional scene detector, optional
"hook finder". 5. `export/`\
 - single-ratio exporter (scale+crop), quality ladder (archive master +
 social). 6. `captions/` (optional)\
- Whisper transcription → styled burn-in. 7. `cli/`\
- Typer/argparse front-end, config presets, dry-run logging.

**Data flow**

    base.mp4 ──extract audio──► base.wav
    overlay_audio.wav ──loudnorm──► overlay_norm.wav
    (base.wav, overlay_norm.wav) ──align──► shift_sec
    overlay_norm.wav ──time-shift──► overlay_shifted.wav
    (base.mp4 + overlay_shifted.wav) ──replace audio──► video_audio.mp4
    (video_audio.mp4 + overlay_video.mov) ──composite──► master.mp4
    master.mp4 ──slice──► clips_src/*.mp4 ──export ratio──► exports/{ratio}/*.mp4

------------------------------------------------------------------------

## 2) MVP Scope (Week 1 build)

**Must-have** - CLI with 3 inputs (+ out_dir).\
- Onset-based alignment with confidence.\
- Audio replacement; overlay composite (5 positions + opacity).\
- Fixed-window slicing (len/stride).\
- Single-ratio export (center-crop).\
- Logs + manifest JSON.

**Done when** - One command processes a long video end-to-end with 0
manual steps. - Outputs at least 30 clips in 9:16 ready for upload.

------------------------------------------------------------------------

## 3) Detailed Steps

### 3.1 Project Scaffold

    shortform_factory/
      pyproject.toml (or requirements.txt)
      src/
        cli.py
        config.py
        utils.py
        io_ops.py
        audio_align.py
        video_ops.py
        cutter.py
        exporter.py
        captions.py   (later)
        scenes.py     (later)
      presets/
        tiktok_vertical.yaml
        reels_square.yaml
      tests/
      README.md

### 3.2 Config (YAML)

``` yaml
# presets/tiktok_vertical.yaml
target_lufs: -14
overlay:
  position: top-right   # top-left, top-right, bottom-left, bottom-right, center or "x,y"
  opacity: 0.9
  margin_px: 24
slicing:
  clip_len: 20
  stride: 18
  min_conf: 0.15
export:
  ratio: "9:16"
  ladder:
    - {codec: "libx264", crf: 20, preset: "veryfast"}   # social
    - {codec: "prores_ks", profile: 3}                  # archive (optional)
```

### 3.3 Alignment Algorithm (MVP)

-   Extract base audio @ 48k mono.
-   Compute onset envelopes (librosa) for base and overlay, z-score
    normalize.
-   Cross-correlate → lag → seconds (hop/sr).
-   Confidence = peak / (\|\|ref\|\|·\|\|tgt\|\|).\
-   If `conf < min_conf`, fall back to 0 offset; log warning.
-   Time-shift overlay with `adelay` (positive) or `-ss` trim
    (negative).

**Edge cases to handle** - Overlay shorter than base (allowed).\
- Drift: assume negligible for now; if needed later, add **piecewise
DTW**.

### 3.4 Video Compose (MVP)

-   Replace audio:
    `ffmpeg -map 0:v -map 1:a -c:v copy -c:a aac -shortest`.
-   Overlay:
    `format=rgba,colorchannelmixer=aa={opacity},overlay=x={x}:y={y}`.
-   Safe-area (later): add `pad` or `drawbox` guides if needed.

### 3.5 Slicing (MVP)

-   Fixed window generator:
    `starts = np.arange(0, dur-clip_len, stride)`.
-   Fast cut: `-ss x -to y -c copy` into `clips_src/`.

### 3.6 Exporter (MVP)

-   Dynamic ratio export based on config (9:16, 1:1, or 16:9).\
-   9:16: `scale=-1:1920,crop=1080:1920`.\
-   1:1: `scale=1920:-1,crop=1080:1080`.\
-   16:9: `scale=1920:-1,setsar=1`.\
-   Audio copy from clip (already aligned).

------------------------------------------------------------------------

## 4) V1 Enhancements (Week 2)

1.  **Scene-augmented slicing:**
    -   Use `pyscenedetect` to propose cut points; merge with windows.\
    -   Keep min gap; limit total clips.
2.  **Hook finder (speech/energy):**
    -   Compute short-term energy + voice activity; bias starts to
        peaks.
3.  **Captioning (optional):**
    -   Whisper → SRT/VTT → burn-in with style preset (font, color,
        stroke).
4.  **Crop intelligence:**
    -   Face/subject tracking (e.g., `mediapipe`) to center 9:16 crop.

------------------------------------------------------------------------

## 5) V2 Power Features (Week 3+)

-   **Batch mode:** process folder of base videos; inheritance of
    preset.\
-   **GUI wrapper:** minimal web UI (FastAPI + htmx) or Tauri desktop.\
-   **Quality ladder in one run:** master (ProRes) + social (H.264).\
-   **Template packs:** different overlays, watermarks, LUTs per
    preset.\
-   **Auto-upload hooks (manual review):** move finished clips to
    "Ready/Platform" folders with filename conventions.

------------------------------------------------------------------------

## 6) CLI Design (Typer/argparse)

    shortform   --base "/in/long.mp4"   --overlay-video "/in/overlay.mov"   --overlay-audio "/in/overlay.wav"   --out "/out/session_001"   --preset "presets/tiktok_vertical.yaml"   --clip-len 20 --clip-stride 18   --scene-detect false --min-conf 0.15   --ratio 9:16   --position top-right --opacity 0.9

-   `--dry-run`: print plan + durations, no renders.\
-   `--manifest`: write JSON summary (alignment offset, conf, clip list,
    exports).

------------------------------------------------------------------------

## 7) Testing & QA

**Golden fixture**\
- 2--3 known long-form videos + overlay audio with known offset.\
- Assert alignment within ±50 ms at `conf ≥ min_conf`.\
- Check clip counts = expected from len/stride.\
- Verify exports exist for each ratio; spot-check sync.

**Performance** - Use `-c copy` wherever possible (cuts).\
- For overlays/ratio exports, default `-preset veryfast`, allow
override.\
- Parallelize exports via Python `concurrent.futures` (per clip/per
ratio).

------------------------------------------------------------------------

## 8) Naming & Folder Strategy

    out/
      session_YYYYmmdd_HHMMSS/
        manifest.json
        master.mp4
        clips_src/
          clip_000000_000020.mp4
          ...
        exports/
          9x16/

-   Filenames = `clip_{start}_{end}.mp4` to preserve ordering (ratio determined by config).

------------------------------------------------------------------------

## 9) Brand Defaults (so you never fiddle)

-   **Fonts:** set your caption font + fallback.\
-   **Colors:** hex for primary/secondary + stroke thickness.\
-   **Watermark:** bottom-right, 16px margin, 70% opacity.\
-   **Safe areas:** reserved top/bottom to avoid platform UI overlays.

Put these in `presets/keo_brand.yaml` and forget them.

------------------------------------------------------------------------

## 10) Risks & Mitigations

-   **Low alignment confidence:** fall back to 0 offset + log; expose
    `--nudge ±ms` to hand-tweak.\
-   **Desync drift:** if detected (low conf after mid-segment check),
    switch to **segmental alignment** (windowed offsets).\
-   **Overlay alpha issues:** ensure overlay video has premultiplied
    alpha or add `format=rgba` step.

------------------------------------------------------------------------

## 11) Immediate Next Actions (practical)

1.  Create repo + scaffold from section 3.1.\
2.  Add `ffprobe` duration + audio extract utils.\
3.  Implement alignment (onset + confidence).\
4.  Wire audio replace → overlay → windows → single-ratio export.\
5.  Ship **MVP preset** (`presets/tiktok_vertical.yaml`) with your brand
    defaults.
