-- Migration: Update to Time-Based Interviews
-- Date: 2024-01-XX
-- Description: Migrate from question-based to time-based interview approach

-- Update existing sessions to have time-based configuration
UPDATE interview_sessions 
SET session_config = session_config || jsonb_build_object(
  'use_time_based_interview', true,
  'interview_duration_minutes', COALESCE(
    (session_config->>'interview_duration_minutes')::int, 
    CASE 
      WHEN (session_config->>'question_count')::int > 0 
      THEN (session_config->>'question_count')::int * 2  -- Assume 2 minutes per question
      ELSE 30  -- Default to 30 minutes
    END
  )
)
WHERE session_config IS NOT NULL;

-- Add indexes for time-based queries if needed
CREATE INDEX IF NOT EXISTS idx_sessions_config_duration 
ON interview_sessions USING gin ((session_config->'interview_duration_minutes'));

CREATE INDEX IF NOT EXISTS idx_sessions_config_time_based 
ON interview_sessions USING gin ((session_config->'use_time_based_interview'));

-- Update session_stats to include time-based metrics where missing
UPDATE interview_sessions 
SET session_stats = session_stats || jsonb_build_object(
  'interview_approach', 'time_based',
  'target_duration_minutes', COALESCE(
    (session_config->>'interview_duration_minutes')::int,
    30
  )
)
WHERE session_stats IS NOT NULL 
AND session_stats->>'interview_approach' IS NULL; 