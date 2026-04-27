# ClipPilot Lite Backend - Quick Start Guide

## 5-Minute Setup

### 1. Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

### 2. Set Up Environment
```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env and add your keys:
# - SUPABASE_URL and keys (from Supabase dashboard)
# - ANTHROPIC_API_KEY (from console.anthropic.com)
# - RUNWAY_API_KEY (from runwayml.com)
# - ELEVENLABS_API_KEY (from elevenlabs.io)
# - DEEPGRAM_API_KEY (from deepgram.com)
# - REDIS_URL (default: redis://localhost:6379)
```

### 3. Database Setup
```bash
# Log into Supabase dashboard
# Go to SQL Editor
# Copy/paste contents of DATABASE_SCHEMA.sql
# Execute

# Create storage buckets:
# 1. Go to Storage
# 2. Create bucket named "videos" (public)
# 3. Create bucket named "audio" (public)
# 4. Upload mood_calm.mp3, mood_inspiring.mp3, mood_upbeat.mp3,
#    mood_dramatic.mp3, mood_playful.mp3 to the "audio" bucket
```

### 4. Install Python Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Start Redis (if not already running)
```bash
# If using Redis locally
redis-server

# Or use cloud Redis (update REDIS_URL in .env)
```

### 6. Run FastAPI Server
```bash
# Terminal 1: Start API server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Visit http://localhost:8000/docs for interactive API documentation
```

### 7. Run ARQ Worker (separate terminal)
```bash
# Terminal 2: Start job worker
python worker.py
```

## Test the API

### 1. Get Health Status
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 2. Create a Job (requires auth token)
First, get a JWT token from your Supabase authentication.

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How photosynthesis works",
    "style": "educational",
    "duration": 30,
    "include_narration": true,
    "include_captions": true,
    "include_music": true
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Video generation queued"
}
```

### 3. Check Job Status
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/jobs/550e8400-e29b-41d4-a716-446655440000
```

Watch the progress increase as the worker processes the video.

### 4. Get Completed Video
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/jobs/550e8400-e29b-41d4-a716-446655440000/result
```

When status is "completed", you'll get the video URL.

## Understanding the Pipeline

The video generation process has these steps (automatic, no manual intervention needed):

1. **Guardrail Check (10%)** - Ensures topic is 12+ appropriate
2. **Research (10%)** - Claude researches the topic
3. **Script (25%)** - Claude generates a timed script with scenes
4. **Review (35%)** - Claude reviews script quality (up to 2 revisions)
5. **Shot List (50%)** - Creates visual prompts for video generation
6. **Video (75%)** - Runway generates video scenes
7. **Narration (75%)** - ElevenLabs generates speech audio
8. **Captions (80%)** - Deepgram transcribes and creates SRT
9. **Assembly (90%)** - FFmpeg combines video + audio + captions + disclaimer
10. **Upload (95%)** - Saves to Supabase Storage
11. **Complete (100%)** - Done!

Each step is tracked in the job status (visible via GET /api/jobs/{job_id}).

## File Structure Quick Reference

```
backend/
├── app/main.py              # FastAPI app entry point
├── app/config.py            # Environment configuration
├── app/routes/
│   ├── health.py           # Health check
│   ├── jobs.py             # Video jobs CRUD
│   └── auth.py             # User profiles
├── app/agents/             # AI agents (5 different)
├── app/services/           # External service integrations
├── app/middleware/         # Auth & rate limiting
├── app/worker/
│   └── tasks.py            # Main video processing task
├── worker.py               # ARQ worker entry point
├── requirements.txt        # Python dependencies
└── .env.example            # Copy to .env
```

## Common Commands

```bash
# Check if Redis is running
redis-cli ping

# View Redis queue depth
redis-cli LLEN arq:queue

# Check active jobs
redis-cli KEYS "arq:job:*"

# Watch logs in real-time
tail -f logs/app.log

# Format code
black app/ worker.py

# Check for errors
flake8 app/ worker.py
```

## Troubleshooting

### "Connection refused" (Redis)
- Start Redis: `redis-server`
- Or update REDIS_URL to cloud Redis in .env

### "Supabase auth failed"
- Verify SUPABASE_URL and keys in .env
- Check that JWT token is valid
- Ensure RLS policies are set up (DATABASE_SCHEMA.sql)

### "FFmpeg not found"
- Install FFmpeg (see step 1 above)
- Verify it's in PATH: `ffmpeg -version`

### Worker not picking up jobs
- Verify worker.py is running
- Check Redis connection: `redis-cli ping`
- Check logs for errors: `python worker.py`

### Jobs stuck in "processing"
- Worker may have crashed, restart it
- Check job timeout (JOB_TIMEOUT_SECONDS in .env)
- Check external API status (Runway, ElevenLabs, etc.)

## Next Steps

1. Connect to Supabase for authentication
2. Build frontend to use the API
3. Configure rate limits for your use case
4. Set up monitoring and alerting
5. Deploy to production (see deployment docs)

## Documentation

- API docs: http://localhost:8000/docs (interactive)
- Full README: ./README.md
- Database schema: ./DATABASE_SCHEMA.sql
- Configuration: .env.example

## Support

Check logs for detailed error messages:
```bash
# JSON-structured logs with timestamps and context
python -m uvicorn app.main:app --log-level debug
```
