"""
Create an asset row in the Marketing Asset Library.

Asset names follow the deterministic convention:
    "{project_title} — LinkedIn (PM)"
    "{project_title} — LinkedIn (DE)"
    "{project_title} — XHS"
    "{project_title} — Notion Website"
    "{project_title} — {Channel}"   ← extras

Usage:
    python scripts/create_asset.py <<'JSON'
    {
      "brand": "youmi",
      "asset_name": "MCP is the new API — LinkedIn (PM)",
      "type": "Post | Carousel | Thread | Article | Case Study | Video",
      "channel": "LinkedIn | XHS | X | General | Substack | YouTube",
      "hook": "one-liner hook",
      "content": "full draft text",
      "topic": ["Workflow", "AI Design"],
      "project_id": "optional project page ID",
      "carousel_brief": "optional design brief text",
      "slides": [{"title": "Slide 1 — Hook", "content": "..."}]
    }
    JSON

Output: JSON with asset_id, asset_url, asset_name, action (created | existing).
"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    query_database, create_page, extract_text, classify_error, DB_IDS,
    title_prop, rich_text_prop, select_prop, multi_select_prop, relation_prop, status_prop,
    heading_block, paragraph_block, divider_block, bookmark_block, image_block, text_to_blocks,
)

CARD_CANVAS_URL = 'https://www.cardcanvas.app/'


def find_existing_asset(asset_name: str, project_id: str = '') -> dict | None:
    db_id = DB_IDS['marketing_assets']
    if not db_id:
        return None

    title_filter = {
        'property': 'Asset Name',
        'title': {'equals': asset_name},
    }
    if project_id:
        filter_obj = {
            'and': [
                title_filter,
                {'property': 'Project', 'relation': {'contains': project_id}},
            ],
        }
    else:
        filter_obj = title_filter

    pages = query_database(db_id, filter_obj=filter_obj)
    return pages[0] if pages else None


def create_asset(data: dict) -> dict:
    db_id = DB_IDS['marketing_assets']
    if not db_id:
        raise ValueError("NOTION_DB_MARKETING_ASSETS is not set in config/env")

    asset_name = data['asset_name']

    existing = find_existing_asset(asset_name, data.get('project_id', ''))
    if existing:
        return {
            'action': 'existing',
            'asset_id': existing['id'],
            'asset_url': existing.get('url', ''),
            'asset_name': asset_name,
            'channel': extract_text(existing.get('properties', {}).get('Channel', {})),
            'type': extract_text(existing.get('properties', {}).get('Type', {})),
            'content_truncated': False,
        }

    properties = {
        'Asset Name': title_prop(asset_name),
        'Type': select_prop(data.get('type', 'Post')),
        'Channel': select_prop(data.get('channel', 'LinkedIn')),
        'Status': status_prop('Draft'),
    }

    if data.get('hook'):
        properties['Hook / Angle'] = rich_text_prop(data['hook'])

    content = data.get('content', '')
    content_truncated = False
    if content:
        # Notion rich_text property limit: 2000 chars; full text is still written to page body below
        if len(content) > 1900:
            properties['Content'] = rich_text_prop(content[:1900])
            content_truncated = True
        else:
            properties['Content'] = rich_text_prop(content)

    if data.get('topic'):
        topics = data['topic'] if isinstance(data['topic'], list) else [data['topic']]
        properties['Topic'] = multi_select_prop(topics)

    if data.get('project_id'):
        properties['Project'] = relation_prop([data['project_id']])

    # Build page body blocks
    children = []

    if data.get('image_url'):
        children.append(heading_block('AI Generated Visual', 2))
        children.append(image_block(data['image_url'], caption=data.get('hook')))
        children.append(divider_block())

    if content:
        children.append(heading_block('Content', 2))
        children.extend(text_to_blocks(content))
        children.append(divider_block())

    if data.get('carousel_brief'):
        children.append(heading_block('Carousel Design Brief', 2))
        children.extend(text_to_blocks(data['carousel_brief']))
        children.append(paragraph_block('Design tool:'))
        children.append(bookmark_block(CARD_CANVAS_URL))
        children.append(divider_block())

    if data.get('slides'):
        children.append(heading_block('Slide Deck', 2))
        for slide in data['slides']:
            children.append(heading_block(slide.get('title', ''), 3))
            children.extend(text_to_blocks(slide.get('content', '')))

    page = create_page(db_id, properties, children if children else None)

    return {
        'action': 'created',
        'asset_id': page['id'],
        'asset_url': page.get('url', ''),
        'asset_name': asset_name,
        'channel': data.get('channel', ''),
        'type': data.get('type', 'Post'),
        'content_truncated': content_truncated,
    }


if __name__ == '__main__':
    try:
        data = json.loads(sys.stdin.read())
        brand = data.get('brand')
        if not brand:
            raise ValueError('brand is required; pass the target brand explicitly')
        from notion_client import set_brand
        set_brand(brand)
        
        result = create_asset(data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        from notion_client import classify_error
        print(json.dumps({'error': str(e), 'kind': classify_error(e)}))
        sys.exit(1)
