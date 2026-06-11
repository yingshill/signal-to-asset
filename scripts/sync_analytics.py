"""
Sync performance analytics for a published asset in Notion.

Usage:
    python scripts/sync_analytics.py <<'JSON'
    {
      "brand": "youmi",
      "asset_id": "...",
      "metrics": {
        "Views": 1500,
        "Likes": 120,
        "Comments": 15,
        "Shares": 5
      }
    }
    JSON

Output: JSON with updated metrics and asset_id.
"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    update_page, number_prop, classify_error, set_brand
)


def sync_analytics(data: dict) -> dict:
    brand = data.get('brand')
    if not brand:
        raise ValueError('brand is required; pass the target brand explicitly')
    set_brand(brand)
    
    asset_id = data.get('asset_id')
    if not asset_id:
        raise ValueError("asset_id is required")
        
    metrics = data.get('metrics', {})
    properties = {}
    
    # Map provided metrics to Notion properties
    # Note: Assumes these properties exist in the database schema
    for key, value in metrics.items():
        properties[key] = number_prop(float(value))
        
    if not properties:
        return {"message": "No metrics provided", "asset_id": asset_id}

    update_page(asset_id, properties)

    return {
        "status": "updated",
        "asset_id": asset_id,
        "metrics_synced": list(properties.keys()),
        "brand": brand
    }


if __name__ == '__main__':
    try:
        data = json.loads(sys.stdin.read())
        result = sync_analytics(data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        from notion_client import classify_error
        print(json.dumps({'error': str(e), 'kind': classify_error(e)}))
        sys.exit(1)
