-- 1. Enable the pgvector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id VARCHAR(50) UNIQUE NOT NULL,
    original_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    department VARCHAR(50) NOT NULL,
    sub_category VARCHAR(100),
    urgency VARCHAR(20) NOT NULL,
    urgency_score FLOAT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    keywords JSONB DEFAULT '[]'::jsonb,
    location JSONB, -- Stores the resolved location dict
    embedding vector(384), -- MiniLM generates 384-dimensional embeddings
    cluster_id VARCHAR(50),
    source VARCHAR(50) DEFAULT 'web',
    suggested_response_urdu TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create an index to speed up vector searches (optional but recommended)
CREATE INDEX ON complaints USING hnsw (embedding vector_cosine_ops);

-- 4. Create RPC function for finding duplicate clusters (Cosine Similarity)
-- This function takes a new embedding, department, and threshold,
-- and returns the most similar existing complaint if it exceeds the threshold.
CREATE OR REPLACE FUNCTION match_complaints (
  query_embedding vector(384),
  match_department VARCHAR,
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (
  id UUID,
  complaint_id VARCHAR,
  original_text TEXT,
  similarity FLOAT,
  cluster_id VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.complaint_id,
    c.original_text,
    1 - (c.embedding <=> query_embedding) AS similarity,
    c.cluster_id
  FROM complaints c
  WHERE c.department = match_department
    -- Only check complaints from the last 7 days
    AND c.processed_at >= NOW() - INTERVAL '7 days'
    -- 1 - (embedding <=> query) is cosine similarity
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
