-- AI Interviewer Agent Database Schema
-- Supabase PostgreSQL Database Setup

-- Create users table (for future authentication support)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create interview_sessions table (core session management)
CREATE TABLE IF NOT EXISTS interview_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_config JSONB NOT NULL DEFAULT '{}',
    conversation_history JSONB NOT NULL DEFAULT '[]',
    per_turn_feedback_log JSONB NOT NULL DEFAULT '[]',
    final_summary JSONB DEFAULT NULL,
    session_stats JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create speech_tasks table (separate speech processing state)
CREATE TABLE IF NOT EXISTS speech_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    task_type TEXT NOT NULL CHECK (task_type IN ('stt_batch', 'tts', 'stt_stream')),
    status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'error')),
    progress_data JSONB DEFAULT '{}',
    result_data JSONB DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON interview_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_speech_tasks_session_id ON speech_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_speech_tasks_status ON speech_tasks(status);
CREATE INDEX IF NOT EXISTS idx_speech_tasks_created_at ON speech_tasks(created_at);

-- Add RLS (Row Level Security) policies for data isolation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE speech_tasks ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY users_policy ON users 
    FOR ALL USING (id = auth.uid());

-- Sessions policy - users can only access their own sessions
CREATE POLICY sessions_policy ON interview_sessions 
    FOR ALL USING (user_id = auth.uid() OR user_id IS NULL);

-- Speech tasks policy - users can only access tasks for their sessions
CREATE POLICY speech_tasks_policy ON speech_tasks 
    FOR ALL USING (
        session_id IN (
            SELECT session_id FROM interview_sessions 
            WHERE user_id = auth.uid() OR user_id IS NULL
        )
    );

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON interview_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_speech_tasks_updated_at 
    BEFORE UPDATE ON speech_tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 