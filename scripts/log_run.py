"""
Append a run summary to logs/runs.jsonl.

Called at the end of every Project Mode run. Each line is a self-contained
JSON record — use `jq` or any JSON-lines reader to query history.

Usage:
    python scripts/log_run.py <<'JSON'
    {
      "brand": "youmi",
      "project_id": "...",
      "project_title": "...",
      "assets": [
        {"asset_id": "...", "asset_name": "...", "action": "created | existing"}
      ],
      "todos": [
        {"task_id": "...", "task": "...", "action": "created | existing"}
      ]
    }
    JSON

Output: JSON with log_file path and counts written.
"""
import sys
import json
import os
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from notion_client import classify_error

LOG_FILE = Path(__file__).parent.parent / 'logs' / 'runs.jsonl'


def log_run(data: dict) -> dict:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    brand = data.get('brand')
    if not brand:
        raise ValueError('brand is required; pass the target brand explicitly')

    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'brand': brand,
        'project_id': data.get('project_id', ''),
        'project_title': data.get('project_title', ''),
        'assets': data.get('assets', []),
        'todos': data.get('todos', []),
    }

    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    assets_created = sum(1 for a in entry['assets'] if a.get('action') == 'created')
    todos_created = sum(1 for t in entry['todos'] if t.get('action') == 'created')

    return {
        'log_file': str(LOG_FILE),
        'brand': entry['brand'],
        'assets_created': assets_created,
        'assets_existing': len(entry['assets']) - assets_created,
        'todos_created': todos_created,
        'todos_existing': len(entry['todos']) - todos_created,
    }


if __name__ == '__main__':
    try:
        data = json.loads(sys.stdin.read())
        result = log_run(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e), 'kind': classify_error(e)}))
        sys.exit(1)
