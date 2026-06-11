"""
Analyze top-performing assets for a brand and generate a 'Post-Mortem' report.

Usage:
    python scripts/generate_post_mortem.py --brand brand_name [--top 5]
"""
import sys
import json
import os
import argparse
sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    query_database, extract_text, DB_IDS, set_brand
)


def get_top_assets(brand: str, limit: int = 5) -> list:
    set_brand(brand)
    db_id = DB_IDS['marketing_assets']
    if not db_id:
        return []
    
    # Sort by Likes or Views descending
    # Note: Assumes these properties exist
    sorts = [
        {"property": "Likes", "direction": "descending"},
        {"property": "Views", "direction": "descending"}
    ]
    
    pages = query_database(db_id, sorts=sorts)
    
    top_assets = []
    for page in pages[:limit]:
        props = page.get('properties', {})
        top_assets.append({
            'name': extract_text(props.get('Asset Name') or props.get('Name') or {}),
            'channel': extract_text(props.get('Channel') or {}),
            'hook': extract_text(props.get('Hook / Angle') or {}),
            'views': props.get('Views', {}).get('number', 0),
            'likes': props.get('Likes', {}).get('number', 0),
            'engagement': props.get('Engagement Rate', {}).get('formula', {}).get('number', 0)
        })
    return top_assets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--brand', required=True)
    parser.add_argument('--top', type=int, default=5)
    args = parser.parse_args()
    
    try:
        assets = get_top_assets(args.brand, args.top)
        print(json.dumps(assets, indent=2, ensure_ascii=False))
    except Exception as e:
        from notion_client import classify_error
        print(json.dumps({'error': str(e), 'kind': classify_error(e)}))
        sys.exit(1)
