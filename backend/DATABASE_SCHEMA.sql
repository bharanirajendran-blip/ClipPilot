-- ClipPilot Lite Database Schema
-- Create this in Supabase PostgreSQL

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Video jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    topic VARCHAR(500) NOT NULL,
    style VARCHAR(50) NOT NULL CHECK (style IN ('educational', 'storytelling', 'explainer', 'documentary', 'animated')),
    duration INTEGER NOT NULL CHECK (duration IN (30, 60, 90)),
    status VARCHAR(50) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(255),
    video_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    title VARCHAR(255),
    description TEXT,
    tags JSONB,
    category VARCHAR(100),
    metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users
CREATE POLICY "Users can read own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for jobs
CREATE POLICY "Users can read own jobs" ON jobs
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert own jobs" ON jobs
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can update jobs" ON jobs
    FOR UPDATE USING (auth.role() = 'service_role');

-- Storage bucket setup
-- Run in Supabase dashboard:
-- 1. Go to Storage
-- 2. Create new bucket named "videos"
-- 3. Make it public
-- 4. Add policy for uploads by authenticated users
