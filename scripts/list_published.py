"""
List recent published or ready assets that need analytics syncing.

Usage:
    python scripts/list_published.py --brand brand_name [--limit 10]
"""
import sys
import json
import os
import argparse
sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    fetch_assets_for_analytics, classify_error
)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--brand', required=True)
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    
    try:
        assets = fetch_assets_for_analytics(args.brand, args.limit)
        print(json.dumps(assets, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e), 'kind': classify_error(e)}))
        sys.exit(1)
