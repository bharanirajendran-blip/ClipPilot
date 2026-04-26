-- ═══════════════════════════════════════════════════
-- ClipPilot Lite — Supabase Database Schema
-- ═══════════════════════════════════════════════════

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── User Profiles ───
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    videos_created INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (NEW.id, NEW.email, COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ─── Jobs ───
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    style TEXT NOT NULL CHECK (style IN ('educational', 'storytelling', 'explainer', 'news')),
    duration INTEGER NOT NULL CHECK (duration IN (30, 60, 90)),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 NOT NULL CHECK (progress >= 0 AND progress <= 100),
    current_step TEXT DEFAULT 'queued',
    video_url TEXT,
    thumbnail_url TEXT,
    title TEXT,
    description TEXT,
    tags TEXT[],
    research_data JSONB,
    script_data JSONB,
    shot_list_data JSONB,
    audio_url TEXT,
    metrics JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON public.jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON public.jobs(created_at DESC);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER jobs_updated_at
    BEFORE UPDATE ON public.jobs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ─── Global Daily Counter ───
CREATE TABLE IF NOT EXISTS public.daily_counters (
    date DATE PRIMARY KEY DEFAULT CURRENT_DATE,
    video_count INTEGER DEFAULT 0 NOT NULL
);

-- ─── Row Level Security ───
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Profiles: users can read/update their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Jobs: users can view their own jobs
CREATE POLICY "Users can view own jobs"
    ON public.jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs"
    ON public.jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Service role bypasses RLS for backend operations
-- (The backend uses SUPABASE_SERVICE_ROLE_KEY which bypasses RLS)

-- ─── Storage Buckets ───
-- Run in Supabase dashboard: create public buckets called "videos" and "audio"
-- Or via SQL:
INSERT INTO storage.buckets (id, name, public)
VALUES
    ('videos', 'videos', true),
    ('audio', 'audio', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies: anyone can read, only service role can write
CREATE POLICY "Public video access"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'videos');

CREATE POLICY "Public audio access"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'audio');

CREATE POLICY "Public audio access"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'audio');
