"""Notion API base client. All scripts import from here."""
import os
import re
import json
import hashlib
import time
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

_MAX_RETRIES = 3
_BASE_DELAY = 1.0  # seconds


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """Wrap requests with exponential backoff on 429 and 5xx responses."""
    last_response = None
    for attempt in range(_MAX_RETRIES + 1):
        r = requests.request(method, url, **kwargs)
        if r.status_code != 429 and r.status_code < 500:
            r.raise_for_status()
            return r
        last_response = r
        if attempt < _MAX_RETRIES:
            delay = (
                float(r.headers.get('Retry-After', _BASE_DELAY * (2 ** attempt)))
                if r.status_code == 429
                else _BASE_DELAY * (2 ** attempt)
            )
            time.sleep(delay)
    last_response.raise_for_status()
    return last_response  # unreachable; satisfies type checker

load_dotenv(Path(__file__).parent.parent / '.env')

NOTION_TOKEN = os.environ.get('NOTION_TOKEN', '')
BASE_URL = 'https://api.notion.com/v1'
HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

_CACHE_DIR = Path(__file__).parent.parent / '.cache' / 'notion'
_CACHE_TTL = 600  # seconds — 10 minutes


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _cache_get(key: str) -> Optional[dict]:
    p = _cache_path(key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        if time.time() - data['ts'] > _CACHE_TTL:
            p.unlink(missing_ok=True)
            return None
        return data['payload']
    except Exception:
        return None


def _cache_set(key: str, payload) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(json.dumps({'ts': time.time(), 'payload': payload}))


def _cache_bust(key: str) -> None:
    _cache_path(key).unlink(missing_ok=True)

# ── Brand Management ──────────────────────────────────────────────────────────

def list_brands() -> list:
    """List all directories in brands/."""
    brands_dir = Path(__file__).parent.parent / 'brands'
    if not brands_dir.exists():
        return ['default']
    return [d.name for d in brands_dir.iterdir() if d.is_dir()]


# Foundational keys are global — shared across all brands, sourced from .env.
# Per-brand config.json can carry source DBs and brand-specific page IDs.
FOUNDATIONAL_DB_KEYS = ('marketing_projects', 'marketing_assets', 'marketing_todos')
FOUNDATIONAL_PAGE_KEYS = ('marketing_plan_template',)


def _foundational_db_ids() -> dict:
    return {
        'marketing_projects': os.environ.get('NOTION_DB_MARKETING_PROJECTS', ''),
        'marketing_assets':   os.environ.get('NOTION_DB_MARKETING_ASSETS', ''),
        'marketing_todos':    os.environ.get('NOTION_DB_MARKETING_TODOS', ''),
    }


def _foundational_page_ids() -> dict:
    return {
        'marketing_plan_template': os.environ.get('NOTION_PAGE_MARKETING_PLAN_TEMPLATE', ''),
    }


def load_brand_config(brand_name: str = 'default') -> dict:
    """
    Load DB/page IDs for a brand. Foundational marketing DBs always come from
    .env (shared across all brands). Per-brand config.json layers source DBs
    and brand-specific page IDs on top; any foundational keys present in the
    brand config are ignored.
    """
    db_ids = _foundational_db_ids()
    page_ids = _foundational_page_ids()

    brand_path = Path(__file__).parent.parent / 'brands' / brand_name / 'config.json'
    if brand_path.exists():
        with open(brand_path) as f:
            brand_notion = json.load(f).get('notion', {})
        for k, v in brand_notion.get('db_ids', {}).items():
            if k not in FOUNDATIONAL_DB_KEYS:
                db_ids[k] = v
        for k, v in brand_notion.get('page_ids', {}).items():
            if k not in FOUNDATIONAL_PAGE_KEYS:
                page_ids[k] = v
    else:
        # No brand config — pick up source DBs from env (legacy single-tenant mode)
        for k in ('ai_daily_hits', 'github_trending', 'podcast_digest', 'course_digest'):
            val = os.environ.get(f'NOTION_DB_{k.upper()}', '')
            if val:
                db_ids[k] = val
        ai_cc = os.environ.get('NOTION_PAGE_AI_COMMAND_CENTER', '')
        if ai_cc:
            page_ids['ai_command_center'] = ai_cc

    return {'db_ids': db_ids, 'page_ids': page_ids}


def find_brand_by_db(db_id: str) -> Optional[str]:
    """Search all brands for one that contains this database ID."""
    db_id_clean = db_id.replace('-', '')
    for brand in list_brands():
        config = load_brand_config(brand)
        for val in config.get('db_ids', {}).values():
            if val.replace('-', '') == db_id_clean:
                return brand
    return None

# Default global IDs (can be overridden by scripts)
_CURRENT_CONFIG = load_brand_config()
DB_IDS = _CURRENT_CONFIG['db_ids']
PAGE_IDS = _CURRENT_CONFIG['page_ids']

def set_brand(brand_name: str):
    """Override global DB_IDS and PAGE_IDS for the current process."""
    config = load_brand_config(brand_name)
    DB_IDS.clear()
    DB_IDS.update(config['db_ids'])
    PAGE_IDS.clear()
    PAGE_IDS.update(config['page_ids'])


def extract_page_id(url: str) -> str:
    """Extract and format a Notion page ID from any Notion URL."""
    clean = url.split('?')[0].split('#')[0]
    # Try dashed UUID format first (already formatted)
    match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', clean)
    if match:
        return match.group(1)
    # Find exactly 32 hex chars bounded by non-hex chars (handles Page-Title-<id> URLs)
    match = re.search(r'(?<![a-f0-9])([a-f0-9]{32})(?![a-f0-9])', clean)
    if match:
        raw = match.group(1)
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    raise ValueError(f"Could not extract page ID from URL: {url}")


def get_page(page_id: str) -> dict:
    key = f"page_{page_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    r = _request_with_retry('GET', f"{BASE_URL}/pages/{page_id}", headers=HEADERS)
    result = r.json()
    _cache_set(key, result)
    return result


def get_page_blocks(page_id: str) -> list:
    key = f"blocks_{page_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    r = _request_with_retry('GET', f"{BASE_URL}/blocks/{page_id}/children", headers=HEADERS)
    result = r.json().get('results', [])
    _cache_set(key, result)
    return result


def query_database(db_id: str, filter_obj: Optional[dict] = None, sorts: Optional[list] = None) -> list:
    body = {}
    if filter_obj:
        body['filter'] = filter_obj
    if sorts:
        body['sorts'] = sorts
    h = hashlib.md5(json.dumps(body, sort_keys=True).encode()).hexdigest()[:8]
    key = f"db_{db_id}_{h}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    results = []
    cursor = None
    while True:
        page_body = dict(body)
        if cursor:
            page_body['start_cursor'] = cursor
        r = _request_with_retry('POST', f"{BASE_URL}/databases/{db_id}/query", headers=HEADERS, json=page_body)
        data = r.json()
        results.extend(data.get('results', []))
        if data.get('has_more') and data.get('next_cursor'):
            cursor = data['next_cursor']
        else:
            break

    _cache_set(key, results)
    return results


def create_page(parent_db_id: str, properties: dict, children: Optional[list] = None) -> dict:
    body = {'parent': {'database_id': parent_db_id}, 'properties': properties}
    if children:
        body['children'] = children
    r = _request_with_retry('POST', f"{BASE_URL}/pages", headers=HEADERS, json=body)
    # bust all cached queries for this database so subsequent reads see the new page
    for p in _CACHE_DIR.glob(f"db_{parent_db_id}_*.json"):
        p.unlink(missing_ok=True)
    return r.json()


def update_page(page_id: str, properties: dict, parent_db_id: Optional[str] = None) -> dict:
    r = _request_with_retry('PATCH', f"{BASE_URL}/pages/{page_id}", headers=HEADERS, json={'properties': properties})
    _cache_bust(f"page_{page_id}")
    if parent_db_id:
        for p in _CACHE_DIR.glob(f"db_{parent_db_id}_*.json"):
            p.unlink(missing_ok=True)
    return r.json()


def append_blocks(page_id: str, children: list) -> dict:
    r = _request_with_retry('PATCH', f"{BASE_URL}/blocks/{page_id}/children", headers=HEADERS, json={'children': children})
    _cache_bust(f"blocks_{page_id}")
    return r.json()


# ── Property value helpers ────────────────────────────────────────────────────

def extract_text(prop: Optional[dict]) -> str:
    if not prop:
        return ''
    ptype = prop.get('type', '')
    if ptype == 'title':
        return ''.join(t.get('plain_text', '') for t in prop.get('title', []))
    if ptype == 'rich_text':
        return ''.join(t.get('plain_text', '') for t in prop.get('rich_text', []))
    if ptype == 'select':
        sel = prop.get('select')
        return sel.get('name', '') if sel else ''
    if ptype == 'multi_select':
        return ', '.join(o.get('name', '') for o in prop.get('multi_select', []))
    if ptype == 'url':
        return prop.get('url', '') or ''
    if ptype == 'date':
        d = prop.get('date')
        return d.get('start', '') if d else ''
    if ptype == 'checkbox':
        return str(prop.get('checkbox', False))
    return ''


def rich_text(content: str) -> list:
    return [{'type': 'text', 'text': {'content': content}}]


def title_prop(content: str) -> dict:
    return {'title': rich_text(content)}


def rich_text_prop(content: str) -> dict:
    return {'rich_text': rich_text(content)}


def select_prop(name: str) -> dict:
    return {'select': {'name': name}}


def multi_select_prop(names: list) -> dict:
    return {'multi_select': [{'name': n} for n in names]}


def relation_prop(page_ids: list) -> dict:
    return {'relation': [{'id': pid} for pid in page_ids]}


def status_prop(name: str) -> dict:
    return {'status': {'name': name}}


def number_prop(value: float) -> dict:
    return {'number': value}


# ── Analytics & Discovery ─────────────────────────────────────────────────────

def fetch_assets_for_analytics(brand_name: str = 'default', limit: int = 10) -> list:
    """Fetch recent published assets to sync analytics."""
    set_brand(brand_name)
    db_id = DB_IDS['marketing_assets']
    if not db_id:
        return []
    
    # Filter for Published or Ready status
    filter_obj = {
        "or": [
            {"property": "Status", "status": {"equals": "Published"}},
            {"property": "Status", "status": {"equals": "Ready"}}
        ]
    }
    
    sorts = [{"timestamp": "created_time", "direction": "descending"}]
    
    pages = query_database(db_id, filter_obj=filter_obj, sorts=sorts)
    
    assets = []
    for page in pages[:limit]:
        props = page.get('properties', {})
        assets.append({
            'id': page['id'],
            'name': extract_text(props.get('Asset Name') or props.get('Name') or {}),
            'channel': extract_text(props.get('Channel') or {}),
            'url': page.get('url', '')
        })
    return assets


# ── Block helpers ─────────────────────────────────────────────────────────────

def paragraph_block(text: str) -> dict:
    return {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': rich_text(text)}}


def heading_block(text: str, level: int = 2) -> dict:
    h = f'heading_{level}'
    return {'object': 'block', 'type': h, h: {'rich_text': rich_text(text)}}


def divider_block() -> dict:
    return {'object': 'block', 'type': 'divider', 'divider': {}}


def bookmark_block(url: str) -> dict:
    return {'object': 'block', 'type': 'bookmark', 'bookmark': {'url': url}}


def image_block(url: str, caption: Optional[str] = None) -> dict:
    """Create an image block from an external URL."""
    block = {
        'object': 'block',
        'type': 'image',
        'image': {
            'type': 'external',
            'external': {'url': url}
        }
    }
    if caption:
        block['image']['caption'] = rich_text(caption)
    return block


def text_to_blocks(text: str) -> list:
    """Split long text into paragraph blocks (Notion limit: 2000 chars per block)."""
    blocks = []
    for i in range(0, len(text), 1900):
        blocks.append(paragraph_block(text[i:i + 1900]))
    return blocks


# ── Error classification ──────────────────────────────────────────────────────

def classify_error(exc: Exception) -> str:
    """Return a stable kind string for structured error output."""
    if isinstance(exc, requests.HTTPError):
        status = getattr(getattr(exc, 'response', None), 'status_code', 0)
        if status == 400:
            return 'schema_error'
        if status == 401:
            return 'auth_error'
        if status == 404:
            return 'not_found'
        if status == 429:
            return 'rate_limit'
        if status >= 500:
            return 'server_error'
        return 'http_error'
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return 'network_error'
    # json.JSONDecodeError is a subclass of ValueError — check it first
    if isinstance(exc, json.JSONDecodeError):
        return 'parse_error'
    if isinstance(exc, ValueError):
        return 'config_error'
    return 'unknown_error'
