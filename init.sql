
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Articles
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT UNIQUE,
    publisher TEXT,
    published_at TIMESTAMP,
    language TEXT DEFAULT 'en',
    scraped_at TIMESTAMP DEFAULT NOW(),
    category_scores VECTOR(20),
    metadata JSONB
);

-- Index for vector similarity
CREATE INDEX IF NOT EXISTS articles_category_vector_idx
    ON articles USING ivfflat (category_scores vector_cosine_ops)
    WITH (lists = 100);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    name TEXT,
    preferences VECTOR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for user vector preferences
CREATE INDEX IF NOT EXISTS users_preference_vector_idx
    ON users USING ivfflat (preferences vector_cosine_ops)
    WITH (lists = 100);

-- Article Reads
CREATE TABLE IF NOT EXISTS article_reads (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    read_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, article_id)
);

-- Synthesized Articles
CREATE TABLE IF NOT EXISTS synthesized_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW(),
    generation_prompt TEXT,
    notes TEXT
);

-- Synthesized Sources
CREATE TABLE IF NOT EXISTS synthesized_sources (
    synthesized_id UUID REFERENCES synthesized_articles(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (synthesized_id, article_id)
);

-- Daily Summaries
CREATE TABLE IF NOT EXISTS daily_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    article_ids UUID[],
    summary_generated_at TIMESTAMP DEFAULT NOW()
);
