-- Supabase/PostgreSQL Table Structure for Blog and FAQ Migration
-- This script creates the tables needed for Blog and FAQ content from Drupal

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- BLOG POSTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core content fields
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    body TEXT,
    body_summary TEXT,
    body_format VARCHAR(50) DEFAULT 'filtered_html',
    
    -- Metadata
    author_id INTEGER, -- Reference to users table (if you have one)
    author_name VARCHAR(255),
    
    -- Publishing status
    status VARCHAR(20) DEFAULT 'published', -- published, draft, archived
    is_promoted BOOLEAN DEFAULT FALSE,
    is_sticky BOOLEAN DEFAULT FALSE,
    
    -- SEO fields
    meta_title VARCHAR(500),
    meta_description TEXT,
    
    -- Drupal migration fields
    drupal_nid INTEGER UNIQUE, -- Original Drupal node ID
    drupal_vid INTEGER, -- Original Drupal revision ID
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT blogs_status_check CHECK (status IN ('published', 'draft', 'archived'))
);

-- Indexes for blogs
CREATE INDEX IF NOT EXISTS idx_blogs_slug ON blogs(slug);
CREATE INDEX IF NOT EXISTS idx_blogs_status ON blogs(status);
CREATE INDEX IF NOT EXISTS idx_blogs_created_at ON blogs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blogs_drupal_nid ON blogs(drupal_nid);
CREATE INDEX IF NOT EXISTS idx_blogs_published_at ON blogs(published_at DESC) WHERE status = 'published';

-- ============================================
-- FAQ TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core content fields
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    
    -- Categorization
    category VARCHAR(255),
    tags TEXT[], -- Array of tags
    
    -- Display order
    display_order INTEGER DEFAULT 0,
    
    -- Publishing status
    status VARCHAR(20) DEFAULT 'published', -- published, draft, archived
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- SEO fields
    meta_title VARCHAR(500),
    meta_description TEXT,
    
    -- Drupal migration fields
    drupal_nid INTEGER UNIQUE, -- Original Drupal node ID
    drupal_vid INTEGER, -- Original Drupal revision ID
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT faqs_status_check CHECK (status IN ('published', 'draft', 'archived'))
);

-- Indexes for FAQs
CREATE INDEX IF NOT EXISTS idx_faqs_slug ON faqs(slug);
CREATE INDEX IF NOT EXISTS idx_faqs_status ON faqs(status);
CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category);
CREATE INDEX IF NOT EXISTS idx_faqs_display_order ON faqs(display_order);
CREATE INDEX IF NOT EXISTS idx_faqs_drupal_nid ON faqs(drupal_nid);
CREATE INDEX IF NOT EXISTS idx_faqs_tags ON faqs USING GIN(tags);

-- ============================================
-- BLOG COMMENTS TABLE (if needed)
-- ============================================
CREATE TABLE IF NOT EXISTS blog_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_id UUID NOT NULL REFERENCES blogs(id) ON DELETE CASCADE,
    
    -- Comment content
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    author_url VARCHAR(500),
    subject VARCHAR(500),
    comment_body TEXT NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'approved', -- approved, pending, spam, deleted
    
    -- Drupal migration fields
    drupal_cid INTEGER UNIQUE, -- Original Drupal comment ID
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT blog_comments_status_check CHECK (status IN ('approved', 'pending', 'spam', 'deleted'))
);

-- Indexes for blog comments
CREATE INDEX IF NOT EXISTS idx_blog_comments_blog_id ON blog_comments(blog_id);
CREATE INDEX IF NOT EXISTS idx_blog_comments_status ON blog_comments(status);
CREATE INDEX IF NOT EXISTS idx_blog_comments_created_at ON blog_comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_comments_drupal_cid ON blog_comments(drupal_cid);

-- ============================================
-- UPDATE TRIGGERS for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_blogs_updated_at BEFORE UPDATE ON blogs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faqs_updated_at BEFORE UPDATE ON faqs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_comments_updated_at BEFORE UPDATE ON blog_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- RLS (Row Level Security) Policies (Optional)
-- ============================================
-- Enable RLS if you want to use Supabase Auth
-- ALTER TABLE blogs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE faqs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE blog_comments ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow public read access to published content
-- CREATE POLICY "Public can view published blogs" ON blogs
--     FOR SELECT USING (status = 'published');
-- 
-- CREATE POLICY "Public can view published faqs" ON faqs
--     FOR SELECT USING (status = 'published');
-- 
-- CREATE POLICY "Public can view approved comments" ON blog_comments
--     FOR SELECT USING (status = 'approved');

