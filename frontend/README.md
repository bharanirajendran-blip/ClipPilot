# ClipPilot Lite - Frontend

A modern, production-ready Next.js 14 frontend for ClipPilot Lite, an AI-powered short vertical video generator.

## Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Supabase Auth
- **UI Components**: Custom React components with Tailwind styling
- **Deployment**: Vercel-ready

## Features

- User authentication (signup/login)
- Video generation workflow
- Real-time job status polling
- Video player with playback controls
- Dashboard with video management
- Responsive design (mobile-first)
- Dark theme with gradient accents
- Progressive loading states

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Landing page
│   │   ├── auth/               # Authentication pages
│   │   ├── create/             # Video creation page
│   │   ├── status/[jobId]/     # Job status page
│   │   ├── result/[jobId]/     # Video result page
│   │   └── dashboard/          # User dashboard
│   ├── components/             # Reusable React components
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── VideoPlayer.tsx
│   │   ├── ProgressSteps.tsx
│   │   └── ProtectedRoute.tsx
│   ├── lib/                    # Utility functions and hooks
│   │   ├── supabase.ts         # Supabase client
│   │   ├── api.ts              # Backend API client
│   │   └── hooks.ts            # Custom React hooks
│   └── styles/
│       └── globals.css         # Global Tailwind styles
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.local                  # Environment variables

```

## Getting Started

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn
- Supabase account and project
- Backend API running (see capstone/backend README)

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.local.example .env.local
   ```
   
   Edit `.env.local` with your Supabase credentials and backend API URL:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. Pages will auto-update as you edit.

### Building for Production

Build the application:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

### Type Checking

Check TypeScript types:

```bash
npm run type-check
```

## Environment Variables

Required environment variables (configure in `.env.local`):

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://abc123.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJhbGc...` |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

All variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Pages and Routes

### Public Routes

- **`/`** - Landing page with feature overview
- **`/auth`** - Authentication (signup/login)

### Protected Routes (require authentication)

- **`/create`** - Video creation form
- **`/status/[jobId]`** - Video generation progress (polls API every 3s)
- **`/result/[jobId]`** - Video player and details
- **`/dashboard`** - User's video gallery and stats

## API Integration

The frontend communicates with the backend API at `process.env.NEXT_PUBLIC_API_URL`.

### API Endpoints Used

All requests include `Authorization: Bearer {token}` header.

- `POST /api/jobs` - Create video generation job
- `GET /api/jobs` - Get user's jobs
- `GET /api/jobs/{jobId}/status` - Poll job status
- `GET /api/jobs/{jobId}/result` - Get completed video details
- `GET /api/profile` - Get user profile (remaining videos)

### Response Examples

**Create Job**:
```json
{ "job_id": "abc123" }
```

**Job Status**:
```json
{
  "status": "processing",
  "progress": 35,
  "current_step": "shots",
  "error_message": null
}
```

**Job Result**:
```json
{
  "video_url": "https://...",
  "title": "The History of AI",
  "description": "A brief overview of artificial intelligence...",
  "tags": ["AI", "technology", "education"],
  "thumbnail_url": "https://..."
}
```

## Authentication Flow

1. User visits `/auth`
2. Enters email and password
3. Supabase creates account or signs in
4. Session token stored in browser
5. Redirected to `/create` on success
6. Protected routes check `useAuth()` hook
7. Unauth users redirected to `/auth`

## Styling

Uses Tailwind CSS with custom theme configuration:

- **Primary color**: Indigo/Violet gradient
- **Dark theme**: Custom dark backgrounds and surfaces
- **Custom components**: Button variants, card styles, inputs
- **Animations**: Smooth transitions and loading states

## Performance Optimizations

- Next.js Image optimization (configured for Supabase CDN)
- Code splitting with dynamic imports
- CSS-in-JS with Tailwind (no runtime overhead)
- Client-side component optimization with `'use client'` directive
- Efficient polling with exponential backoff

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## Deployment

The frontend is optimized for Vercel deployment:

1. Push code to GitHub
2. Connect GitHub repo to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy automatically on push

### Docker Deployment

Build Docker image:

```bash
docker build -t clippilot-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_SUPABASE_URL=... \
  -e NEXT_PUBLIC_SUPABASE_ANON_KEY=... \
  -e NEXT_PUBLIC_API_URL=... \
  clippilot-frontend
```

## Troubleshooting

### "Cannot find module '@/...'"

Check that `tsconfig.json` has the correct `paths` configuration.

### "CORS error from API"

Ensure backend is running and `NEXT_PUBLIC_API_URL` is correct. Backend must enable CORS for frontend origin.

### Videos not loading

Check that `NEXT_PUBLIC_SUPABASE_URL` is correct and Supabase storage bucket is accessible.

### Authentication not working

Verify Supabase credentials are correct. Check browser console for errors.

## Development Workflow

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Make changes and commit: `git commit -m 'Add amazing feature'`
3. Test locally: `npm run dev`
4. Run type check: `npm run type-check`
5. Push and create pull request

## License

Part of the ClipPilot Lite capstone project.

## Support

For issues or questions, check:
- Backend README: `../backend/README.md`
- API documentation: `../backend/docs/`
