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
