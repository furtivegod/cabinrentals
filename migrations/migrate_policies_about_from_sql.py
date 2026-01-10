#!/usr/bin/env python3
"""
Migration script to migrate Policies and About Us pages from Drupal SQL dump file to Supabase

Usage:
    python migrate_policies_about_from_sql.py --sql-file cabinre_drupal7.sql \
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
    """Parse SQL file and extract node, field_data_body, and users data"""
    print(f"📖 Reading SQL file: {sql_file_path}")
    
    data = {
        'nodes': [],
        'body_fields': [],
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
    print(f"   Found {len(data['nodes'])} relevant nodes")
    print(f"   Found {len(data['body_fields'])} body field records")
    print(f"   Found {len(data['users'])} users")
    
    return data


def process_parsed_data(parsed: Dict, data: Dict):
    """Process parsed INSERT statement data"""
    table = parsed['table']
    rows = parsed['rows']
    
    if table == 'node':
        for row in rows:
            # Process policy and about us nodes
            node_type = row.get('type', '')
            title = row.get('title', '').lower()
            
            # Check if it's a policy or about us page
            is_policy = any(keyword in title for keyword in ['policy', 'privacy', 'terms', 'cancellation', 'refund', 'agreement'])
            is_about = any(keyword in title for keyword in ['about', 'about-us', 'about_us']) or 'about' in node_type.lower()
            
            # Also check for 'page' type nodes that might be policies or about us
            if node_type in ('page', 'webform', 'landing_page') or is_policy or is_about:
                data['nodes'].append(row)
    elif table == 'field_data_body':
        for row in rows:
            # Only process non-deleted body fields for nodes
            if row.get('deleted', 0) == 0 and row.get('entity_type') == 'node':
                data['body_fields'].append(row)
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


def detect_policy_type(title: str) -> Optional[str]:
    """Detect policy type from title"""
    title_lower = title.lower()
    
    if 'privacy' in title_lower:
        return 'privacy'
    elif 'terms' in title_lower or 'term' in title_lower:
        return 'terms'
    elif 'cancellation' in title_lower:
        return 'cancellation'
    elif 'refund' in title_lower:
        return 'refund'
    elif 'agreement' in title_lower:
        return 'agreement'
    elif 'policy' in title_lower:
        return 'general'
    
    return None


def detect_about_section(title: str) -> Optional[str]:
    """Detect about us section from title"""
    title_lower = title.lower()
    
    if 'history' in title_lower:
        return 'history'
    elif 'team' in title_lower or 'staff' in title_lower:
        return 'team'
    elif 'mission' in title_lower or 'vision' in title_lower:
        return 'mission'
    elif 'contact' in title_lower:
        return 'contact'
    elif 'about' in title_lower and ('us' in title_lower or 'company' in title_lower or 'our' in title_lower):
        return 'main'
    
    return 'main'  # Default to main


def process_policies_and_about(supabase: Client, data: Dict):
    """Process and insert policies and about us pages into Supabase"""
    # Build lookup maps - use both entity_id and revision_id for matching
    body_map_by_entity = {}  # entity_id -> list of body records
    body_map_by_revision = {}  # (entity_id, revision_id) -> body record
    
    for body in data['body_fields']:
        entity_id = body.get('entity_id')
        revision_id = body.get('revision_id')
        bundle = body.get('bundle', '')
        entity_type = body.get('entity_type', 'node')
        
        # Only process node body fields
        if entity_id and entity_type == 'node':
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
    
    # Separate policies and about us pages
    policies = []
    about_pages = []
    nodes_without_body = []
    
    for node in data['nodes']:
        node_type = node.get('type', '')
        nid = node.get('nid')
        vid = node.get('vid')
        title = node.get('title', '')
        title_lower = title.lower()
        
        if not nid:
            continue
        
        # Determine if it's a policy or about us page
        is_policy = any(keyword in title_lower for keyword in ['policy', 'privacy', 'terms', 'cancellation', 'refund', 'agreement'])
        is_about = any(keyword in title_lower for keyword in ['about', 'about-us', 'about_us']) or 'about' in node_type.lower()
        
        # Skip if neither
        if not is_policy and not is_about:
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
            nodes_without_body.append((nid, node_type, title))
        
        # Get author name
        uid = node.get('uid', 0)
        author_name = data['users'].get(uid, {}).get('name', '')
        
        node_data = {
            'nid': nid,
            'vid': vid,
            'title': title,
            'uid': uid,
            'status': node.get('status', 0),
            'created': node.get('created', 0),
            'changed': node.get('changed', 0),
            'promote': node.get('promote', 0),
            'body_value': body_data.get('body_value', ''),
            'body_summary': body_data.get('body_summary', ''),
            'body_format': body_data.get('body_format', 'filtered_html'),
            'author_name': author_name
        }
        
        if is_policy:
            policies.append(node_data)
        elif is_about:
            about_pages.append(node_data)
    
    if nodes_without_body:
        print(f"   ⚠ Warning: {len(nodes_without_body)} nodes have empty body content")
        if len(nodes_without_body) <= 10:
            for nid, ntype, title in nodes_without_body[:10]:
                print(f"      - Node {nid} ({ntype}): {title[:50]}")
    
    print(f"\n📝 Found {len(policies)} policy pages and {len(about_pages)} about us pages")
    
    return policies, about_pages


def insert_policies_to_supabase(supabase: Client, policies: List[Dict]):
    """Insert policy pages into Supabase"""
    inserted = 0
    skipped = 0
    
    for policy in policies:
        try:
            # Check if policy already exists
            existing = supabase.from_('policies').select('id').eq('drupal_nid', policy['nid']).execute()
            if existing.data:
                skipped += 1
                continue
            
            # Generate slug
            policy_slug = slugify(policy['title'])
            
            # Ensure unique slug
            slug_check = supabase.from_('policies').select('id').eq('slug', policy_slug).execute()
            if slug_check.data:
                policy_slug = f"{policy_slug}-{policy['nid']}"
            
            # Detect policy type
            policy_type = detect_policy_type(policy['title'])
            
            # Convert timestamps
            created_at = datetime.fromtimestamp(policy['created']).isoformat() if policy['created'] else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(policy['changed']).isoformat() if policy['changed'] else created_at
            published_at = created_at if policy['status'] == 1 else None
            
            # Insert policy
            data = {
                'title': policy['title'],
                'slug': policy_slug,
                'body': policy.get('body_value', ''),
                'body_summary': policy.get('body_summary', ''),
                'body_format': policy.get('body_format', 'filtered_html'),
                'policy_type': policy_type,
                'author_name': policy.get('author_name', ''),
                'status': 'published' if policy['status'] == 1 else 'draft',
                'is_featured': bool(policy.get('promote', 0)),
                'drupal_nid': policy['nid'],
                'drupal_vid': policy['vid'],
                'created_at': created_at,
                'updated_at': updated_at,
                'published_at': published_at
            }
            
            result = supabase.from_('policies').insert(data).execute()
            if result.data:
                inserted += 1
            
        except Exception as e:
            print(f"✗ Error inserting policy {policy.get('nid')}: {e}")
            continue
    
    print(f"✓ Inserted {inserted} policies, skipped {skipped} duplicates")


def insert_about_pages_to_supabase(supabase: Client, about_pages: List[Dict]):
    """Insert about us pages into Supabase"""
    inserted = 0
    skipped = 0
    
    for about in about_pages:
        try:
            # Check if about page already exists
            existing = supabase.from_('about_us').select('id').eq('drupal_nid', about['nid']).execute()
            if existing.data:
                skipped += 1
                continue
            
            # Generate slug
            about_slug = slugify(about['title'])
            
            # Ensure unique slug
            slug_check = supabase.from_('about_us').select('id').eq('slug', about_slug).execute()
            if slug_check.data:
                about_slug = f"{about_slug}-{about['nid']}"
            
            # Detect section
            section = detect_about_section(about['title'])
            
            # Convert timestamps
            created_at = datetime.fromtimestamp(about['created']).isoformat() if about['created'] else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(about['changed']).isoformat() if about['changed'] else created_at
            published_at = created_at if about['status'] == 1 else None
            
            # Insert about page
            data = {
                'title': about['title'],
                'slug': about_slug,
                'body': about.get('body_value', ''),
                'body_summary': about.get('body_summary', ''),
                'body_format': about.get('body_format', 'filtered_html'),
                'section': section,
                'author_name': about.get('author_name', ''),
                'status': 'published' if about['status'] == 1 else 'draft',
                'is_featured': bool(about.get('promote', 0)),
                'drupal_nid': about['nid'],
                'drupal_vid': about['vid'],
                'created_at': created_at,
                'updated_at': updated_at,
                'published_at': published_at
            }
            
            result = supabase.from_('about_us').insert(data).execute()
            if result.data:
                inserted += 1
            
        except Exception as e:
            print(f"✗ Error inserting about page {about.get('nid')}: {e}")
            continue
    
    print(f"✓ Inserted {inserted} about us pages, skipped {skipped} duplicates")


def main():
    parser = argparse.ArgumentParser(description='Migrate Policies and About Us pages from Drupal SQL dump to Supabase')
    
    parser.add_argument('--sql-file', default='cabinre_drupal7.sql',
                       help='Path to Drupal SQL dump file')
    parser.add_argument('--supabase-url', default=os.getenv('SUPABASE_URL', ''),
                       help='Supabase project URL')
    parser.add_argument('--supabase-key', default=os.getenv('SUPABASE_KEY', ''),
                       help='Supabase API key (anon or service role key)')
    
    # Migration options
    parser.add_argument('--migrate-policies', action='store_true', default=True,
                       help='Migrate policy pages')
    parser.add_argument('--migrate-about', action='store_true', default=True,
                       help='Migrate about us pages')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run - parse SQL but don\'t insert data')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Drupal SQL to Supabase Migration - Policies & About Us")
    print("=" * 60)
    
    # Parse SQL file
    data = parse_sql_file(args.sql_file)
    
    # Connect to Supabase
    supabase = get_supabase_client(args.supabase_url, args.supabase_key)
    
    try:
        # Process policies and about us pages
        policies, about_pages = process_policies_and_about(supabase, data)
        
        # Migrate Policies
        if args.migrate_policies and policies:
            print("\n--- Migrating Policy Pages ---")
            if not args.dry_run:
                insert_policies_to_supabase(supabase, policies)
            else:
                print(f"  [DRY RUN] Would migrate {len(policies)} policy pages")
        
        # Migrate About Us Pages
        if args.migrate_about and about_pages:
            print("\n--- Migrating About Us Pages ---")
            if not args.dry_run:
                insert_about_pages_to_supabase(supabase, about_pages)
            else:
                print(f"  [DRY RUN] Would migrate {len(about_pages)} about us pages")
        
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


