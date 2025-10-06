-- Create candidates table for structured LinkedIn profiles
-- This table stores all profile data in a single denormalized table

CREATE TABLE IF NOT EXISTS candidates (
    -- Primary identification
    linkedin_url TEXT PRIMARY KEY,

    -- Basic profile information
    name TEXT NOT NULL,
    headline TEXT,
    location TEXT,
    phone TEXT,
    email TEXT,

    -- Profile images
    profile_pic TEXT,
    profile_pic_high_quality TEXT,

    -- Connections
    connected_to TEXT[],

    -- Career information
    seniority TEXT,
    skills TEXT[],
    years_experience INTEGER,
    average_tenure NUMERIC(4,2),
    worked_at_startup BOOLEAN DEFAULT FALSE,

    -- Nested data as JSONB for flexible querying
    experiences JSONB,
    education JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common search fields
CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name);
CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates(location);
CREATE INDEX IF NOT EXISTS idx_candidates_seniority ON candidates(seniority);
CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates USING GIN(skills);
CREATE INDEX IF NOT EXISTS idx_candidates_worked_at_startup ON candidates(worked_at_startup);

-- Create GIN indexes on JSONB fields for efficient querying
CREATE INDEX IF NOT EXISTS idx_candidates_experiences ON candidates USING GIN(experiences);
CREATE INDEX IF NOT EXISTS idx_candidates_education ON candidates USING GIN(education);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_candidates_updated_at ON candidates;
CREATE TRIGGER update_candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - optional, uncomment if needed
-- ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations for service role - optional
-- CREATE POLICY "Enable all access for service role" ON candidates
--     FOR ALL
--     USING (true)
--     WITH CHECK (true);

COMMENT ON TABLE candidates IS 'Structured LinkedIn candidate profiles with AI-enhanced data';
COMMENT ON COLUMN candidates.linkedin_url IS 'LinkedIn profile URL - used as primary key';
COMMENT ON COLUMN candidates.experiences IS 'JSONB array of work experiences with company details, skills, and industry tags';
COMMENT ON COLUMN candidates.education IS 'JSONB array of educational background';
COMMENT ON COLUMN candidates.skills IS 'Array of technical and domain skills extracted from profile';
