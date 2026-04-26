# ClipPilot Lite

AI-powered short vertical video generator built as a capstone project for UConn GRAD 5900: Applied Generative AI (Spring 2026).

Enter a topic, pick a style, and get a production-ready 30–50 second video with AI narration, captions, background music, and a professional cinematic look — all generated automatically by a 5-agent pipeline orchestrated through the Model Context Protocol (MCP).

## Course Concepts Demonstrated

| Week | Topic | Implementation |
|------|-------|---------------|
| 1 | AI Landscape | Multi-model selection: Claude Haiku for agents, Google Veo 2.0 for video (Runway fallback), ElevenLabs for TTS, Deepgram for STT |
| 2 | Prompt Engineering | 5 specialized system prompts with JSON schema enforcement, self-check instructions, prompt chaining |
| 3 | Developer Stack | Pipeline pattern with FastAPI + Next.js + Supabase + Redis + ARQ orchestration |
| 7 | Evaluation | LLM-as-Judge (review agent), per-step timing metrics, cost estimates per video |
| 9 | MCP Servers | MCP tool server exposing 4 tools via JSON-RPC 2.0, MCP client in worker pipeline |
| 10 | Multi-Agent | 5-agent sequential pipeline with supervisor pattern (review agent gates the flow) |
| 11 | Human-in-the-Loop | User controls topic/style/duration/audio, review feedback loop, behind-the-scenes transparency |
| 12 | Small Models | Claude Haiku (cost-efficient) for all agents, ~$0.04 per video in API costs |
| 13 | Vision Validation | Post-generation frame extraction + Claude vision check on every video clip |
| 14 | Safety | Input + output guardrails (fail-closed), 12+ content filtering, SSRF protection, JWT auth |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js 14  │────▶│  FastAPI API  │────▶│  ARQ Worker  │
│   Frontend   │     │   + MCP RPC  │     │  (Pipeline)  │
└─────────────┘     └──────┬───────┘     └──────┬───────┘
                           │                     │
                    ┌──────▼───────┐      ┌──────▼───────┐
                    │   Supabase   │      │  MCP Client   │
                    │ Auth+DB+Store│      │      ↓        │
                    └──────────────┘      │  MCP Server   │
                                          │      ↓        │
                    ┌──────────────┐      │  Tool Layer   │
                    │    Redis     │      │ Veo│Runway│TTS │
                    │  (ARQ Queue) │      │ Deepgram│FFmpeg│
                    └──────────────┘      └──────────────┘
```

### MCP Integration

The worker pipeline calls external services through the MCP protocol:

```
Worker (Agent Runtime)
    ↓  mcp_client.call_tool("generate_video", {prompt, duration})
MCP Client (app/mcp/client.py)
    ↓  tools/call (JSON-RPC 2.0)
MCP Server (app/mcp/server.py)
    ↓  routes to provider based on VIDEO_PROVIDER config
VeoService / RunwayService / ElevenLabsService / DeepgramService
    ↓  HTTP/SDK API calls
External APIs (Google Veo 2.0, Runway, ElevenLabs, Deepgram)
```

MCP tools available at `GET /mcp/tools`:

| Tool | Description |
|------|-------------|
| `generate_video` | AI video generation — routes to Veo 2.0 (primary) or Runway (fallback) based on config |
| `elevenlabs_text_to_speech` | Text-to-speech narration |
| `deepgram_transcribe` | Audio transcription with word timestamps |
| `content_safety_check` | 12+ content moderation |

## AI Pipeline (5 Agents)

1. **Research Agent** — Gathers facts, statistics, and narrative angles for the topic
2. **Script Agent** — Writes a timed narration script with concrete visual descriptions; accepts revision feedback
3. **Shot List Agent** — Converts scenes into optimized video generation prompts with camera direction, lighting, and style
4. **Review Agent** — LLM-as-Judge that checks accuracy, tone, pacing, and 12+ compliance; can send script back for revision with structured feedback
5. **Metadata Agent** — Generates title, description, and tags for discoverability

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python 3.11 |
| MCP Protocol | Custom MCP server + client (JSON-RPC 2.0) |
| Job Queue | Redis + ARQ |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth (server-side token verification) |
| Storage | Supabase Storage (videos + audio buckets) |
| AI Agents | Claude Haiku 3.5 (5 specialized agents) |
| Video Gen | Google Veo 2.0 (primary), Runway Gen-3 Alpha Turbo (fallback) |
| Narration | ElevenLabs Turbo v2.5 |
| Captions | Deepgram Nova-2 |
| Assembly | FFmpeg (bundled via imageio-ffmpeg) |
| Background Music | Pure Python ambient generator (no API cost) |

## Safety and Guardrails

- Input moderation via Claude before any processing (fail-closed on errors)
- Output moderation on generated scripts (fail-closed on errors)
- 12+ family-friendly content enforcement
- SSRF protection on audio URLs (only Supabase storage allowed)
- JWT token verification via Supabase server-side auth
- Audio URL validation at submission time (reject untrusted domains)
- Auto-disclaimer burned into every video: *"Generated by ClipPilot based on user input. Verify claims independently."*
- Vision validation: post-generation frame extraction + Claude vision check on generated clips
- Tiered retry logic: automatic prompt simplification and retry on video generation failures
- Job cancellation: full abort support (DB flag + ARQ job abort in Redis)

## Evaluation Metrics

Every completed job records metrics as JSONB:

```json
{
  "research_seconds": 18.2,
  "script_seconds": 12.4,
  "total_seconds": 245.6,
  "scenes_generated": 5,
  "scenes_total": 5,
  "cost_estimate": {
    "claude_agents": 0.025,
    "veo_video": 0.45,
    "elevenlabs_tts": 0.01,
    "deepgram_stt": 0.005,
    "total": 0.49
  }
}
```

## Rate Limits

- 2 videos per user account (lifetime, configurable)
- 50 videos for tester accounts (configurable via TESTER_EMAILS + TESTER_VIDEO_LIMIT)
- 20 videos per day (global cap)
- Budget target: ~$36/month at 50 videos

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Redis (install via `brew install redis` on macOS)
- Supabase project (free tier works)
- API keys: Anthropic, ElevenLabs, Deepgram
- Google Cloud project with Vertex AI API enabled (for Veo 2.0) + Application Default Credentials
- Runway API key (optional, only needed if using Runway as video provider)

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/capstone.git
cd capstone

# Copy example env and fill in your API keys
cp .env.example .env
```

Edit `.env` with your actual keys:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=sb_publishable_xxx
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxx
ANTHROPIC_API_KEY=sk-ant-xxx
ELEVENLABS_API_KEY=sk_xxx
DEEPGRAM_API_KEY=xxx
REDIS_URL=redis://localhost:6379

# Video provider: "veo" (Google Veo 2.0) or "runway"
VIDEO_PROVIDER=veo
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET=your-gcs-bucket-name

# Only needed if VIDEO_PROVIDER=runway
RUNWAY_API_KEY=key_xxx
```

### 2. Set up Supabase

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run the contents of `supabase/schema.sql`
3. This creates: profiles table, jobs table, storage buckets (videos + audio), RLS policies, and auto-triggers

### 3. Configure frontend environment

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_xxx
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start Redis

```bash
# Terminal 1
redis-server
```

Or if Redis is already running as a service, skip this step.

### 5. Start backend (FastAPI)

```bash
# Terminal 2
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` should return `{"status": "ok"}`

### 6. Start worker (ARQ)

```bash
# Terminal 3
cd backend
source .venv/bin/activate
arq app.worker.settings.WorkerSettings
```

You should see: `Starting worker for 1 functions: process_video_job`

**Important**: Only run ONE worker. Do not run both `arq` and `python -m worker` simultaneously.

### 7. Start frontend (Next.js)

```bash
# Terminal 4
cd frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

### 8. Verify API keys (optional)

```bash
cd backend
python test_keys.py
```

### Docker (all-in-one)

```bash
docker-compose up --build
```

## Usage

1. Go to `http://localhost:3000` and sign up with email/password
2. Click "Create" and enter a topic (be specific for best results)
3. Choose a style (educational, storytelling, explainer, news)
4. Choose duration (30 or 50 seconds)
5. Optionally record narration with the mic button or upload an audio file
6. Click "Generate Video" and wait (~2-5 minutes)
7. View and download your completed video on the result page

### Tips for Good Results

- Be specific: *"How CRISPR gene editing works in cancer treatment"* beats *"science stuff"*
- Include perspective: *"Explain blockchain to a 10-year-old"* gives the AI a clear angle
- Add context: *"The history of coffee from Ethiopia to modern espresso"* tells a story arc
- Keep it focused: One clear topic works better than trying to cover everything

## API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/profile` | User profile with video quota |
| POST | `/api/jobs` | Create video generation job |
| GET | `/api/jobs` | List user's jobs |
| GET | `/api/jobs/{id}/status` | Poll job progress |
| GET | `/api/jobs/{id}/result` | Get completed video URL + metadata + metrics |
| POST | `/api/jobs/{id}/cancel` | Cancel a running or queued job |
| DELETE | `/api/jobs/{id}` | Delete a completed/failed job |
| POST | `/api/jobs/upload-audio` | Upload custom narration audio |

### MCP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mcp/rpc` | JSON-RPC 2.0 MCP protocol endpoint |
| GET | `/mcp/tools` | List available MCP tools (convenience) |

Example MCP JSON-RPC call:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page with features and CTA |
| `/auth` | Login, registration, and password reset |
| `/create` | Topic input, style/duration selection, mic recording, audio upload |
| `/status/[jobId]` | Real-time progress tracking with step indicators + cancel button |
| `/result/[jobId]` | Video player, download, delete, behind-the-scenes data, metrics |
| `/dashboard` | User's video gallery with delete option |

## Project Structure

```
capstone/
├── backend/
│   ├── app/
│   │   ├── agents/          # 5 Claude AI agents
│   │   │   ├── base.py      # BaseAgent with JSON extraction
│   │   │   ├── research_agent.py
│   │   │   ├── script_agent.py
│   │   │   ├── shot_list_agent.py
│   │   │   ├── review_agent.py
│   │   │   └── metadata_agent.py
│   │   ├── mcp/             # Model Context Protocol layer
│   │   │   ├── server.py    # MCP tool server (tools/list + tools/call)
│   │   │   ├── client.py    # MCP client for worker pipeline
│   │   │   └── routes.py    # HTTP transport (JSON-RPC 2.0)
│   │   ├── middleware/      # Auth (Supabase server-side JWT)
│   │   ├── models/          # Pydantic schemas
│   │   ├── routes/          # REST API endpoints
│   │   ├── services/        # External API integrations
│   │   │   ├── veo_service.py       # Google Veo 2.0 video generation (primary)
│   │   │   ├── runway_service.py    # Runway Gen-3 video generation (fallback)
│   │   │   ├── elevenlabs_service.py # Text-to-speech
│   │   │   ├── deepgram_service.py  # Transcription
│   │   │   ├── ffmpeg_service.py    # Video assembly
│   │   │   ├── music_service.py     # Ambient music generation
│   │   │   ├── guardrails.py        # Content moderation (fail-closed)
│   │   │   ├── vision_validator.py  # Post-generation vision validation
│   │   │   └── storage_service.py   # Supabase storage
│   │   ├── utils/           # SRT generation, structured logging
│   │   ├── worker/          # ARQ job processing + settings
│   │   ├── config.py        # Pydantic Settings (env vars)
│   │   └── main.py          # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── test_keys.py         # API key validation script
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js 14 pages (App Router)
│   │   │   ├── page.tsx     # Landing page
│   │   │   ├── auth/        # Login/register
│   │   │   ├── create/      # Video creation form + mic recording
│   │   │   ├── status/      # Job progress tracking
│   │   │   ├── result/      # Video player + download
│   │   │   └── dashboard/   # Video gallery
│   │   ├── components/      # Shared UI components
│   │   ├── lib/             # Supabase client, API helpers, hooks
│   │   └── styles/          # Global CSS + Tailwind
│   ├── Dockerfile
│   └── package.json
├── supabase/
│   └── schema.sql           # Database schema + RLS + storage buckets
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | required |
| `SUPABASE_ANON_KEY` | Supabase publishable key | required |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase secret key | required |
| `ANTHROPIC_API_KEY` | Claude API key | required |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | required |
| `DEEPGRAM_API_KEY` | Deepgram API key | required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `VIDEO_PROVIDER` | Video generation provider | `veo` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (for Veo) | required if veo |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `GCS_BUCKET` | GCS bucket for Veo output | required if veo |
| `VEO_MODEL` | Veo model name | `veo-2.0-generate-001` |
| `RUNWAY_API_KEY` | Runway API key | required if runway |
| `RUNWAY_MODEL` | Runway model name | `gen3a_turbo` |
| `MAX_VIDEOS_PER_USER` | Per-user lifetime video limit | `2` |
| `TESTER_EMAILS` | Comma-separated tester emails (higher limit) | `""` |
| `TESTER_VIDEO_LIMIT` | Video limit for tester accounts | `50` |
| `MAX_VIDEOS_PER_DAY_GLOBAL` | Global daily video cap | `20` |
| `ANTHROPIC_MODEL` | Claude model name | `claude-haiku-4-5-20251001` |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice | `21m00Tcm4TlvDq8ikWAM` |
| `APP_ENV` | Environment (development/production) | `development` |

## Deployment

| Service | Platform | Notes |
|---------|----------|-------|
| Frontend | Vercel | Connect GitHub repo, set `NEXT_PUBLIC_*` env vars |
| Backend + Worker | Railway | Deploy from `backend/` directory, set all env vars |
| Database + Auth + Storage | Supabase | Free tier sufficient for demo |
| Redis | Railway or Upstash | Upstash free tier works |

## Cost Analysis

| Service | Cost per Video | Monthly (50 videos) |
|---------|---------------|---------------------|
| Claude Haiku (5 agents) | ~$0.025 | $1.25 |
| Google Veo 2.0 (5-9 clips) | ~$0.45 | $22.50 |
| ElevenLabs (narration) | ~$0.01 | $0.50 |
| Deepgram (transcription) | ~$0.005 | $0.25 |
| Background Music | $0.00 | $0.00 |
| Supabase (free tier) | $0.00 | $0.00 |
| Redis (Upstash free) | $0.00 | $0.00 |
| **Total** | **~$0.49** | **~$24.50** |

## License

Private — UConn GRAD 5900 capstone project, Spring 2026.
