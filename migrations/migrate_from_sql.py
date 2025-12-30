#!/usr/bin/env python3
"""
Migration script to migrate Blog and FAQ data from Drupal SQL dump file to Supabase

Usage:
    python migrate_from_sql.py --sql-file cabinre_drupal7.sql \
                               --supabase-url https://xxx.supabase.co \
                               --supabase-key your_key

Requirements:
    pip install supabase python-dotenv
"""

import argparse
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional, Set
from supabase import create_client, Client
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


def parse_sql_value(value: str) -> any:
    """Parse a SQL value, handling NULL, strings, and numbers"""
    if not value:
        return None
    
    value = value.strip()
    
    if not value or value.upper() == 'NULL':
        return None
    
    # Handle quoted strings
    if value.startswith("'") and value.endswith("'"):
        # Remove outer quotes and handle escaped quotes
        unquoted = value[1:-1]
        # Handle MySQL-style escaped quotes ('')
        unquoted = unquoted.replace("''", "'")
        # Handle backslash-escaped quotes
        unquoted = unquoted.replace("\\'", "'")
        # Handle other escape sequences
        unquoted = unquoted.replace("\\n", "\n")
        unquoted = unquoted.replace("\\r", "\r")
        unquoted = unquoted.replace("\\t", "\t")
        unquoted = unquoted.replace("\\\\", "\\")
        return unquoted
    
    if value.startswith('"') and value.endswith('"'):
        unquoted = value[1:-1]
        unquoted = unquoted.replace('""', '"')
        unquoted = unquoted.replace('\\"', '"')
        unquoted = unquoted.replace("\\n", "\n")
        unquoted = unquoted.replace("\\r", "\r")
        unquoted = unquoted.replace("\\t", "\t")
        unquoted = unquoted.replace("\\\\", "\\")
        return unquoted
    
    # Try to parse as number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_insert_statement(line: str) -> Optional[Dict]:
    """Parse an INSERT statement and return table name and values"""
    # Match: INSERT INTO `table` (`col1`, `col2`) VALUES (...)
    match = re.match(r'INSERT INTO `(\w+)`\s*\(([^)]+)\)\s*VALUES\s*(.+)', line, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    
    table_name = match.group(1)
    columns_str = match.group(2)
    values_str = match.group(3)
    
    # Parse column names
    columns = [col.strip().strip('`') for col in columns_str.split(',')]
    
    # Parse values - handle multi-line VALUES
    # Remove trailing semicolon and whitespace
    values_str = values_str.rstrip(';').strip()
    
    # Split rows - handle multi-line INSERT statements
    rows = []
    if values_str.startswith('('):
        # More robust parsing: find all complete value tuples
        # This handles cases where values contain parentheses, quotes, etc.
        i = 0
        while i < len(values_str):
            if values_str[i] == '(':
                # Find matching closing parenthesis
                depth = 1
                start = i + 1
                i += 1
                while i < len(values_str) and depth > 0:
                    if values_str[i] == '(':
                        depth += 1
                    elif values_str[i] == ')':
                        depth -= 1
                    elif values_str[i] in ("'", '"'):
                        # Skip quoted strings
                        quote_char = values_str[i]
                        i += 1
                        while i < len(values_str):
                            if values_str[i] == quote_char and values_str[i-1] != '\\':
                                break
                            i += 1
                    i += 1
                
                if depth == 0:
                    # Extract the row string
                    row_str = values_str[start:i-1]
                    values = parse_row_values(row_str)
                    
                    if len(values) == len(columns):
                        rows.append(dict(zip(columns, values)))
                    elif len(values) > 0:
                        # Partial match - might be due to parsing issues
                        # Try to pad with None or truncate
                        if len(values) < len(columns):
                            values.extend([None] * (len(columns) - len(values)))
                            rows.append(dict(zip(columns, values[:len(columns)])))
            else:
                i += 1
    
    return {
        'table': table_name,
        'columns': columns,
        'rows': rows
    }


def parse_row_values(row_str: str) -> List:
    """Parse a single row of values from an INSERT statement"""
    values = []
    current = ""
    in_quotes = False
    quote_char = None
    paren_depth = 0
    escape_next = False
    
    i = 0
    while i < len(row_str):
        char = row_str[i]
        
        if escape_next:
            current += char
            escape_next = False
        elif char == '\\' and in_quotes:
            escape_next = True
            current += char
        elif char in ("'", '"') and not escape_next:
            if not in_quotes:
                in_quotes = True
                quote_char = char
                current += char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
                current += char
            else:
                current += char
        elif char == '(' and not in_quotes:
            paren_depth += 1
            current += char
        elif char == ')' and not in_quotes:
            paren_depth -= 1
            current += char
        elif char == ',' and not in_quotes and paren_depth == 0:
            values.append(parse_sql_value(current))
            current = ""
        else:
            current += char
        
        i += 1
    
    # Add the last value
    if current.strip():
        values.append(parse_sql_value(current))
    
    return values


def parse_sql_file(sql_file_path: str) -> Dict[str, List[Dict]]:
    """Parse SQL file and extract node, field_data_body, comment, and users data"""
    print(f"📖 Reading SQL file: {sql_file_path}")
    
    data = {
        'nodes': [],
        'body_fields': [],
        'comments': [],
        'users': {}
    }
    
    current_statement = None
    current_table = None
    statement_buffer = []
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('--') or line.startswith('/*'):
                    continue
                
                # Check if this is an INSERT statement
                if line.upper().startswith('INSERT INTO'):
                    # Process any previous buffered statement
                    if statement_buffer:
                        full_statement = ' '.join(statement_buffer)
                        parsed = parse_insert_statement(full_statement)
                        if parsed:
                            process_parsed_data(parsed, data)
                        statement_buffer = []
                    
                    # Start new statement
                    statement_buffer = [line]
                    current_statement = 'INSERT'
                elif current_statement == 'INSERT':
                    # Continue building INSERT statement (multi-line)
                    statement_buffer.append(line)
                    # Check if statement is complete (ends with ;)
                    if line.endswith(';'):
                        full_statement = ' '.join(statement_buffer)
                        parsed = parse_insert_statement(full_statement)
                        if parsed:
                            process_parsed_data(parsed, data)
                        statement_buffer = []
                        current_statement = None
                
                # Progress indicator
                if line_num % 100000 == 0:
                    print(f"   Processed {line_num:,} lines...")
    
    except FileNotFoundError:
        print(f"✗ SQL file not found: {sql_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading SQL file: {e}")
        sys.exit(1)
    
    # Process any remaining buffered statement
    if statement_buffer:
        full_statement = ' '.join(statement_buffer)
        parsed = parse_insert_statement(full_statement)
        if parsed:
            process_parsed_data(parsed, data)
    
    print(f"✓ Parsed SQL file")
    print(f"   Found {len(data['nodes'])} nodes")
    print(f"   Found {len(data['body_fields'])} body field records")
    
    # Count body fields by bundle
    body_by_bundle = {}
    for body in data['body_fields']:
        bundle = body.get('bundle', 'unknown')
        body_by_bundle[bundle] = body_by_bundle.get(bundle, 0) + 1
    
    if body_by_bundle:
        print(f"   Body fields by type: {dict(body_by_bundle)}")
    
    print(f"   Found {len(data['comments'])} comments")
    print(f"   Found {len(data['users'])} users")
    
    return data


def process_parsed_data(parsed: Dict, data: Dict):
    """Process parsed INSERT statement data"""
    table = parsed['table']
    rows = parsed['rows']
    
    if table == 'node':
        for row in rows:
            # Only process blog and FAQ nodes
            node_type = row.get('type', '')
            if node_type in ('blog', 'faq', 'page', 'landing_page'):
                data['nodes'].append(row)
    elif table == 'field_data_body':
        for row in rows:
            # Only process non-deleted body fields for nodes
            if row.get('deleted', 0) == 0 and row.get('entity_type') == 'node':
                data['body_fields'].append(row)
    elif table == 'comment':
        for row in rows:
            data['comments'].append(row)
    elif table == 'users':
        for row in rows:
            uid = row.get('uid')
            if uid:
                data['users'][uid] = row


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


def process_blogs_and_faqs(supabase: Client, data: Dict):
    """Process and insert blogs and FAQs into Supabase"""
    # Build lookup maps - use both entity_id and revision_id for matching
    # Key format: (entity_id, revision_id) or just entity_id as fallback
    body_map_by_entity = {}  # entity_id -> list of body records
    body_map_by_revision = {}  # (entity_id, revision_id) -> body record
    
    for body in data['body_fields']:
        entity_id = body.get('entity_id')
        revision_id = body.get('revision_id')
        bundle = body.get('bundle', '')
        entity_type = body.get('entity_type', 'node')
        
        # Only process node body fields for relevant bundles
        if entity_id and entity_type == 'node' and bundle in ('blog', 'faq', 'page', 'landing_page'):
            # Store by entity_id (for fallback)
            if entity_id not in body_map_by_entity:
                body_map_by_entity[entity_id] = []
            body_map_by_entity[entity_id].append(body)
            
            # Store by (entity_id, revision_id) for exact matching
            if revision_id:
                key = (entity_id, revision_id)
                # Keep the latest/most relevant body record
                if key not in body_map_by_revision:
                    body_map_by_revision[key] = body
                else:
                    # If multiple exist, prefer non-empty body_value
                    existing = body_map_by_revision[key]
                    if body.get('body_value') and not existing.get('body_value'):
                        body_map_by_revision[key] = body
    
    print(f"   Built body map: {len(body_map_by_entity)} entities, {len(body_map_by_revision)} revision matches")
    
    # Separate blogs and FAQs
    blogs = []
    faqs = []
    nodes_without_body = []
    
    for node in data['nodes']:
        node_type = node.get('type', '')
        nid = node.get('nid')
        vid = node.get('vid')
        
        if not nid:
            continue
        
        # Try to get body content - first try exact revision match, then fallback to entity_id
        body_data = {}
        
        # First, try exact match by (entity_id, revision_id)
        if vid:
            key = (nid, vid)
            if key in body_map_by_revision:
                body_data = body_map_by_revision[key]
        
        # If no exact match, try to find any body for this entity_id
        if not body_data and nid in body_map_by_entity:
            body_records = body_map_by_entity[nid]
            # Prefer body records that match the node type
            matching_bodies = [b for b in body_records if b.get('bundle') == node_type]
            if matching_bodies:
                # Use the one with the most recent revision_id or non-empty body
                body_data = max(matching_bodies, key=lambda b: (
                    bool(b.get('body_value')),  # Prefer non-empty
                    b.get('revision_id', 0)  # Then most recent revision
                ))
            elif body_records:
                # Fallback to any body record
                body_data = max(body_records, key=lambda b: (
                    bool(b.get('body_value')),
                    b.get('revision_id', 0)
                ))
        
        # Track nodes without body for debugging
        if not body_data.get('body_value'):
            nodes_without_body.append((nid, node_type, node.get('title', '')))
        
        # Get author name
        uid = node.get('uid', 0)
        author_name = data['users'].get(uid, {}).get('name', '')
        
        node_data = {
            'nid': nid,
            'vid': vid,
            'title': node.get('title', ''),
            'uid': uid,
            'status': node.get('status', 0),
            'created': node.get('created', 0),
            'changed': node.get('changed', 0),
            'promote': node.get('promote', 0),
            'sticky': node.get('sticky', 0),
            'body_value': body_data.get('body_value', ''),
            'body_summary': body_data.get('body_summary', ''),
            'body_format': body_data.get('body_format', 'filtered_html'),
            'author_name': author_name
        }
        
        if node_type == 'blog':
            blogs.append(node_data)
        elif node_type in ('faq', 'page', 'landing_page'):
            # Check if it's an FAQ based on title
            title = node_data['title'].lower()
            if 'faq' in title or 'question' in title or 'faq' in node_type:
                faqs.append(node_data)
    
    if nodes_without_body:
        print(f"   ⚠ Warning: {len(nodes_without_body)} nodes have empty body content")
        if len(nodes_without_body) <= 10:
            for nid, ntype, title in nodes_without_body[:10]:
                print(f"      - Node {nid} ({ntype}): {title[:50]}")
    
    print(f"\n📝 Found {len(blogs)} blog posts and {len(faqs)} FAQ entries")
    
    return blogs, faqs


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


def insert_comments_to_supabase(supabase: Client, comments: List[Dict], blog_nid_to_uuid: Dict[int, str], users: Dict):
    """Insert blog comments into Supabase"""
    if not comments:
        return
    
    inserted = 0
    skipped = 0
    
    for comment in comments:
        try:
            nid = comment.get('nid')
            if not nid or nid not in blog_nid_to_uuid:
                skipped += 1
                continue
            
            # Check if comment already exists
            cid = comment.get('cid')
            if cid:
                existing = supabase.from_('blog_comments').select('id').eq('drupal_cid', cid).execute()
                if existing.data:
                    skipped += 1
                    continue
            
            blog_uuid = blog_nid_to_uuid[nid]
            
            # Convert timestamps
            created_at = datetime.fromtimestamp(comment['created']).isoformat() if comment.get('created') else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(comment['changed']).isoformat() if comment.get('changed') else created_at
            
            # Determine status
            status_map = {
                0: 'pending',
                1: 'approved',
                2: 'spam'
            }
            status = status_map.get(comment.get('status', 1), 'approved')
            
            # Get author info
            uid = comment.get('uid', 0)
            user = users.get(uid, {})
            
            # Insert comment
            comment_data = {
                'blog_id': blog_uuid,
                'author_name': comment.get('name', user.get('name', 'Anonymous')),
                'author_email': comment.get('mail', user.get('mail', '')),
                'author_url': comment.get('homepage', ''),
                'subject': comment.get('subject', ''),
                'comment_body': comment.get('comment_body_value', ''),
                'status': status,
                'drupal_cid': cid,
                'created_at': created_at,
                'updated_at': updated_at
            }
            
            result = supabase.from_('blog_comments').insert(comment_data).execute()
            if result.data:
                inserted += 1
            
        except Exception as e:
            print(f"✗ Error inserting comment {comment.get('cid')}: {e}")
            continue
    
    print(f"✓ Inserted {inserted} comments, skipped {skipped} duplicates")


def main():
    parser = argparse.ArgumentParser(description='Migrate Blog and FAQ data from Drupal SQL dump to Supabase')
    
    parser.add_argument('--sql-file', default='cabinre_drupal7.sql',
                       help='Path to Drupal SQL dump file')
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
                       help='Dry run - parse SQL but don\'t insert data')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Drupal SQL to Supabase Migration - Blog & FAQ")
    print("=" * 60)
    
    # Parse SQL file
    data = parse_sql_file(args.sql_file)
    
    # Connect to Supabase
    supabase = get_supabase_client(args.supabase_url, args.supabase_key)
    
    try:
        # Process blogs and FAQs
        blogs, faqs = process_blogs_and_faqs(supabase, data)
        
        # Migrate Blogs
        if args.migrate_blogs and blogs:
            print("\n--- Migrating Blog Posts ---")
            if not args.dry_run:
                insert_blogs_to_supabase(supabase, blogs)
            else:
                print(f"  [DRY RUN] Would migrate {len(blogs)} blog posts")
        
        # Migrate FAQs
        if args.migrate_faqs and faqs:
            print("\n--- Migrating FAQ Entries ---")
            if not args.dry_run:
                insert_faqs_to_supabase(supabase, faqs)
            else:
                print(f"  [DRY RUN] Would migrate {len(faqs)} FAQ entries")
        
        # Migrate Comments
        if args.migrate_comments and data['comments']:
            print("\n--- Migrating Blog Comments ---")
            if not args.dry_run:
                # Get blog UUID mapping
                blog_nids = [b['nid'] for b in blogs]
                blog_nid_to_uuid = {}
                batch_size = 100
                for i in range(0, len(blog_nids), batch_size):
                    batch = blog_nids[i:i + batch_size]
                    result = supabase.from_('blogs').select('drupal_nid, id').in_('drupal_nid', batch).execute()
                    for row in result.data:
                        blog_nid_to_uuid[row['drupal_nid']] = row['id']
                
                insert_comments_to_supabase(supabase, data['comments'], blog_nid_to_uuid, data['users'])
            else:
                print(f"  [DRY RUN] Would migrate {len(data['comments'])} comments")
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

