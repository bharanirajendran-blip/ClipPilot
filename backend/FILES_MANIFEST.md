# ClipPilot Lite Backend - Files Manifest

Complete list of all production-ready backend files created.

## Project Root Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python package dependencies (FastAPI, Supabase, Redis, ARQ, etc.) |
| `.env.example` | Environment variable template (copy to .env) |
| `worker.py` | ARQ worker entry point for async job processing |
| `DATABASE_SCHEMA.sql` | PostgreSQL schema for Supabase |
| `README.md` | Full documentation and setup guide |
| `QUICKSTART.md` | 5-minute quick start guide |
| `ARCHITECTURE.md` | Detailed system architecture and design |
| `FILES_MANIFEST.md` | This file - complete file listing |

## Application Code Structure

```
app/
├── __init__.py
├── main.py                          # FastAPI application entry point
├── config.py                        # Pydantic Settings from environment
│
├── models/
│   ├── __init__.py
│   └── schemas.py                   # Pydantic request/response models
│
├── middleware/
│   ├── __init__.py
│   ├── auth.py                      # JWT authentication dependency
│   └── rate_limit.py                # Rate limiting (user lifetime + daily global)
│
├── routes/
│   ├── __init__.py
│   ├── health.py                    # GET /health endpoint
│   ├── jobs.py                      # Video job CRUD endpoints
│   └── auth.py                      # User profile endpoints
│
├── services/
│   ├── __init__.py
│   ├── guardrails.py                # Content safety using Claude
│   ├── runway_service.py            # Runway Gen-3 video generation
│   ├── elevenlabs_service.py        # ElevenLabs TTS
│   ├── deepgram_service.py          # Deepgram speech-to-text
│   ├── ffmpeg_service.py            # FFmpeg video processing
│   └── storage_service.py           # Supabase Storage uploads
│
├── agents/
│   ├── __init__.py
│   ├── base.py                      # Base agent class
│   ├── research_agent.py            # Research & fact gathering
│   ├── script_agent.py              # Script generation
│   ├── shot_list_agent.py           # Visual prompt generation
│   ├── review_agent.py              # Quality assurance & revision
│   └── metadata_agent.py            # Title, description, tags
│
├── worker/
│   ├── __init__.py
│   ├── tasks.py                     # Main video processing pipeline task
│   └── settings.py                  # ARQ worker configuration
│
└── utils/
    ├── __init__.py
    ├── logger.py                    # Structured JSON logging
    └── srt.py                       # SRT subtitle formatting
```

## File Count Summary

- **Python files**: 33
- **Configuration files**: 2 (.env.example, config.py)
- **Documentation files**: 4 (README.md, QUICKSTART.md, ARCHITECTURE.md, this file)
- **Database files**: 1 (DATABASE_SCHEMA.sql)
- **Dependency files**: 1 (requirements.txt)
- **Entry points**: 2 (app/main.py, worker.py)
- **Total files**: 43

## Core Functionality by Component

### API Server (main.py + routes)
- Health check endpoint
- Job creation with validation and rate limiting
- Job status polling with progress tracking
- Job result retrieval (videos + metadata)
- Job listing with pagination
- User profile creation and retrieval
- JWT authentication
- CORS support
- Exception handling
- Request logging

### AI Agents (5 specialized Claude agents)
1. **Research Agent** - Gathers facts, statistics, narrative angles
2. **Script Agent** - Creates timed scripts with visual descriptions
3. **Shot List Agent** - Optimizes visual prompts for Runway
4. **Review Agent** - Quality assurance with revision loops
5. **Metadata Agent** - Generates SEO-optimized titles, descriptions, tags

### Video Processing Pipeline (worker/tasks.py)
- Multi-step orchestration (12 processing steps)
- Progress tracking and updates
- Content safety checks (input + output)
- Runway video generation
- ElevenLabs speech synthesis
- Deepgram audio transcription
- FFmpeg video assembly
- Thumbnail creation
- Supabase Storage uploads
- Graceful error handling and degradation

### External Service Integrations
- **Runway Gen-3 Alpha Turbo** - Video generation with polling
- **ElevenLabs Turbo v2.5** - Text-to-speech with voice selection
- **Deepgram Nova-2** - Speech-to-text with word-level timestamps
- **FFmpeg** - Video/audio/subtitle processing
- **Supabase** - Authentication, database, storage
- **Anthropic Claude** - Multi-agent AI pipeline

### Security & Compliance
- JWT authentication with Supabase
- 12+ audience guardrails
- Content safety classification
- Rate limiting (per-user lifetime + global daily)
- Row-Level Security (RLS) on database
- Family-friendly disclaimer auto-burning
- Graceful error messages (no sensitive data exposed)

### Infrastructure
- FastAPI async web framework
- Redis + ARQ for job queue
- Supabase PostgreSQL for persistence
- Structured JSON logging
- Environment-based configuration
- Graceful startup/shutdown

## Design Principles

### Code Quality
- No placeholders or TODOs
- Complete error handling throughout
- Comprehensive type hints
- Pydantic validation on all inputs
- Structured logging with context
- Clear separation of concerns

### Production-Ready
- Environment-based configuration
- Graceful degradation (non-critical failures continue)
- Timeout handling
- Connection pooling
- Rate limiting
- Security best practices
- Comprehensive documentation

### Scalability
- Async/await throughout
- Queue-based job processing
- Horizontal scaling support
- No hard-coded state
- Cloud-native design

### Maintainability
- Modular architecture
- Service layer abstraction
- Agent-based AI pattern
- Clear naming conventions
- Comprehensive documentation
- Example configurations

## Testing Checklist

Before deployment, verify:

- [ ] All Python files parse without syntax errors
- [ ] Environment variables are set (.env file)
- [ ] Supabase database schema is created
- [ ] Redis is accessible
- [ ] FFmpeg is installed and in PATH
- [ ] All API keys are valid
- [ ] Health endpoint responds
- [ ] Auth middleware validates tokens correctly
- [ ] Rate limiting works
- [ ] Job creation succeeds
- [ ] Worker processes jobs
- [ ] External services integrate properly
- [ ] Video generation completes
- [ ] Videos upload to storage
- [ ] Logs are properly formatted

## Documentation Files

1. **README.md** - Complete setup, API documentation, troubleshooting
2. **QUICKSTART.md** - 5-minute quick start with test curl commands
3. **ARCHITECTURE.md** - System design, data flow, components
4. **FILES_MANIFEST.md** - This file
5. **DATABASE_SCHEMA.sql** - Database structure with RLS policies
6. **.env.example** - Environment variable template

## Key File Dependencies

```
main.py
  ├─ config.py (reads environment)
  ├─ routes/ (all route handlers)
  ├─ middleware/ (auth and rate limiting)
  ├─ services/ (external integrations)
  └─ utils/ (logging)

routes/jobs.py
  ├─ models/schemas.py (request/response validation)
  ├─ middleware/auth.py (user authentication)
  ├─ middleware/rate_limit.py (rate limiting)
  ├─ services/guardrails.py (content safety)
  └─ services/storage_service.py (uploads)

worker/tasks.py
  ├─ agents/ (research, script, review, shot list, metadata)
  ├─ services/ (guardrails, runway, elevenlabs, deepgram, ffmpeg, storage)
  ├─ utils/srt.py (subtitle formatting)
  └─ utils/logger.py (logging)

agents/*.py
  ├─ agents/base.py (shared Claude client)
  └─ config.py (API keys)

services/*.py
  └─ config.py (API keys and URLs)
```

## Configuration Reference

### Required Environment Variables
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_ANON_KEY
REDIS_URL
ANTHROPIC_API_KEY
RUNWAY_API_KEY
ELEVENLABS_API_KEY
DEEPGRAM_API_KEY
```

### Optional Environment Variables
```
APP_ENV (development|production)
LOG_LEVEL (DEBUG|INFO|WARNING|ERROR)
BACKEND_CORS_ORIGINS (comma-separated URLs)
MAX_VIDEOS_PER_USER (default: 2)
MAX_VIDEOS_PER_DAY_GLOBAL (default: 20)
JOB_TIMEOUT_SECONDS (default: 600)
RUNWAY_POLL_INTERVAL (default: 5)
RUNWAY_MAX_RETRIES (default: 60)
ANTHROPIC_MODEL (default: claude-3-5-haiku-20241022)
ELEVENLABS_VOICE_ID (default: 21m00Tcm4TlvDq8ikWAM)
ELEVENLABS_MODEL_ID (default: eleven_turbo_v2_5)
```

## API Endpoints Summary

### Health
- `GET /health` - Health check

### Jobs
- `POST /api/jobs` - Create job
- `GET /api/jobs/{job_id}` - Get status
- `GET /api/jobs/{job_id}/result` - Get result
- `GET /api/jobs` - List user's jobs

### Auth
- `POST /api/auth/profile` - Get/create user profile

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python -m uvicorn app.main:app --reload

# Run ARQ worker
python worker.py

# Format code
black app/ worker.py

# Lint code
flake8 app/ worker.py

# Type check
mypy app/

# Run tests (if configured)
pytest
```

## Deployment Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Set all environment variables
- [ ] Create Supabase project
- [ ] Run DATABASE_SCHEMA.sql
- [ ] Create "videos" storage bucket
- [ ] Install FFmpeg on server
- [ ] Install Python dependencies
- [ ] Set up Redis (local or managed)
- [ ] Start FastAPI server
- [ ] Start ARQ worker
- [ ] Test /health endpoint
- [ ] Monitor logs
- [ ] Set up alerts for errors
- [ ] Configure backups
- [ ] Set up rate limiting appropriately

## Support

For detailed information, see:
- Full documentation: README.md
- Quick setup: QUICKSTART.md
- System design: ARCHITECTURE.md
- Database: DATABASE_SCHEMA.sql
