#!/usr/bin/env python3
"""
Migration script to migrate Blog and FAQ data from Drupal MySQL to Supabase PostgreSQL

Usage:
    python migrate_blog_faq.py --drupal-host localhost --drupal-db drupal_db --drupal-user user --drupal-password pass \
                                --supabase-url https://xxx.supabase.co --supabase-key your_key

Requirements:
    pip install mysql-connector-python supabase python-dotenv
"""

import argparse
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional
import mysql.connector
from mysql.connector import Error as MySQLError
from supabase import create_client, Client
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove all non-word characters except hyphens
    text = re.sub(r'[^\w\-]+', '', text)
    # Replace multiple hyphens with single hyphen
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


def parse_host_from_url(url_or_host: str) -> str:
    """Extract hostname from URL or return hostname as-is"""
    if not url_or_host:
        return url_or_host
    
    # Remove trailing slash
    url_or_host = url_or_host.rstrip('/')
    
    # If it looks like a URL, parse it
    if url_or_host.startswith(('http://', 'https://')):
        parsed = urlparse(url_or_host)
        hostname = parsed.hostname or parsed.path.split('/')[0]
        if hostname:
            print(f"ℹ Extracted hostname '{hostname}' from URL: {url_or_host}")
            return hostname
    
    return url_or_host


def get_drupal_connection(host: str, database: str, user: str, password: str, port: int = 3306, 
                         connection_timeout: int = 10, use_ssl: bool = False):
    """Create MySQL connection to Drupal database"""
    try:
        # Parse host from URL if needed
        host = parse_host_from_url(host)
        
        if not host:
            raise ValueError("Drupal MySQL host is required")
        
        # Build connection parameters
        connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'connection_timeout': connection_timeout,
            'autocommit': True
        }
        
        # Add SSL if requested
        if use_ssl:
            connection_params['ssl_disabled'] = False
            connection_params['ssl_verify_cert'] = False
            connection_params['ssl_verify_identity'] = False
        
        print(f"ℹ Attempting to connect to MySQL at {host}:{port}...")
        connection = mysql.connector.connect(**connection_params)
        print(f"✓ Connected to Drupal MySQL database: {database} on {host}:{port}")
        return connection
        
    except MySQLError as e:
        error_code = e.errno if hasattr(e, 'errno') else None
        error_msg = str(e)
        
        print(f"\n✗ Error connecting to Drupal MySQL: {e}")
        print(f"   Host: {host}, Database: {database}, Port: {port}")
        
        # Provide specific troubleshooting based on error
        if error_code == 2013 or "Lost connection" in error_msg or "reading initial communication packet" in error_msg:
            print("\n🔍 Troubleshooting tips:")
            print("   1. Check if MySQL allows remote connections:")
            print("      - MySQL server might only allow localhost connections")
            print("      - Check MySQL bind-address in my.cnf (should be 0.0.0.0 or your IP)")
            print("   2. Verify firewall settings:")
            print(f"      - Port {port} might be blocked by firewall")
            print("      - Check if your IP is whitelisted on the MySQL server")
            print("   3. Test connectivity:")
            print(f"      - Try: telnet {host} {port} (or: Test-NetConnection {host} -Port {port} on Windows)")
            print("   4. Check if you need SSH tunnel:")
            print("      - Some hosts require SSH tunneling for MySQL access")
            print("   5. Verify credentials:")
            print("      - Ensure username and password are correct")
            print("      - Check if user has remote access privileges")
            print("   6. Try using SSL connection:")
            print("      - Some MySQL servers require SSL: add --use-ssl flag")
        elif error_code == 2003 or "Can't connect" in error_msg:
            print("\n🔍 Troubleshooting tips:")
            print(f"   1. Verify hostname '{host}' is correct and resolvable")
            print(f"   2. Check if port {port} is correct")
            print("   3. Ensure MySQL server is running")
        elif error_code == 1045:
            print("\n🔍 Troubleshooting tips:")
            print("   1. Verify username and password are correct")
            print("   2. Check if user exists and has proper permissions")
        
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print(f"   Host: {host}, Database: {database}, Port: {port}")
        sys.exit(1)


def get_supabase_client(supabase_url: str, supabase_key: str) -> Client:
    """Create Supabase client using URL and API key"""
    try:
        if not supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not supabase_key:
            raise ValueError("SUPABASE_KEY is required")
        
        client = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase")
        return client
    except Exception as e:
        print(f"✗ Error connecting to Supabase: {e}")
        print("   Make sure SUPABASE_URL and SUPABASE_KEY are set correctly")
        sys.exit(1)


def fetch_blogs_from_drupal(mysql_conn) -> List[Dict]:
    """Fetch all blog posts from Drupal"""
    cursor = mysql_conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            n.nid,
            n.vid,
            n.title,
            n.uid,
            n.status,
            n.created,
            n.changed,
            n.promote,
            n.sticky,
            b.body_value,
            b.body_summary,
            b.body_format,
            u.name as author_name
        FROM node n
        LEFT JOIN field_data_body b ON b.entity_id = n.nid 
            AND b.entity_type = 'node' 
            AND b.bundle = 'blog'
            AND b.deleted = 0
        LEFT JOIN users u ON u.uid = n.uid
        WHERE n.type = 'blog'
        ORDER BY n.created DESC
    """
    
    cursor.execute(query)
    blogs = cursor.fetchall()
    cursor.close()
    
    print(f"✓ Found {len(blogs)} blog posts in Drupal")
    return blogs


def fetch_faqs_from_drupal(mysql_conn) -> List[Dict]:
    """Fetch all FAQ entries from Drupal"""
    cursor = mysql_conn.cursor(dictionary=True)
    
    # Try to find FAQ content - could be 'page', 'faq', or 'landing_page' type
    # with title containing FAQ or in a specific category
    query = """
        SELECT 
            n.nid,
            n.vid,
            n.title,
            n.uid,
            n.status,
            n.created,
            n.changed,
            n.promote,
            b.body_value,
            b.body_summary,
            b.body_format,
            u.name as author_name
        FROM node n
        LEFT JOIN field_data_body b ON b.entity_id = n.nid 
            AND b.entity_type = 'node'
            AND b.deleted = 0
        LEFT JOIN users u ON u.uid = n.uid
        WHERE (
            n.type = 'faq' 
            OR (n.type = 'page' AND (n.title LIKE '%FAQ%' OR n.title LIKE '%faq%' OR n.title LIKE '%Question%'))
            OR (n.type = 'landing_page' AND (n.title LIKE '%FAQ%' OR n.title LIKE '%faq%'))
        )
        AND n.status = 1
        ORDER BY n.created DESC
    """
    
    cursor.execute(query)
    faqs = cursor.fetchall()
    cursor.close()
    
    print(f"✓ Found {len(faqs)} FAQ entries in Drupal")
    return faqs


def fetch_blog_comments_from_drupal(mysql_conn, blog_nids: List[int]) -> List[Dict]:
    """Fetch comments for blog posts"""
    if not blog_nids:
        return []
    
    cursor = mysql_conn.cursor(dictionary=True)
    placeholders = ','.join(['%s'] * len(blog_nids))
    
    query = f"""
        SELECT 
            c.cid,
            c.nid,
            c.uid,
            c.subject,
            c.comment_body_value as comment_body,
            c.status,
            c.created,
            c.changed,
            u.name as author_name,
            u.mail as author_email,
            u.homepage as author_url
        FROM comment c
        LEFT JOIN field_data_comment_body cb ON cb.entity_id = c.cid
            AND cb.entity_type = 'comment'
            AND cb.deleted = 0
        LEFT JOIN users u ON u.uid = c.uid
        WHERE c.nid IN ({placeholders})
        AND c.status = 1
        ORDER BY c.created ASC
    """
    
    cursor.execute(query, blog_nids)
    comments = cursor.fetchall()
    cursor.close()
    
    print(f"✓ Found {len(comments)} blog comments in Drupal")
    return comments


def insert_blogs_to_supabase(supabase: Client, blogs: List[Dict]):
    """Insert blog posts into Supabase"""
    inserted = 0
    skipped = 0
    
    for blog in blogs:
        try:
            # Check if blog already exists
            existing = supabase.from_('blogs').select('id').eq('drupal_nid', blog['nid']).execute()
            if existing.data:
                skipped += 1
                continue
            
            # Generate slug
            blog_slug = slugify(blog['title'])
            
            # Ensure unique slug
            slug_check = supabase.from_('blogs').select('id').eq('slug', blog_slug).execute()
            if slug_check.data:
                blog_slug = f"{blog_slug}-{blog['nid']}"
            
            # Convert timestamps
            created_at = datetime.fromtimestamp(blog['created']).isoformat() if blog['created'] else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(blog['changed']).isoformat() if blog['changed'] else created_at
            published_at = created_at if blog['status'] == 1 else None
            
            # Insert blog
            data = {
                'title': blog['title'],
                'slug': blog_slug,
                'body': blog.get('body_value', ''),
                'body_summary': blog.get('body_summary', ''),
                'body_format': blog.get('body_format', 'filtered_html'),
                'author_name': blog.get('author_name', ''),
                'status': 'published' if blog['status'] == 1 else 'draft',
                'is_promoted': bool(blog.get('promote', 0)),
                'is_sticky': bool(blog.get('sticky', 0)),
                'drupal_nid': blog['nid'],
                'drupal_vid': blog['vid'],
                'created_at': created_at,
                'updated_at': updated_at,
                'published_at': published_at
            }
            
            result = supabase.from_('blogs').insert(data).execute()
            if result.data:
                inserted += 1
            
        except Exception as e:
            print(f"✗ Error inserting blog {blog.get('nid')}: {e}")
            continue
    
    print(f"✓ Inserted {inserted} blogs, skipped {skipped} duplicates")


def insert_faqs_to_supabase(supabase: Client, faqs: List[Dict]):
    """Insert FAQ entries into Supabase"""
    inserted = 0
    skipped = 0
    
    for faq in faqs:
        try:
            # Check if FAQ already exists
            existing = supabase.from_('faqs').select('id').eq('drupal_nid', faq['nid']).execute()
            if existing.data:
                skipped += 1
                continue
            
            # Extract question and answer from title and body
            question = faq['title']
            answer = faq.get('body_value', '')
            
            # Generate slug
            faq_slug = slugify(question)
            
            # Ensure unique slug
            slug_check = supabase.from_('faqs').select('id').eq('slug', faq_slug).execute()
            if slug_check.data:
                faq_slug = f"{faq_slug}-{faq['nid']}"
            
            # Convert timestamps
            created_at = datetime.fromtimestamp(faq['created']).isoformat() if faq['created'] else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(faq['changed']).isoformat() if faq['changed'] else created_at
            published_at = created_at if faq['status'] == 1 else None
            
            # Insert FAQ
            data = {
                'question': question,
                'answer': answer,
                'slug': faq_slug,
                'status': 'published' if faq['status'] == 1 else 'draft',
                'is_featured': bool(faq.get('promote', 0)),
                'drupal_nid': faq['nid'],
                'drupal_vid': faq['vid'],
                'created_at': created_at,
                'updated_at': updated_at,
                'published_at': published_at
            }
            
            result = supabase.from_('faqs').insert(data).execute()
            if result.data:
                inserted += 1
            
        except Exception as e:
            print(f"✗ Error inserting FAQ {faq.get('nid')}: {e}")
            continue
    
    print(f"✓ Inserted {inserted} FAQs, skipped {skipped} duplicates")


def insert_comments_to_supabase(supabase: Client, comments: List[Dict], blog_nid_to_uuid: Dict[int, str]):
    """Insert blog comments into Supabase"""
    if not comments:
        return
    
    # Get blog UUIDs for the comments
    blog_nids = list(set([c['nid'] for c in comments]))
    blog_map = {}
    
    # Fetch blogs in batches (Supabase has limits on IN clause size)
    batch_size = 100
    for i in range(0, len(blog_nids), batch_size):
        batch = blog_nids[i:i + batch_size]
        result = supabase.from_('blogs').select('drupal_nid, id').in_('drupal_nid', batch).execute()
        for row in result.data:
            blog_map[row['drupal_nid']] = row['id']
    
    inserted = 0
    skipped = 0
    
    for comment in comments:
        try:
            # Check if comment already exists
            existing = supabase.from_('blog_comments').select('id').eq('drupal_cid', comment['cid']).execute()
            if existing.data:
                skipped += 1
                continue
            
            blog_uuid = blog_map.get(comment['nid'])
            if not blog_uuid:
                skipped += 1
                continue
            
            # Convert timestamps
            created_at = datetime.fromtimestamp(comment['created']).isoformat() if comment['created'] else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(comment['changed']).isoformat() if comment['changed'] else created_at
            
            # Determine status
            status_map = {
                0: 'pending',
                1: 'approved',
                2: 'spam'
            }
            status = status_map.get(comment.get('status', 1), 'approved')
            
            # Insert comment
            data = {
                'blog_id': blog_uuid,
                'author_name': comment.get('author_name', 'Anonymous'),
                'author_email': comment.get('author_email', ''),
                'author_url': comment.get('author_url', ''),
                'subject': comment.get('subject', ''),
                'comment_body': comment.get('comment_body', ''),
                'status': status,
                'drupal_cid': comment['cid'],
                'created_at': created_at,
                'updated_at': updated_at
            }
            
            result = supabase.from_('blog_comments').insert(data).execute()
            if result.data:
                inserted += 1
            
        except Exception as e:
            print(f"✗ Error inserting comment {comment.get('cid')}: {e}")
            continue
    
    print(f"✓ Inserted {inserted} comments, skipped {skipped} duplicates")


def main():
    parser = argparse.ArgumentParser(description='Migrate Blog and FAQ data from Drupal to Supabase')
    
    # Drupal MySQL connection
    parser.add_argument('--drupal-host', default=os.getenv('DRUPAL_DB_HOST', 'localhost'),
                       help='Drupal MySQL host')
    parser.add_argument('--drupal-db', default=os.getenv('DRUPAL_DB_NAME', 'drupal'),
                       help='Drupal MySQL database name')
    parser.add_argument('--drupal-user', default=os.getenv('DRUPAL_DB_USER', 'root'),
                       help='Drupal MySQL user')
    parser.add_argument('--drupal-password', default=os.getenv('DRUPAL_DB_PASSWORD', ''),
                       help='Drupal MySQL password')
    parser.add_argument('--drupal-port', type=int, default=int(os.getenv('DRUPAL_DB_PORT', 3306)),
                       help='Drupal MySQL port')
    parser.add_argument('--drupal-connection-timeout', type=int, default=int(os.getenv('DRUPAL_DB_TIMEOUT', 10)),
                       help='MySQL connection timeout in seconds')
    parser.add_argument('--use-ssl', action='store_true', default=os.getenv('DRUPAL_DB_USE_SSL', '').lower() == 'true',
                       help='Use SSL for MySQL connection')
    
    # Supabase connection
    parser.add_argument('--supabase-url', default=os.getenv('SUPABASE_URL', ''),
                       help='Supabase project URL')
    parser.add_argument('--supabase-key', default=os.getenv('SUPABASE_KEY', ''),
                       help='Supabase API key (anon or service role key)')
    
    # Migration options
    parser.add_argument('--migrate-blogs', action='store_true', default=True,
                       help='Migrate blog posts')
    parser.add_argument('--migrate-faqs', action='store_true', default=True,
                       help='Migrate FAQ entries')
    parser.add_argument('--migrate-comments', action='store_true', default=False,
                       help='Migrate blog comments')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run - don\'t actually insert data')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Drupal to Supabase Migration - Blog & FAQ")
    print("=" * 60)
    
    # Connect to Drupal
    mysql_conn = get_drupal_connection(
        args.drupal_host,
        args.drupal_db,
        args.drupal_user,
        args.drupal_password,
        args.drupal_port,
        args.drupal_connection_timeout,
        args.use_ssl
    )
    
    # Connect to Supabase
    supabase = get_supabase_client(args.supabase_url, args.supabase_key)
    
    try:
        # Migrate Blogs
        if args.migrate_blogs:
            print("\n--- Migrating Blog Posts ---")
            blogs = fetch_blogs_from_drupal(mysql_conn)
            if blogs and not args.dry_run:
                insert_blogs_to_supabase(supabase, blogs)
                
                # Migrate comments if requested
                if args.migrate_comments:
                    print("\n--- Migrating Blog Comments ---")
                    blog_nids = [b['nid'] for b in blogs]
                    comments = fetch_blog_comments_from_drupal(mysql_conn, blog_nids)
                    if comments:
                        # Get blog UUID mapping
                        blog_nid_to_uuid = {}
                        batch_size = 100
                        for i in range(0, len(blog_nids), batch_size):
                            batch = blog_nids[i:i + batch_size]
                            result = supabase.from_('blogs').select('drupal_nid, id').in_('drupal_nid', batch).execute()
                            for row in result.data:
                                blog_nid_to_uuid[row['drupal_nid']] = row['id']
                        insert_comments_to_supabase(supabase, comments, blog_nid_to_uuid)
            elif args.dry_run:
                print(f"  [DRY RUN] Would migrate {len(blogs)} blog posts")
        
        # Migrate FAQs
        if args.migrate_faqs:
            print("\n--- Migrating FAQ Entries ---")
            faqs = fetch_faqs_from_drupal(mysql_conn)
            if faqs and not args.dry_run:
                insert_faqs_to_supabase(supabase, faqs)
            elif args.dry_run:
                print(f"  [DRY RUN] Would migrate {len(faqs)} FAQ entries")
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        mysql_conn.close()
        print("\n✓ Database connections closed")


if __name__ == '__main__':
    main()

