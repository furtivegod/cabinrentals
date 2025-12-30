-- Supabase/PostgreSQL Table Structure for Policies and About Us Pages Migration
-- This script creates the tables needed for Policy and About Us content from Drupal

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- POLICIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core content fields
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    body TEXT,
    body_summary TEXT,
    body_format VARCHAR(50) DEFAULT 'filtered_html',
    
    -- Policy type/category
    policy_type VARCHAR(100), -- e.g., 'privacy', 'terms', 'cancellation', 'refund', etc.
    
    -- Metadata
    author_id INTEGER, -- Reference to users table (if you have one)
    author_name VARCHAR(255),
    
    -- Publishing status
    status VARCHAR(20) DEFAULT 'published', -- published, draft, archived
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- Display order
    display_order INTEGER DEFAULT 0,
    
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
    
    -- Constraints
    CONSTRAINT policies_status_check CHECK (status IN ('published', 'draft', 'archived'))
);

-- Indexes for policies
CREATE INDEX IF NOT EXISTS idx_policies_slug ON policies(slug);
CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);
CREATE INDEX IF NOT EXISTS idx_policies_policy_type ON policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_policies_display_order ON policies(display_order);
CREATE INDEX IF NOT EXISTS idx_policies_created_at ON policies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_policies_drupal_nid ON policies(drupal_nid);
CREATE INDEX IF NOT EXISTS idx_policies_published_at ON policies(published_at DESC) WHERE status = 'published';

-- ============================================
-- ABOUT US PAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS about_us_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core content fields
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    body TEXT,
    body_summary TEXT,
    body_format VARCHAR(50) DEFAULT 'filtered_html',
    
    -- Page section/type
    section VARCHAR(100), -- e.g., 'main', 'history', 'team', 'mission', etc.
    
    -- Metadata
    author_id INTEGER, -- Reference to users table (if you have one)
    author_name VARCHAR(255),
    
    -- Publishing status
    status VARCHAR(20) DEFAULT 'published', -- published, draft, archived
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- Display order
    display_order INTEGER DEFAULT 0,
    
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
    
    -- Constraints
    CONSTRAINT about_us_pages_status_check CHECK (status IN ('published', 'draft', 'archived'))
);

-- Indexes for about_us_pages
CREATE INDEX IF NOT EXISTS idx_about_us_pages_slug ON about_us_pages(slug);
CREATE INDEX IF NOT EXISTS idx_about_us_pages_status ON about_us_pages(status);
CREATE INDEX IF NOT EXISTS idx_about_us_pages_section ON about_us_pages(section);
CREATE INDEX IF NOT EXISTS idx_about_us_pages_display_order ON about_us_pages(display_order);
CREATE INDEX IF NOT EXISTS idx_about_us_pages_created_at ON about_us_pages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_about_us_pages_drupal_nid ON about_us_pages(drupal_nid);
CREATE INDEX IF NOT EXISTS idx_about_us_pages_published_at ON about_us_pages(published_at DESC) WHERE status = 'published';

-- ============================================
-- UPDATE TRIGGERS for updated_at
-- ============================================
-- Reuse the existing function if it exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_about_us_pages_updated_at BEFORE UPDATE ON about_us_pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- RLS (Row Level Security) Policies (Optional)
-- ============================================
-- Enable RLS if you want to use Supabase Auth
-- ALTER TABLE policies ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE about_us_pages ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow public read access to published content
-- CREATE POLICY "Public can view published policies" ON policies
--     FOR SELECT USING (status = 'published');
-- 
-- CREATE POLICY "Public can view published about_us_pages" ON about_us_pages
--     FOR SELECT USING (status = 'published');


