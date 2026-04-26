# ClipPilot Lite - Architecture & Design

## System Overview

ClipPilot Lite is a distributed system for generating short-form educational videos using AI. The backend orchestrates multiple services and AI agents to transform a single topic into a production-ready video.

```
User Request
    ↓
API Server (FastAPI)
    ↓ [Validation, Auth, Rate Limit]
    ↓
Job Queue (Redis + ARQ)
    ↓ [Async Processing]
Worker Process
    ↓ [Multi-Agent Pipeline]
    ↓
External Services (Runway, ElevenLabs, Deepgram, FFmpeg)
    ↓
Supabase Storage
    ↓
Video URL → User
```

## Component Architecture

### 1. API Server (FastAPI)

**Location**: `app/main.py`

Core responsibilities:
- HTTP request handling
- JWT authentication
- Request validation (Pydantic)
- CORS middleware
- Structured logging
- Error handling

Key features:
- Lifespan events for startup/shutdown
- Request logging middleware
- Exception handlers
- Multiple routers for separation of concerns

```
Incoming Request
    ↓
[CORS Middleware]
    ↓
[Request Logger]
    ↓
[Auth Middleware] → JWT Verification
    ↓
[Router] → Handler Function
    ↓
[Response] → Client
```

### 2. Authentication & Authorization

**Location**: `app/middleware/auth.py`

Flow:
1. Client sends JWT token in Authorization header
2. FastAPI extracts Bearer token
3. Token verified with Supabase
4. User ID extracted and passed to handlers
5. User ID available in dependency injection

```python
@router.get("/api/jobs")
async def list_jobs(user_id: str = Depends(get_current_user)):
    # Only process jobs for this specific user
    pass
```

### 3. Rate Limiting

**Location**: `app/middleware/rate_limit.py`

Two-level system:

**Per-User Lifetime**:
- Query Supabase `jobs` table
- Count jobs where `user_id = current_user`
- Compare against `MAX_VIDEOS_PER_USER` (default: 2)
- Raise 429 if exceeded

**Global Daily**:
- Use Redis counter key: `videos:daily:YYYY-MM-DD`
- Increment on job creation
- 24-hour TTL for automatic reset
- Compare against `MAX_VIDEOS_PER_DAY_GLOBAL` (default: 20)

Both checks run before job is queued.

### 4. Job Management

**Location**: `app/routes/jobs.py`

Endpoints:
- `POST /api/jobs` - Create job (validated, rate-limited)
- `GET /api/jobs/{id}` - Get status with progress
- `GET /api/jobs/{id}/result` - Get result URLs (when completed)
- `GET /api/jobs` - List user's jobs with pagination

Job states:
```
queued → processing → completed
                  ↓
                 failed
```

### 5. Guardrails (Content Safety)

**Location**: `app/services/guardrails.py`

Two checkpoints:

**Input Guardrail** (at job creation):
```
User Topic
    ↓
Claude Classification
    ↓
Categories: {safe, violence, explicit, hate_speech, dangerous, misinformation, ...}
    ↓
is_safe? → Proceed : Reject
```

**Output Guardrail** (after script generation):
```
Generated Script
    ↓
Claude Classification
    ↓
is_safe? → Proceed : Mark Job Failed
```

All guardrails enforce 12+ audience appropriateness.

### 6. AI Agents Pipeline

**Location**: `app/agents/`

Five specialized agents work sequentially:

#### Agent 1: Research Agent
- **Input**: Topic string
- **Output**: {key_facts, statistics, narrative_angles, interesting_details}
- **Purpose**: Gathers accurate information for video content
- **Model**: Claude Haiku (cost-effective)

```
Topic: "How solar panels work"
    ↓
Research
    ↓
{
  "key_facts": ["Convert sunlight to electricity", ...],
  "statistics": [{"stat": "8% of US electricity", "source": "..."}],
  "narrative_angles": ["Environmental impact", "Cost-benefit analysis"],
  ...
}
```

#### Agent 2: Script Agent
- **Input**: Topic, style, duration, research data
- **Output**: Timed script with scenes
- **Purpose**: Writes engaging narration and visual descriptions
- **Scene structure**: {scene_number, duration_seconds, narration, visual_description}

```
Script Output:
{
  "scenes": [
    {
      "scene_number": 1,
      "duration_seconds": 10,
      "narration": "Solar panels convert sunlight into electricity...",
      "visual_description": "Wide shot of solar panels on a rooftop..."
    },
    ...
  ]
}
```

#### Agent 3: Shot List Agent
- **Input**: Script from script agent
- **Output**: Runway Gen-3 optimized prompts
- **Purpose**: Converts scenes to visual generation prompts
- **Optimization**: Camera angles, lighting, visual styles for AI video generation

#### Agent 4: Review Agent
- **Input**: Script + shot list
- **Output**: Approval status + revision suggestions
- **Purpose**: Quality assurance and 12+ compliance
- **Loop**: Up to 2 revision cycles before proceeding

```
Script + ShotList
    ↓
Review
    ↓
approved = true? → Proceed : Request Revision
    ↓
revision_needed = true && revisions < 2? → Loop : Proceed Anyway
```

#### Agent 5: Metadata Agent
- **Input**: Topic, script
- **Output**: Title, description, tags, category
- **Purpose**: SEO optimization and discoverability

### 7. Video Generation Services

#### Runway Service
**Purpose**: Generate video scenes
**API**: Runway Gen-3 Alpha Turbo

Flow:
1. Create generation task with prompt
2. Poll for completion (every 5 seconds, max 60 retries)
3. Download video bytes when ready
4. Return video

```python
prompt = "Wide shot of solar panels converting sunlight..."
video_bytes = runway.generate_video(prompt, duration=10)
```

#### ElevenLabs Service
**Purpose**: Text-to-speech narration
**API**: ElevenLabs Turbo v2.5

Flow:
1. Extract full narration from script
2. Call TTS API with voice settings
3. Return audio bytes (MP3)

```python
narration = "Solar panels convert sunlight..."
audio = elevenlabs.generate_speech(narration)
```

#### Deepgram Service
**Purpose**: Speech-to-text for captions
**API**: Deepgram Nova-2

Flow:
1. Take audio bytes from ElevenLabs
2. Transcribe with word-level timestamps
3. Return list of {word, start, end}

```python
words = deepgram.transcribe_with_timestamps(audio_bytes)
# [{"word": "Solar", "start": 0.0, "end": 0.3}, ...]
```

#### FFmpeg Service
**Purpose**: Video assembly and processing

Operations:
1. **combine_video_audio**: Merge video + audio streams
2. **burn_captions**: Hardcode SRT subtitles
3. **add_disclaimer**: Burn disclaimer text at bottom
4. **create_thumbnail**: Extract frame as PNG
5. **get_video_duration**: Query video length

```
Input Video
    ↓
[Combine with Audio]
    ↓
[Burn Captions]
    ↓
[Add Disclaimer] → "Generated by ClipPilot..."
    ↓
Final Video
```

#### Storage Service
**Purpose**: Upload to Supabase Storage

Operations:
1. **upload_video**: Store MP4, return public URL
2. **upload_thumbnail**: Store PNG, return public URL
3. **delete_job_files**: Cleanup on error/retry

Bucket: `videos/`
Structure: `{job_id}/video.mp4`, `{job_id}/thumbnail.png`

### 8. Job Processing Worker

**Location**: `app/worker/tasks.py`

Main function: `process_video_job(ctx, job_id)`

Orchestration:
```
1. Get job details from Supabase (10%)
2. Research topic (10%) → research_agent
3. Generate script (25%) → script_agent
4. Review loop (35%) → review_agent, script_agent (up to 2 revisions)
5. Output safety check (50%) → guardrails.check_output_safety
6. Generate video scenes (60%) → runway_service
7. Generate narration (75%) → elevenlabs_service
8. Transcribe audio (80%) → deepgram_service
9. Assembly (85%) → ffmpeg_service
10. Upload files (95%) → storage_service
11. Update job with results (99%)
12. Mark complete (100%)
```

Each step:
- Updates job `current_step` and `progress`
- Logs with context
- Handles errors gracefully (warnings continue, critical errors fail job)

**Error Handling**:
- Graceful degradation (skip audio if TTS fails, use video only)
- Single video clip failure doesn't stop job
- Caption generation is optional
- Job marked as failed only if critical path breaks

### 9. Data Models

**Location**: `app/models/schemas.py`

Core models:

```python
CreateJobRequest:
  - topic: str
  - style: enum(educational, storytelling, explainer, news)
  - duration: enum(30, 60)

JobStatusResponse:
  - job_id: str
  - status: str (queued, processing, completed, failed)
  - progress: int (0-100)
  - current_step: str
  - error_message: str | null

JobResultResponse:
  - job_id: str
  - video_url: str
  - thumbnail_url: str
  - title: str
  - description: str
  - tags: list[str]
  - category: str
  - metadata: dict

UserProfile:
  - user_id: str
  - videos_created: int
  - videos_remaining: int
```

### 10. Database Schema

**Location**: `DATABASE_SCHEMA.sql`

Tables:
- `users`: User profiles
- `jobs`: Video generation jobs

Key fields:
- `id`: UUID primary key
- `user_id`: FK to users
- `status`: Current job status
- `progress`: 0-100 percentage
- `current_step`: Description of current work
- `video_url`: Storage URL when completed
- `error_message`: If failed

Indexes on:
- `user_id` (for listing user jobs)
- `status` (for filtering queued/processing)
- `created_at` (for ordering/pagination)

Row-Level Security (RLS):
- Users can only read/write their own data
- Service role can update jobs (for worker)

## Data Flow Example

### Request: Create a Video

```
1. USER makes POST /api/jobs with topic "Solar panels"
   ↓
2. FASTAPI validates request
   ├─ Input guardrail check (Claude)
   └─ Rate limit check (Supabase + Redis)
   ↓
3. INSERT job into Supabase with status="queued"
   ↓
4. ENQUEUE ARQ task with job_id
   ↓
5. RETURN job_id to user
```

### Processing: Worker Handles Job

```
6. WORKER picks up task from Redis queue
   ├─ Retrieve job details
   └─ Begin processing
   ↓
7. RESEARCH AGENT
   ├─ Call Claude with topic
   └─ Get key facts + statistics
   ↓
8. SCRIPT AGENT
   ├─ Call Claude with research
   └─ Get timed script with scenes
   ↓
9. REVIEW AGENT (loop 1)
   ├─ Call Claude with script
   └─ Check approval
   ↓
10. If revision needed & count < 2:
    ├─ Regenerate script
    └─ Loop back to step 9
    ↓
11. SHOT LIST AGENT
    ├─ Call Claude with script
    └─ Get Runway-optimized prompts
    ↓
12. OUTPUT SAFETY CHECK
    ├─ Call Claude with full script
    └─ Verify 12+ compliance
    ↓
13. RUNWAY SERVICE (for each scene)
    ├─ Create generation task
    ├─ Poll for completion
    └─ Download video bytes
    ↓
14. ELEVENLABS SERVICE
    ├─ Extract narration from script
    └─ Generate speech audio
    ↓
15. DEEPGRAM SERVICE
    ├─ Transcribe audio
    └─ Get word-level timestamps
    ↓
16. SRT FORMATTING
    ├─ Convert timestamps to SRT
    └─ Get subtitle file
    ↓
17. FFMPEG ASSEMBLY
    ├─ Combine video + audio
    ├─ Burn captions
    ├─ Add disclaimer
    └─ Get final video bytes
    ↓
18. CREATE THUMBNAIL
    ├─ Extract frame from video
    └─ Get PNG bytes
    ↓
19. SUPABASE STORAGE UPLOAD
    ├─ Upload video.mp4
    ├─ Upload thumbnail.png
    └─ Get public URLs
    ↓
20. METADATA AGENT
    ├─ Call Claude with topic + script
    └─ Get title, description, tags
    ↓
21. UPDATE JOB IN SUPABASE
    ├─ Set status="completed"
    ├─ Store video_url
    ├─ Store metadata
    └─ Set completed_at timestamp
    ↓
22. MARK JOB DONE (100%)
```

### Response: User Gets Video

```
23. USER polls GET /api/jobs/{job_id}
    ↓
24. FASTAPI queries Supabase
    ├─ If status != "completed": return progress
    └─ If status == "completed": user can fetch result
    ↓
25. USER calls GET /api/jobs/{job_id}/result
    ↓
26. FASTAPI returns video_url + metadata
    ↓
27. USER accesses video URL
    ↓
28. SUPABASE STORAGE serves video file
```

## Configuration & Customization

### Environment Variables
All configuration through `.env` file:
- API keys (Anthropic, Runway, ElevenLabs, Deepgram)
- Rate limits (per-user, global daily)
- Timeouts and retry counts
- Log level and environment

### Model Selection
- **Claude**: Configurable via `ANTHROPIC_MODEL` (defaults to Haiku 3.5)
- **ElevenLabs Voice**: Configurable via `ELEVENLABS_VOICE_ID`
- **ElevenLabs Model**: Configurable via `ELEVENLABS_MODEL_ID`

### Rate Limits
- `MAX_VIDEOS_PER_USER`: Lifetime limit (default: 2)
- `MAX_VIDEOS_PER_DAY_GLOBAL`: Daily limit (default: 20)

## Scaling Considerations

### Horizontal Scaling
1. **Multiple API instances**: Behind load balancer
2. **Multiple workers**: Run more ARQ worker processes
3. **Managed Redis**: Use Upstash, AWS ElastiCache, etc.
4. **CDN**: Cloudflare for video delivery

### Queue Monitoring
- Monitor Redis queue depth
- Alert on processing time exceeds threshold
- Auto-scale workers based on queue size

### Cost Optimization
- Use Claude Haiku for agents (cheaper than Opus/Sonnet)
- Batch process jobs during off-peak hours
- Monitor API usage for each service
- Consider rate limiting to manage costs

## Security

### Authentication
- Supabase JWT tokens
- Verified against Supabase endpoints
- User ID extracted from token claims

### Authorization
- Row-Level Security (RLS) on database
- Users can only access their own jobs
- Service role required for worker updates

### Data Protection
- Environment variables for sensitive data
- HTTPS for all external API calls
- Video URLs are public (expected for user-facing content)
- Metadata stored securely in Supabase

### Content Safety
- Input and output guardrails using Claude
- Blocked content categories
- 12+ audience enforcement
- Transparent disclaimer burned into videos

## Testing Strategy

Unit tests for:
- Service integrations (mock HTTP calls)
- Agent calls (mock Claude responses)
- Guardrail logic
- Rate limiting calculations
- Data model validation

Integration tests for:
- Full job processing pipeline
- Database operations
- Storage operations
- Auth middleware

Load tests for:
- Queue throughput
- Concurrent job processing
- API endpoint performance

## Monitoring & Logging

### Structured Logging
JSON output with:
- Timestamp
- Log level
- Module/function
- Message
- Error details (if applicable)

### Metrics to Track
- Job success rate
- Average processing time
- API latency (p50, p95, p99)
- Queue depth
- Error rates by service
- Rate limit hits
- API usage by service

### Alerts
- Job processing timeout
- Service failures (Runway, ElevenLabs, etc.)
- High error rates
- Queue backup
- Storage quota issues

## Deployment

See deployment guides for:
- Docker containerization
- Docker Compose for local development
- Kubernetes deployment
- Cloud hosting (AWS, GCP, Azure, etc.)
