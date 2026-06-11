"""
Automated test suite — runs against live Notion APIs.
Cleans up all test rows it creates (archives them).

Usage:
    python scripts/test_run.py --brand brand_name

Optional — test fetch_entry against a real source page:
    python scripts/test_run.py --url "https://www.notion.so/..." --brand brand_name
"""
import sys
import json
import argparse
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    NOTION_TOKEN, DB_IDS, get_page, query_database, create_page, update_page,
    extract_page_id, title_prop, rich_text_prop, select_prop, status_prop, relation_prop,
    set_brand
)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--brand', required=True)
parser.add_argument('--url', default='')
args, _ = parser.parse_known_args()

# Set brand context early
set_brand(args.brand)

PASS = '✅'
FAIL = '❌'
SKIP = '⏭'
results = []


def report(name, passed, detail=''):
    status = PASS if passed else FAIL
    results.append(passed)
    suffix = f'  ({detail})' if detail else ''
    print(f"  {status} {name}{suffix}")


def archive(page_id):
    """Archive (soft-delete) a Notion page."""
    import requests
    from notion_client import HEADERS, BASE_URL
    requests.patch(f"{BASE_URL}/pages/{page_id}", headers=HEADERS, json={'archived': True})


# ── Test 1: Token ─────────────────────────────────────────────────────────────

print(f"\n── Test 1: API connectivity (Brand: {args.brand}) ──")
try:
    import requests
    from notion_client import HEADERS, BASE_URL
    r = requests.get(f"{BASE_URL}/users/me", headers=HEADERS)
    r.raise_for_status()
    name = r.json().get('name', 'unknown')
    report("Notion token valid", True, f"integration: {name}")
except Exception as e:
    report("Notion token valid", False, str(e))

# ── Test 2: DB reachability ───────────────────────────────────────────────────

print("\n── Test 2: Database reachability ──")
for db_name, db_id in DB_IDS.items():
    if not db_id or len(db_id) < 32:
        report(f"{db_name}", False, "missing or invalid ID in config/env")
        continue
    try:
        rows = query_database(db_id)
        report(f"{db_name}", True, f"{len(rows)} rows returned")
    except Exception as e:
        report(f"{db_name}", False, str(e)[:80])

# ── Test 3: fetch_entry (optional — requires --url) ───────────────────────────

print("\n── Test 3: fetch_entry ──")
if args.url:
    try:
        import subprocess, shlex
        cmd = [sys.executable, 'scripts/fetch_entry.py', args.url]
        if args.brand:
            cmd.append(args.brand)
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        data = json.loads(result.stdout)
        if 'error' in data:
            report("fetch_entry", False, data['error'])
        else:
            report("fetch_entry", True, f"title: {data.get('title', '')[:50]}")
    except Exception as e:
        report("fetch_entry", False, str(e))
else:
    print(f"  {SKIP} fetch_entry — pass --url to test (skipped)")

# ── Test 4: create_project (creates + archives) ───────────────────────────────

print("\n── Test 4: create_project ──")
test_project_id = None
try:
    db_id = DB_IDS['marketing_projects']
    page = create_page(db_id, {
        'Name': title_prop('[TEST] brand_os automated test'),
        'Status': select_prop('Planning'),
    })
    test_project_id = page['id']
    report("create_project — create", True, f"id: {test_project_id[:8]}...")
except Exception as e:
    report("create_project — create", False, str(e)[:80])

# ── Test 5: create_asset (creates + archives) ─────────────────────────────────

print("\n── Test 5: create_asset ──")
test_asset_id = None
try:
    db_id = DB_IDS['marketing_assets']
    props = {
        'Asset Name': title_prop('[TEST] brand_os automated test asset'),
        'Type': select_prop('Post'),
        'Channel': select_prop('LinkedIn'),
        'Status': status_prop('Draft'),
    }
    if test_project_id:
        props['Project'] = relation_prop([test_project_id])
    page = create_page(db_id, props)
    test_asset_id = page['id']
    report("create_asset — create", True, f"id: {test_asset_id[:8]}...")
except Exception as e:
    report("create_asset — create", False, str(e)[:80])

# ── Test 6: create_todo (creates + archives) ──────────────────────────────────

print("\n── Test 6: create_todo ──")
test_todo_id = None
try:
    db_id = DB_IDS['marketing_todos']
    props = {
        'Task': title_prop('[TEST] Review — brand_os automated test'),
        'Priority': select_prop('🔥 High'),
        'Status': status_prop('Not Started'),
    }
    if test_asset_id:
        props['Linked Asset'] = relation_prop([test_asset_id])
    page = create_page(db_id, props)
    test_todo_id = page['id']
    report("create_todo — create", True, f"id: {test_todo_id[:8]}...")
except Exception as e:
    report("create_todo — create", False, str(e)[:80])

# ── Test 7: generate_visual (optional — requires OPENAI_API_KEY) ──────────────

print("\n── Test 7: generate_visual ──")
openai_key = os.environ.get('OPENAI_API_KEY')
if openai_key:
    try:
        import subprocess
        cmd = [sys.executable, 'scripts/generate_visuals.py']
        input_data = json.dumps({
            "brand": args.brand,
            "prompt": "Test visual for automated suite",
            "aspect_ratio": "1:1"
        })
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        data = json.loads(result.stdout)
        if 'error' in data:
            report("generate_visual", False, data['error'])
        else:
            report("generate_visual", True, f"url: {data.get('image_url', '')[:50]}...")
    except Exception as e:
        report("generate_visual", False, str(e))
else:
    print(f"  {SKIP} generate_visual — set OPENAI_API_KEY in .env to test (skipped)")

# ── Cleanup ───────────────────────────────────────────────────────────────────

print("\n── Cleanup ──")
for label, pid in [("test project", test_project_id), ("test asset", test_asset_id), ("test todo", test_todo_id)]:
    if pid:
        try:
            archive(pid)
            report(f"archived {label}", True)
        except Exception as e:
            report(f"archived {label}", False, str(e)[:60])

# ── Summary ───────────────────────────────────────────────────────────────────

print()
passed = sum(1 for r in results if r)
total = len(results)
status = PASS if passed == total else FAIL
print(f"{status} {passed}/{total} tests passed\n")
sys.exit(0 if passed == total else 1)
