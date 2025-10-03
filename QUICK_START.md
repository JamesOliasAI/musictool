# Keo Shortform Factory - Quick Start Guide

## 🎬 What You Got

A complete video processing system with:
- **Python CLI** with scene detection, hook finding, and caption generation
- **React Web App** with authentication, job management, and dashboard
- **Supabase Database** with secure user data and job tracking

## ⚡ 5-Minute Setup

### 1. Install Python Backend

```bash
# Install core dependencies
pip install -e .

# Install V1 features (optional but recommended)
pip install -e ".[captions,scenes]"
```

### 2. Test Python CLI

```bash
# Show all commands
shortform --help

# Test with placeholder
shortform process \
  --base /path/to/video.mp4 \
  --overlay-video /path/to/overlay.mov \
  --overlay-audio /path/to/music.wav \
  --out ./output/ \
  --scene-detect \
  --hook-detect
```

### 3. Start Web App

```bash
# Go to web directory
cd web

# Install dependencies (if not done)
npm install

# Start development server
npm run dev

# Open browser to http://localhost:5173
```

### 4. Create Your First Account

1. Open http://localhost:5173
2. Click "Don't have an account? Sign up"
3. Enter email and password
4. Sign up
5. You're in!

## 🎯 Features You Can Use Now

### Python CLI - Ready to Use ✅

#### Single Video Processing
```bash
shortform process \
  --base long_video.mp4 \
  --overlay-video face_cam.mov \
  --overlay-audio music.wav \
  --out ./output/ \
  --clip-len 20 \
  --ratio 9:16 \
  --scene-detect \
  --hook-detect \
  --captions
```

#### Batch Processing
```bash
# Process all videos in a folder
shortform batch \
  --folder ./videos/ \
  --overlay-video face_cam.mov \
  --overlay-audio music.wav \
  --out ./batch_output/ \
  --workers 4
```

### Web App - Dashboard Ready ✅

#### What Works
- ✅ User sign up and login
- ✅ Dashboard with job stats
- ✅ Job creation form (placeholder uploads)
- ✅ Job detail view
- ✅ Preset management
- ✅ Responsive design

#### What Needs Integration
- ⏭ Actual file upload to Supabase Storage
- ⏭ Trigger Python processing from web
- ⏭ Real-time progress updates
- ⏭ Video preview player

## 📚 Common Commands

### Python CLI

```bash
# Show help
shortform --help
shortform batch --help

# Dry run (no processing)
shortform process --dry-run \
  --base video.mp4 \
  --overlay-video overlay.mov \
  --overlay-audio music.wav \
  --out test/

# With all V1 features
shortform process \
  --base video.mp4 \
  --overlay-video overlay.mov \
  --overlay-audio music.wav \
  --out output/ \
  --scene-detect \
  --hook-detect \
  --captions \
  --preset presets/tiktok_vertical.yaml

# Batch from CSV
shortform batch \
  --csv jobs.csv \
  --out batch_output/ \
  --workers 2
```

### Web App

```bash
# Development
cd web && npm run dev

# Build for production
cd web && npm run build

# Preview production build
cd web && npm run preview
```

## 🔍 Understanding the Flow

### Current Flow (Python CLI)
1. You provide: base video + overlay video + overlay audio
2. System aligns audio using onset detection
3. System replaces base audio with aligned overlay
4. System composites overlay video on base
5. System slices into clips (scene/hook aware)
6. System exports to multiple ratios
7. You get: 20-30+ ready-to-post clips

### Future Flow (Web App - After Integration)
1. Upload videos through web interface
2. Configure settings in UI
3. Click "Create Job"
4. Watch real-time progress
5. Preview and download clips
6. Share or publish directly

## 🎨 Customizing Presets

Edit `presets/tiktok_vertical.yaml` or create your own:

```yaml
target_lufs: -14

overlay:
  position: top-right  # or: top-left, bottom-left, bottom-right, center
  opacity: 0.9
  margin_px: 24

slicing:
  clip_len: 20        # Length of each clip
  stride: 18          # Overlap between clips
  scene_detect: true  # Use scene detection
  hook_detect: true   # Find engaging moments

captions:
  enabled: true       # Generate captions
  model: base         # Whisper model size
  language: en

export:
  ratio: "9:16"       # 9:16, 1:1, or 16:9
  quality_ladder:
    - codec: libx264
      crf: 20
      preset: veryfast
```

## 🐛 Troubleshooting

### Python CLI

**Issue**: "ffmpeg not found"
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Check installation
ffmpeg -version
```

**Issue**: "Module not found"
```bash
# Reinstall with all features
pip install -e ".[captions,scenes]"
```

### Web App

**Issue**: "Cannot connect to Supabase"
- Check `.env` file exists in `web/` directory
- Verify Supabase URL and key are correct

**Issue**: "Build fails"
```bash
# Clean and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📖 Next Steps

### Learn More
1. Read `PROJECT_SUMMARY.md` for complete overview
2. Read `WEB_APP_README.md` for web app details
3. Read original `README.md` for Python CLI details

### Extend the System
1. Create custom presets for different platforms
2. Experiment with scene and hook detection
3. Try batch processing on multiple videos
4. Customize Tailwind theme in web app

### Integrate File Upload (Advanced)
1. Set up Supabase Storage buckets
2. Create Edge Functions for processing
3. Connect frontend uploads to backend
4. Add real-time progress tracking

## 🎓 Examples

### Example 1: Gaming Highlights
```bash
shortform process \
  --base gameplay.mp4 \
  --overlay-video facecam.mov \
  --overlay-audio commentary.wav \
  --out gaming_clips/ \
  --hook-detect \
  --position bottom-right
```

### Example 2: Podcast Clips
```bash
shortform process \
  --base podcast_video.mp4 \
  --overlay-video logo.mov \
  --overlay-audio podcast_audio.wav \
  --out podcast_clips/ \
  --captions \
  --clip-len 45 \
  --ratio 1:1
```

### Example 3: Course Content
```bash
shortform process \
  --base lesson.mp4 \
  --overlay-video slides.mov \
  --overlay-audio narration.wav \
  --out lesson_clips/ \
  --scene-detect \
  --captions \
  --ratio 16:9
```

## 💬 Support

- Check documentation files in project root
- Review inline code comments
- Test with dry-run mode first
- Start with default settings

## 🚀 Production Deployment

### Backend
- Deploy Python service to any cloud platform (AWS, GCP, DigitalOcean)
- Ensure FFmpeg is installed in runtime
- Set Supabase credentials as environment variables
- Use queue system (Celery, RQ) for job processing

### Frontend
- Build: `cd web && npm run build`
- Deploy `web/dist/` folder to:
  - Vercel (recommended)
  - Netlify
  - AWS S3 + CloudFront
  - Any static hosting
- Set environment variables for Supabase

## ✅ Verification Checklist

- [ ] Python installed (3.8+)
- [ ] FFmpeg installed and in PATH
- [ ] Python dependencies installed
- [ ] Node.js installed (18+)
- [ ] Web dependencies installed
- [ ] Can run `shortform --help`
- [ ] Can access http://localhost:5173
- [ ] Can sign up and log in
- [ ] Can create a job (even with placeholders)
- [ ] Can view dashboard

---

**You're all set!** Start with the Python CLI to process some videos, then explore the web interface. The system is modular and extensible - add features as you need them.
