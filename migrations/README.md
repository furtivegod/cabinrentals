# Database Migration Guide - Blog, FAQ, Policies & About Us

This directory contains scripts to migrate Blog, FAQ, Policies, and About Us content from the old Drupal MySQL database to Supabase PostgreSQL.

## Prerequisites

1. **Supabase Project**: Create a Supabase project at https://supabase.com
2. **Database Access**: Get your Supabase database connection string
3. **Drupal Database Access**: Access to the old Drupal MySQL database
4. **Python Dependencies**: Install required packages

## Setup

### 1. Install Dependencies

```bash
pip install mysql-connector-python psycopg2-binary python-dotenv
```

### 2. Create Supabase Tables

First, run the SQL scripts to create the tables in Supabase:

```bash
# Option 1: Using Supabase Dashboard
# Go to SQL Editor in Supabase dashboard and run:
# 1. backend/migrations/create_blog_faq_tables.sql (for blogs, FAQs, and comments)
# 2. backend/migrations/create_policies_about_tables.sql (for policies and about us pages)

# Option 2: Using psql command line
psql "postgresql://postgres:[password]@[host]:5432/postgres" -f create_blog_faq_tables.sql
psql "postgresql://postgres:[password]@[host]:5432/postgres" -f create_policies_about_tables.sql
```

### 3. Configure Environment Variables

Create a `.env` file in the backend directory:

```env
# Drupal MySQL Connection
DRUPAL_DB_HOST=localhost
DRUPAL_DB_NAME=drupal_db_name
DRUPAL_DB_USER=root
DRUPAL_DB_PASSWORD=your_password
DRUPAL_DB_PORT=3306

# Supabase Connection
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

**Important**: Replace `[password]` in `SUPABASE_DB_URL` with your actual Supabase database password (found in Project Settings > Database).

## Running the Migration

### Blog & FAQ Migration

#### Dry Run (Test without inserting data)

```bash
# For direct MySQL connection
python migrate_blog_faq.py --dry-run

# For SQL dump file
python migrate_from_sql.py --sql-file cabinre_drupal7.sql --dry-run
```

#### Full Migration

```bash
# Migrate everything (direct MySQL connection)
python migrate_blog_faq.py

# Migrate from SQL dump file
python migrate_from_sql.py --sql-file cabinre_drupal7.sql

# Migrate only blogs
python migrate_from_sql.py --sql-file cabinre_drupal7.sql --migrate-faqs=false

# Migrate only FAQs
python migrate_from_sql.py --sql-file cabinre_drupal7.sql --migrate-blogs=false

# Include comments
python migrate_from_sql.py --sql-file cabinre_drupal7.sql --migrate-comments
```

### Policies & About Us Migration

#### Dry Run (Test without inserting data)

```bash
python migrate_policies_about_from_sql.py --sql-file cabinre_drupal7.sql --dry-run
```

#### Full Migration

```bash
# Migrate everything
python migrate_policies_about_from_sql.py --sql-file cabinre_drupal7.sql

# Migrate only policies
python migrate_policies_about_from_sql.py --sql-file cabinre_drupal7.sql --migrate-about=false

# Migrate only about us pages
python migrate_policies_about_from_sql.py --sql-file cabinre_drupal7.sql --migrate-policies=false
```

### Command Line Options

#### Blog & FAQ Migration (Direct MySQL)

```bash
python migrate_blog_faq.py \
    --drupal-host localhost \
    --drupal-db drupal_db \
    --drupal-user root \
    --drupal-password your_password \
    --supabase-url https://xxx.supabase.co \
    --migrate-blogs \
    --migrate-faqs \
    --migrate-comments
```

#### Blog & FAQ Migration (SQL Dump)

```bash
python migrate_from_sql.py \
    --sql-file cabinre_drupal7.sql \
    --supabase-url https://xxx.supabase.co \
    --supabase-key your_key \
    --migrate-blogs \
    --migrate-faqs \
    --migrate-comments \
    --dry-run
```

#### Policies & About Us Migration (SQL Dump)

```bash
python migrate_policies_about_from_sql.py \
    --sql-file cabinre_drupal7.sql \
    --supabase-url https://xxx.supabase.co \
    --supabase-key your_key \
    --migrate-policies \
    --migrate-about \
    --dry-run
```

## Table Structures

### Blogs Table

- `id` (UUID) - Primary key
- `title` - Blog post title
- `slug` - URL-friendly slug
- `body` - Full blog content (HTML)
- `body_summary` - Teaser/summary
- `author_name` - Author name
- `status` - published/draft/archived
- `drupal_nid` - Original Drupal node ID (for reference)
- `created_at`, `updated_at`, `published_at` - Timestamps

### FAQs Table

- `id` (UUID) - Primary key
- `question` - FAQ question
- `answer` - FAQ answer (HTML)
- `slug` - URL-friendly slug
- `category` - FAQ category (optional)
- `tags` - Array of tags
- `display_order` - Order for display
- `status` - published/draft/archived
- `drupal_nid` - Original Drupal node ID (for reference)
- `created_at`, `updated_at`, `published_at` - Timestamps

### Blog Comments Table

- `id` (UUID) - Primary key
- `blog_id` - Reference to blog post
- `author_name`, `author_email`, `author_url` - Comment author info
- `subject` - Comment subject
- `comment_body` - Comment content
- `status` - approved/pending/spam/deleted
- `drupal_cid` - Original Drupal comment ID
- `created_at`, `updated_at` - Timestamps

### Policies Table

- `id` (UUID) - Primary key
- `title` - Policy page title
- `slug` - URL-friendly slug
- `body` - Full policy content (HTML)
- `body_summary` - Teaser/summary
- `policy_type` - Type of policy (privacy, terms, cancellation, refund, agreement, general)
- `author_name` - Author name
- `status` - published/draft/archived
- `is_featured` - Whether to feature this policy
- `display_order` - Order for display
- `drupal_nid` - Original Drupal node ID (for reference)
- `created_at`, `updated_at`, `published_at` - Timestamps

### About Us Pages Table

- `id` (UUID) - Primary key
- `title` - About us page title
- `slug` - URL-friendly slug
- `body` - Full about us content (HTML)
- `body_summary` - Teaser/summary
- `section` - Section type (main, history, team, mission, contact)
- `author_name` - Author name
- `status` - published/draft/archived
- `is_featured` - Whether to feature this page
- `display_order` - Order for display
- `drupal_nid` - Original Drupal node ID (for reference)
- `created_at`, `updated_at`, `published_at` - Timestamps

## Verification

After migration, verify the data:

```sql
-- Check blog count
SELECT COUNT(*) FROM blogs;

-- Check FAQ count
SELECT COUNT(*) FROM faqs;

-- Check comments count
SELECT COUNT(*) FROM blog_comments;

-- Check policies count
SELECT COUNT(*) FROM policies;

-- Check about us pages count
SELECT COUNT(*) FROM about_us;

-- View sample blogs
SELECT title, slug, status, created_at FROM blogs ORDER BY created_at DESC LIMIT 10;

-- View sample FAQs
SELECT question, slug, status FROM faqs ORDER BY display_order LIMIT 10;

-- View sample policies
SELECT title, slug, policy_type, status FROM policies ORDER BY display_order LIMIT 10;

-- View sample about us pages
SELECT title, slug, section, status FROM about_us ORDER BY display_order LIMIT 10;
```

## Troubleshooting

### Connection Issues

1. **Supabase Connection**: Make sure `SUPABASE_DB_URL` is correct and includes the password
2. **Drupal Connection**: Verify MySQL credentials and that the database is accessible
3. **SSL**: Supabase requires SSL connections - the script uses `sslmode='require'`

### Data Issues

1. **Duplicate Entries**: The script checks for existing entries by `drupal_nid` and skips duplicates
2. **Missing Data**: Check Drupal database to ensure content exists and is published (`status = 1`)
3. **Slug Conflicts**: Slugs are auto-generated and made unique by appending Drupal node ID if needed

### FAQ Detection

The script searches for FAQs in multiple ways:
- Content type = 'faq'
- Content type = 'page' with title containing 'FAQ' or 'Question'
- Content type = 'landing_page' with title containing 'FAQ'

If FAQs aren't being found, you may need to adjust the query in `fetch_faqs_from_drupal()`.

### Policy Detection

The migration script automatically detects policies based on title keywords:
- 'policy', 'privacy', 'terms', 'cancellation', 'refund', 'agreement'

Policy types are automatically detected:
- `privacy` - Privacy policy
- `terms` - Terms of service
- `cancellation` - Cancellation policy
- `refund` - Refund policy
- `agreement` - User agreement
- `general` - General policy

### About Us Detection

The migration script automatically detects about us pages based on title keywords:
- 'about', 'about-us', 'about_us'

Sections are automatically detected:
- `main` - Main about us page
- `history` - Company history
- `team` - Team/staff information
- `mission` - Mission/vision
- `contact` - Contact information

## Next Steps

After migration:

1. **Review Data**: Check the migrated content in Supabase dashboard
2. **Update Backend Models**: Ensure your FastAPI models match the table structure
3. **Create API Endpoints**: Build endpoints to serve blog and FAQ data
4. **Frontend Integration**: Connect Next.js frontend to the new API

