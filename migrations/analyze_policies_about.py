#!/usr/bin/env python3
"""
Quick script to analyze the SQL dump for policy and about us pages
"""

import re
from collections import defaultdict

def analyze_sql_file(sql_file_path: str):
    """Analyze SQL file to find policy and about us related content"""
    print(f"📖 Analyzing SQL file: {sql_file_path}")
    
    node_types = defaultdict(int)
    policy_about_nodes = []
    
    # Keywords to search for
    keywords = ['policy', 'privacy', 'terms', 'cancellation', 'refund', 'about', 'about-us', 'about_us']
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_insert = None
            buffer = []
            
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('--') or line.startswith('/*'):
                    continue
                
                # Check if this is an INSERT statement for node table
                if line.upper().startswith('INSERT INTO `node`'):
                    if buffer:
                        full_statement = ' '.join(buffer)
                        # Try to extract node data
                        if any(kw in full_statement.lower() for kw in keywords):
                            policy_about_nodes.append((line_num, full_statement[:200]))
                        buffer = []
                    
                    buffer = [line]
                elif buffer and not line.endswith(';'):
                    buffer.append(line)
                elif buffer and line.endswith(';'):
                    buffer.append(line)
                    full_statement = ' '.join(buffer)
                    if any(kw in full_statement.lower() for kw in keywords):
                        policy_about_nodes.append((line_num, full_statement[:200]))
                    buffer = []
                
                # Extract node types
                match = re.search(r"type.*=.*['\"]([^'\"]+)['\"]", line, re.I)
                if match:
                    node_type = match.group(1)
                    node_types[node_type] += 1
                
                # Progress indicator
                if line_num % 100000 == 0:
                    print(f"   Processed {line_num:,} lines...")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    print(f"\n✓ Analysis complete")
    print(f"\n📊 Node types found:")
    for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"   {node_type}: {count}")
    
    print(f"\n📄 Found {len(policy_about_nodes)} potential policy/about us nodes")
    if policy_about_nodes:
        print("\nFirst few matches:")
        for line_num, snippet in policy_about_nodes[:10]:
            print(f"   Line {line_num}: {snippet}...")

if __name__ == '__main__':
    import sys
    sql_file = sys.argv[1] if len(sys.argv) > 1 else 'cabinre_drupal7.sql'
    analyze_sql_file(sql_file)


