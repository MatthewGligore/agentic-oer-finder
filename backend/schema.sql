-- Supabase Schema for Syllabus Database
-- Run this SQL in Supabase SQL Editor to create tables

-- Create syllabuses table (master index)
CREATE TABLE IF NOT EXISTS syllabuses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_code TEXT NOT NULL,
  course_title TEXT,
  term TEXT,
  section_number TEXT,
  course_id TEXT NOT NULL UNIQUE,
  instructor_name TEXT,
  syllabus_url TEXT NOT NULL UNIQUE,
  scraped_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_syllabuses_course_code ON syllabuses(course_code);
CREATE INDEX IF NOT EXISTS idx_syllabuses_term ON syllabuses(term);
CREATE INDEX IF NOT EXISTS idx_syllabuses_course_id ON syllabuses(course_id);

-- Create syllabus_sections table (parsed content)
CREATE TABLE IF NOT EXISTS syllabus_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  syllabus_id UUID NOT NULL REFERENCES syllabuses(id) ON DELETE CASCADE,
  section_type TEXT NOT NULL CHECK (section_type IN ('objectives', 'topics', 'grading', 'prerequisites', 'resources', 'assessment', 'policies', 'other')),
  section_title TEXT,
  section_content TEXT,
  "order" INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for fast queries on sections
CREATE INDEX IF NOT EXISTS idx_sections_syllabus_id ON syllabus_sections(syllabus_id);
CREATE INDEX IF NOT EXISTS idx_sections_type ON syllabus_sections(section_type);

-- Saved resource snapshots for demo bookmarking (per-user when auth is enabled).
-- Legacy anonymous/demo rows use LEGACY_SAVED_USER_ID (see migrations below).
CREATE TABLE IF NOT EXISTS saved_resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL DEFAULT '00000000-0000-4000-8000-000000000001'::uuid,
  course_code TEXT NOT NULL,
  resource_url TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  source TEXT,
  license TEXT,
  final_rank_score NUMERIC,
  reasoning_summary TEXT,
  evaluation_payload JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  CONSTRAINT saved_resources_user_course_url UNIQUE (user_id, course_code, resource_url)
);

CREATE INDEX IF NOT EXISTS idx_saved_resources_course_code ON saved_resources(course_code);

-- Search/session telemetry for adaptive ranking.
CREATE TABLE IF NOT EXISTS search_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  course_code TEXT NOT NULL,
  term TEXT,
  query_variants JSONB DEFAULT '[]'::jsonb,
  syllabus_snapshot JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_search_sessions_course_code ON search_sessions(course_code);

CREATE TABLE IF NOT EXISTS result_impressions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  search_session_id UUID NOT NULL REFERENCES search_sessions(id) ON DELETE CASCADE,
  result_id TEXT NOT NULL,
  resource_url TEXT NOT NULL,
  rank_position INTEGER NOT NULL,
  source TEXT,
  final_rank_score NUMERIC,
  feature_payload JSONB DEFAULT '{}'::jsonb,
  evaluation_payload JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(search_session_id, result_id)
);

CREATE INDEX IF NOT EXISTS idx_result_impressions_session ON result_impressions(search_session_id);
CREATE INDEX IF NOT EXISTS idx_result_impressions_resource ON result_impressions(resource_url);

CREATE TABLE IF NOT EXISTS feedback_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  search_session_id UUID REFERENCES search_sessions(id) ON DELETE SET NULL,
  user_id UUID,
  result_id TEXT,
  event_type TEXT NOT NULL CHECK (event_type IN ('click', 'save', 'open_detail', 'dispute', 'manual_override', 'thumbs_up', 'thumbs_down')),
  course_code TEXT,
  resource_url TEXT,
  criterion TEXT,
  old_score NUMERIC,
  new_score NUMERIC,
  reason TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_events_session ON feedback_events(search_session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_events_type ON feedback_events(event_type);
CREATE INDEX IF NOT EXISTS idx_feedback_events_course ON feedback_events(course_code);

-- Enable Full Text Search on section content (optional, for advanced search)
ALTER TABLE syllabus_sections ADD COLUMN IF NOT EXISTS search_vector tsvector GENERATED ALWAYS AS (
  to_tsvector('english', COALESCE(section_title, '') || ' ' || COALESCE(section_content, ''))
) STORED;

CREATE INDEX IF NOT EXISTS idx_sections_search ON syllabus_sections USING GIN(search_vector);

-- Optional: Create view for commonly-needed joins
CREATE OR REPLACE VIEW syllabuses_with_sections AS
SELECT 
  s.id,
  s.course_code,
  s.course_title,
  s.term,
  s.section_number,
  s.instructor_name,
  s.syllabus_url,
  ss.section_type,
  ss.section_content,
  s.scraped_at,
  s.created_at
FROM syllabuses s
LEFT JOIN syllabus_sections ss ON s.id = ss.syllabus_id
ORDER BY s.created_at DESC, ss."order" ASC;

-- Enable Row Level Security (optional - for multi-tenant setups)
-- ALTER TABLE syllabuses ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE syllabus_sections ENABLE ROW LEVEL SECURITY;

-- Create a function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to auto-update updated_at
CREATE OR REPLACE TRIGGER update_syllabuses_updated_at
BEFORE UPDATE ON syllabuses
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_sections_updated_at
BEFORE UPDATE ON syllabus_sections
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_saved_resources_updated_at
BEFORE UPDATE ON saved_resources
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ---------------------------------------------------------------------------
-- Global query-term statistics for adaptive OER search (mined from feedback).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_term_stats (
  subject TEXT NOT NULL,
  term TEXT NOT NULL,
  positive_count INTEGER NOT NULL DEFAULT 0,
  negative_count INTEGER NOT NULL DEFAULT 0,
  weight NUMERIC NOT NULL DEFAULT 0,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  PRIMARY KEY (subject, term)
);

CREATE INDEX IF NOT EXISTS idx_query_term_stats_subject ON query_term_stats(subject);

-- ---------------------------------------------------------------------------
-- Idempotent migrations for databases created before multi-tenant columns.
-- LEGACY_SAVED_USER_ID: rows without auth are attributed here until users re-save.
-- ---------------------------------------------------------------------------
ALTER TABLE saved_resources ADD COLUMN IF NOT EXISTS user_id UUID;
UPDATE saved_resources SET user_id = '00000000-0000-4000-8000-000000000001'::uuid WHERE user_id IS NULL;
ALTER TABLE saved_resources ALTER COLUMN user_id SET DEFAULT '00000000-0000-4000-8000-000000000001'::uuid;
ALTER TABLE saved_resources ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE feedback_events ADD COLUMN IF NOT EXISTS user_id UUID;

ALTER TABLE saved_resources DROP CONSTRAINT IF EXISTS saved_resources_course_code_resource_url_key;
ALTER TABLE saved_resources DROP CONSTRAINT IF EXISTS saved_resources_user_course_url;
ALTER TABLE saved_resources ADD CONSTRAINT saved_resources_user_course_url UNIQUE (user_id, course_code, resource_url);

CREATE INDEX IF NOT EXISTS idx_saved_resources_user_course ON saved_resources(user_id, course_code);

-- Row Level Security: direct PostgREST access with user JWT (backend uses service role and bypasses RLS).
ALTER TABLE saved_resources ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS saved_resources_select_own ON saved_resources;
DROP POLICY IF EXISTS saved_resources_insert_own ON saved_resources;
DROP POLICY IF EXISTS saved_resources_update_own ON saved_resources;
DROP POLICY IF EXISTS saved_resources_delete_own ON saved_resources;

CREATE POLICY saved_resources_select_own ON saved_resources
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY saved_resources_insert_own ON saved_resources
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY saved_resources_update_own ON saved_resources
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY saved_resources_delete_own ON saved_resources
  FOR DELETE USING (auth.uid() = user_id);
