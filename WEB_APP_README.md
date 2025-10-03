# Keo Shortform Factory - Full Stack Application

## Overview

A complete full-stack application for automated short-form video creation with audio alignment, overlay compositing, and intelligent clip generation.

## Architecture

### Backend (Python CLI)
- **MVP Features**: Audio alignment, overlay compositing, fixed-window slicing, multi-ratio export
- **V1 Enhancements**: Scene detection, hook finder, caption generation (Whisper)
- **V2 Features**: Batch processing, parallel export, quality ladder

### Frontend (React + TypeScript + Vite)
- Modern React 18 with TypeScript
- Tailwind CSS for styling
- React Router for navigation
- Supabase for authentication and database

### Database (Supabase/PostgreSQL)
- Users table with RLS
- Presets for configuration management
- Processing jobs with status tracking
- Output clips with metadata

## Project Structure

```
project/
├── src/                    # Python backend
│   ├── cli.py             # CLI with V1/V2 features
│   ├── audio_align.py     # Audio alignment
│   ├── video_ops.py       # Video operations
│   ├── cutter.py          # Clip slicing
│   ├── exporter.py        # Multi-ratio export
│   ├── scenes.py          # V1: Scene detection
│   ├── hook_finder.py     # V1: Hook detection
│   ├── captions.py        # V1: Whisper captions
│   └── batch_processor.py # V2: Batch processing
│
├── web/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── Layout.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── NewJob.tsx
│   │   │   ├── JobDetail.tsx
│   │   │   └── Presets.tsx
│   │   ├── lib/
│   │   │   └── supabase.ts
│   │   └── App.tsx
│   ├── tailwind.config.js
│   └── package.json
│
└── presets/               # Preset configurations
    └── tiktok_vertical.yaml
```

## Features Implemented

### Python Backend

#### MVP Features
- ✅ Audio alignment with onset-based cross-correlation
- ✅ Confidence scoring and fallback handling
- ✅ Audio replacement and overlay compositing
- ✅ Fixed-window video slicing
- ✅ Multi-ratio export (9:16, 1:1, 16:9)
- ✅ Manifest generation

#### V1 Enhancements
- ✅ Scene detection using FFmpeg analysis
- ✅ Scene-augmented clip generation
- ✅ Hook finder with audio energy analysis
- ✅ Voice activity detection
- ✅ Caption generation with Whisper
- ✅ Caption burn-in with styling

#### V2 Features
- ✅ Batch processor for multiple videos
- ✅ CSV-based batch job loading
- ✅ Folder-based batch processing
- ✅ Parallel job execution with ThreadPoolExecutor
- ✅ Batch manifest generation

### Frontend (Web Application)

#### Core Features
- ✅ User authentication (sign up/sign in/sign out)
- ✅ Protected routes with auth middleware
- ✅ Dashboard with job statistics
- ✅ Recent jobs list with status indicators
- ✅ Job creation form with configuration
- ✅ Job detail view with clips gallery
- ✅ Preset management interface
- ✅ Responsive design with Tailwind CSS

#### UI/UX Features
- ✅ Modern, clean interface design
- ✅ Smooth animations and transitions
- ✅ Loading states
- ✅ Error handling
- ✅ Form validation
- ✅ Status badges and progress indicators

### Database Schema

#### Tables
- **users**: User profiles (extends auth.users)
- **presets**: Reusable configuration presets
- **processing_jobs**: Video processing jobs with status tracking
- **output_clips**: Generated clips with metadata

#### Security
- Row Level Security (RLS) enabled on all tables
- Users can only access their own data
- Public presets are readable by all authenticated users
- Secure foreign key relationships

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- FFmpeg and ffprobe
- Supabase account (already configured)

### Backend Setup

```bash
# Install Python dependencies
pip install -e .

# For V1 features (optional)
pip install -e ".[captions,scenes]"

# Run CLI
shortform --help

# Example usage
shortform \
  --base video.mp4 \
  --overlay-video overlay.mov \
  --overlay-audio music.wav \
  --out output/ \
  --scene-detect \
  --hook-detect \
  --captions

# Batch processing
shortform batch \
  --folder videos/ \
  --overlay-video overlay.mov \
  --overlay-audio music.wav \
  --out batch_output/ \
  --workers 4
```

### Frontend Setup

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Environment Variables

The `.env` file is already configured with Supabase credentials:
```
VITE_SUPABASE_URL=https://tkksxqvzmladxhzzlcyt.supabase.co
VITE_SUPABASE_ANON_KEY=[configured]
```

## CLI Commands

### Single Video Processing
```bash
shortform process \
  --base <video> \
  --overlay-video <overlay> \
  --overlay-audio <audio> \
  --out <output_dir> \
  [--scene-detect] \
  [--hook-detect] \
  [--captions] \
  [--clip-len 20] \
  [--ratio 9:16]
```

### Batch Processing
```bash
# From folder
shortform batch \
  --folder <videos_folder> \
  --overlay-video <overlay> \
  --overlay-audio <audio> \
  --out <output_dir> \
  --workers 4

# From CSV
shortform batch \
  --csv jobs.csv \
  --out <output_dir> \
  --workers 4
```

## Configuration Presets

Presets are YAML files in `presets/` directory:

```yaml
target_lufs: -14
overlay:
  position: top-right
  opacity: 0.9
  margin_px: 24
slicing:
  clip_len: 20
  stride: 18
  min_conf: 0.15
  scene_detect: false
  hook_detect: false
captions:
  enabled: false
  model: base
  language: en
export:
  ratio: "9:16"
  quality_ladder:
    - codec: libx264
      crf: 20
      preset: veryfast
```

## API Endpoints (To Be Implemented)

The following Supabase Edge Functions need to be created for full web functionality:

1. **upload-video**: Handle video file uploads to Supabase Storage
2. **process-job**: Trigger Python CLI processing for a job
3. **job-status**: Poll job status and progress
4. **generate-thumbnails**: Create thumbnail images for clips

## Next Steps

### Immediate
1. Implement file upload to Supabase Storage
2. Create Edge Functions for job processing
3. Add real-time progress updates with Supabase Realtime
4. Implement drag-and-drop file upload

### Future Enhancements
1. Video preview player in web UI
2. Clip editing and trim interface
3. Bulk download of clips
4. Social media direct publishing
5. Template marketplace
6. Collaborative preset sharing
7. Analytics dashboard
8. Webhook integrations

## Technology Stack

### Backend
- Python 3.8+
- FFmpeg for video processing
- Librosa for audio analysis
- Whisper for speech-to-text (optional)
- Typer for CLI interface

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Supabase JS Client

### Infrastructure
- Supabase (PostgreSQL + Auth + Storage + Edge Functions)
- Row Level Security for data protection

## Database Queries Examples

### Fetch User Jobs
```typescript
const { data } = await supabase
  .from('processing_jobs')
  .select('*')
  .eq('user_id', user.id)
  .order('created_at', { ascending: false });
```

### Create New Job
```typescript
const { data } = await supabase
  .from('processing_jobs')
  .insert([{
    user_id: user.id,
    status: 'pending',
    config: { /* job config */ }
  }])
  .select()
  .single();
```

### Fetch Job Clips
```typescript
const { data } = await supabase
  .from('output_clips')
  .select('*')
  .eq('job_id', jobId)
  .order('clip_number');
```

## Performance Considerations

1. **Video Processing**: CPU-intensive, runs on backend
2. **Batch Jobs**: Parallel processing with configurable workers
3. **File Storage**: Use Supabase Storage for large files
4. **Progress Updates**: Real-time subscriptions for live progress
5. **Thumbnails**: Generate on upload for faster preview

## Security

1. **Authentication**: Supabase Auth with email/password
2. **Authorization**: RLS policies enforce user data isolation
3. **File Access**: Signed URLs for private storage
4. **API Keys**: Server-side only, never exposed to client

## Deployment

### Backend
- Deploy as Python service on any cloud platform
- Ensure FFmpeg is available in runtime
- Configure environment variables for Supabase

### Frontend
- Build: `npm run build`
- Deploy to Vercel, Netlify, or any static hosting
- Set environment variables for Supabase

## License

See LICENSE file for details.

## Support

For issues, questions, or feature requests, please use the project's issue tracker.
