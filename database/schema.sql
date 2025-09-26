"""
Supabase database schema for video chunking pipeline
"""

# SQL schema for Supabase database
SUPABASE_SCHEMA = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Videos table to store video metadata
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR NOT NULL,
    title VARCHAR,
    duration FLOAT,
    file_size BIGINT,
    transcription_status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video chunks table for storing text chunks with embeddings
CREATE TABLE IF NOT EXISTS video_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_timestamp FLOAT NOT NULL,
    end_timestamp FLOAT NOT NULL,
    speaker VARCHAR,
    word_count INTEGER,
    character_count INTEGER,
    embedding VECTOR(3072),  -- OpenAI text-embedding-3-large dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_timestamps CHECK (start_timestamp >= 0 AND end_timestamp > start_timestamp),
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT valid_word_count CHECK (word_count >= 0),
    CONSTRAINT valid_character_count CHECK (character_count >= 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_video_chunks_video_id ON video_chunks(video_id);
CREATE INDEX IF NOT EXISTS idx_video_chunks_chunk_index ON video_chunks(video_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_video_chunks_timestamps ON video_chunks(start_timestamp, end_timestamp);
CREATE INDEX IF NOT EXISTS idx_video_chunks_speaker ON video_chunks(speaker);

-- Vector similarity search index
CREATE INDEX IF NOT EXISTS idx_video_chunks_embedding 
ON video_chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Query logs table for analytics
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    retrieved_chunks UUID[],
    response_text TEXT,
    similarity_scores FLOAT[],
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for query analytics
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_videos_updated_at 
    BEFORE UPDATE ON videos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for similarity search
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding VECTOR(3072),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    video_id_filter UUID DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    video_id UUID,
    chunk_text TEXT,
    chunk_index INTEGER,
    start_timestamp FLOAT,
    end_timestamp FLOAT,
    speaker VARCHAR,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vc.id,
        vc.video_id,
        vc.chunk_text,
        vc.chunk_index,
        vc.start_timestamp,
        vc.end_timestamp,
        vc.speaker,
        1 - (vc.embedding <=> query_embedding) as similarity_score
    FROM video_chunks vc
    WHERE 
        (video_id_filter IS NULL OR vc.video_id = video_id_filter)
        AND 1 - (vc.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY vc.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get chunk statistics
CREATE OR REPLACE FUNCTION get_chunk_statistics(video_uuid UUID)
RETURNS TABLE (
    total_chunks INTEGER,
    total_characters BIGINT,
    total_words BIGINT,
    avg_chunk_size FLOAT,
    duration_seconds FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_chunks,
        SUM(vc.character_count) as total_characters,
        SUM(vc.word_count) as total_words,
        AVG(vc.character_count) as avg_chunk_size,
        MAX(vc.end_timestamp) as duration_seconds
    FROM video_chunks vc
    WHERE vc.video_id = video_uuid;
END;
$$ LANGUAGE plpgsql;
"""

# RLS (Row Level Security) policies for production
RLS_POLICIES = """
-- Enable RLS on tables
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;

-- Example policies (adjust based on your authentication setup)
-- Allow authenticated users to read all data
CREATE POLICY "Allow authenticated read access" ON videos
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access" ON video_chunks
    FOR SELECT TO authenticated
    USING (true);

-- Allow service role full access
CREATE POLICY "Allow service role full access" ON videos
    FOR ALL TO service_role
    USING (true);

CREATE POLICY "Allow service role full access" ON video_chunks
    FOR ALL TO service_role
    USING (true);
"""
