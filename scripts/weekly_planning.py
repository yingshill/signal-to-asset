"""
Weekly Planning Mode — surface top 3 ready assets and create publish tasks.

Usage:
    python scripts/weekly_planning.py --brand brand_name

Output: JSON summary of assets surfaced and tasks created.
"""
import sys
import json
import os
import argparse
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    query_database, create_page, extract_text, DB_IDS,
    title_prop, select_prop, relation_prop, set_brand
)


def get_ready_assets() -> list:
    from notion_client import DB_IDS
    db_id = DB_IDS['marketing_assets']
    if not db_id:
        raise ValueError("NOTION_DB_MARKETING_ASSETS is not set in config/env")

    pages = query_database(
        db_id,
        filter_obj={'property': 'Status', 'select': {'equals': 'Ready'}},
        sorts=[{'property': 'Ready Date', 'direction': 'ascending'}],
    )

    assets = []
    for page in pages:
        props = page.get('properties', {})
        assets.append({
            'id': page['id'],
            'url': page.get('url', ''),
            'name': extract_text(props.get('Asset Name') or props.get('Name') or {}),
            'channel': extract_text(props.get('Channel') or {}),
            'ready_date': extract_text(props.get('Ready Date') or {}),
            'type': extract_text(props.get('Type') or {}),
        })
    return assets


def publish_task_exists(asset_id: str) -> bool:
    from notion_client import DB_IDS
    db_id = DB_IDS['marketing_todos']
    if not db_id:
        return False
    pages = query_database(db_id, filter_obj={
        'property': 'Linked Asset',
        'relation': {'contains': asset_id},
    })
    for page in pages:
        task_name = extract_text(
            page['properties'].get('Task') or page['properties'].get('Name') or {}
        ).lower()
        if 'publish' in task_name:
            return True
    return False


def run(brand: str) -> dict:
    if not brand:
        raise ValueError('brand is required; pass --brand explicitly')
    set_brand(brand)
    
    assets = get_ready_assets()
    top3 = assets[:3]

    if not top3:
        return {'brand': brand, 'assets': [], 'tasks_created': 0, 'message': 'No Ready assets found.'}

    from notion_client import DB_IDS
    db_id = DB_IDS['marketing_todos']
    if not db_id:
        raise ValueError("NOTION_DB_MARKETING_TODOS is not set in config/env")

    created = []
    skipped = []

    for asset in top3:
        if publish_task_exists(asset['id']):
            skipped.append(asset['name'])
            continue

        properties = {
            'Task': title_prop(f"Publish: {asset['name']}"),
            'Priority': select_prop('🔥 High'),
            'Status': select_prop('Not Started'),
            'Linked Asset': relation_prop([asset['id']]),
        }
        if asset['channel']:
            properties['Channel'] = select_prop(asset['channel'])

        create_page(db_id, properties)
        created.append({
            'asset': asset['name'],
            'channel': asset['channel'],
            'ready_since': asset['ready_date'],
            'type': asset['type'],
        })

    today = datetime.now()
    week_end = today + timedelta(days=(6 - today.weekday()))
    week_label = f"{today.strftime('%b %d')}–{week_end.strftime('%b %d, %Y')}"

    return {
        'brand': brand,
        'week': week_label,
        'tasks_created': len(created),
        'tasks_skipped': skipped,
        'top_assets': created,
        'total_ready': len(assets),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--brand', required=True)
    args = parser.parse_args()
    
    try:
        result = run(args.brand)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)
