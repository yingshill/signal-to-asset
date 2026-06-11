"""
Human eval script — score agent output after a Project Mode run.
Run after each session until the agent is production-ready.

Usage:
    python scripts/eval_run.py --brand brand_name
    python scripts/eval_run.py "https://notion.so/..." --brand brand_name

Scores saved to: .eval/<date>-<project-slug>.json
"""
import sys
import json
import os
import re
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from notion_client import (
    DB_IDS, query_database, extract_page_id, extract_text, set_brand
)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--brand', required=True)
parser.add_argument('url', nargs='?', default='')
args, _ = parser.parse_known_args()

# Set brand context early
set_brand(args.brand)

EVAL_DIR = Path(__file__).parent.parent / '.eval'
EVAL_DIR.mkdir(exist_ok=True)


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40]


def prompt_score(label, lo=1, hi=5):
    while True:
        raw = input(f"    {label} [{lo}-{hi}]: ").strip()
        if raw == '':
            return None
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"    Enter a number from {lo} to {hi}, or press Enter to skip.")


def prompt_text(label):
    raw = input(f"    {label}: ").strip()
    return raw or None


def find_recent_project():
    from notion_client import DB_IDS
    rows = query_database(DB_IDS['marketing_projects'])
    if not rows:
        return None
    # sort by created_time descending
    rows.sort(key=lambda r: r.get('created_time', ''), reverse=True)
    return rows[0]


def fetch_project_assets(project_id):
    from notion_client import DB_IDS
    rows = query_database(DB_IDS['marketing_assets'])
    return [r for r in rows if any(
        rel.get('id', '').replace('-', '') == project_id.replace('-', '')
        for rel in r.get('properties', {}).get('Project', {}).get('relation', [])
    )]


# ── Resolve project ───────────────────────────────────────────────────────────

print(f"\n── Eval: Creative Content Manager Agent (Brand: {args.brand}) ──\n")

project = None
if args.url and args.url.startswith('http'):
    try:
        pid = extract_page_id(args.url)
        from notion_client import DB_IDS
        rows = query_database(DB_IDS['marketing_projects'])
        for r in rows:
            if r['id'].replace('-', '') == pid.replace('-', ''):
                project = r
                break
        if not project:
            print(f"Project not found for URL: {args.url}")
            sys.exit(1)
    except Exception as e:
        print(f"Error resolving project URL: {e}")
        sys.exit(1)
else:
    project = find_recent_project()
    if not project:
        print(f"No projects found in Marketing Projects DB for brand '{args.brand}'.")
        sys.exit(1)

project_id = project['id']
project_title = extract_text(
    project['properties'].get('Name') or project['properties'].get('Title') or {}
)
print(f"Project: {project_title}")
print(f"URL:     {project.get('url', '')}\n")

# ── Fetch assets ──────────────────────────────────────────────────────────────

assets = fetch_project_assets(project_id)
if not assets:
    print("No assets found linked to this project.")
    sys.exit(1)

print(f"Found {len(assets)} asset(s) to evaluate.\n")

# ── Eval each asset ───────────────────────────────────────────────────────────

eval_results = []

for i, asset in enumerate(assets, 1):
    props = asset.get('properties', {})
    name    = extract_text(props.get('Asset Name') or props.get('Name') or {})
    channel = extract_text(props.get('Channel') or {})
    atype   = extract_text(props.get('Type') or {})
    hook    = extract_text(props.get('Hook / Angle') or {})
    content = extract_text(props.get('Content') or {})

    print(f"── Asset {i}/{len(assets)}: {name} ──")
    print(f"   Channel: {channel}  |  Type: {atype}")
    if hook:
        print(f"   Hook:    {hook[:120]}")
    if content:
        print(f"   Content preview:\n")
        for line in content[:600].split('\n'):
            print(f"     {line}")
        if len(content) > 600:
            print(f"     ... ({len(content) - 600} more chars)")
    print()

    print("   Score this asset (press Enter to skip any field):")
    scores = {
        'hook_quality':    prompt_score('Hook quality (does it grab attention?)'),
        'content_quality': prompt_score('Content quality (clarity, specifics, voice)'),
        'channel_fit':     prompt_score('Channel fit (right tone/length for platform)'),
        'overall':         prompt_score('Overall'),
        'notes':           prompt_text('Notes (optional)'),
    }
    scores = {k: v for k, v in scores.items() if v is not None}

    eval_results.append({
        'asset_id':   asset['id'],
        'asset_name': name,
        'channel':    channel,
        'type':       atype,
        'scores':     scores,
    })
    print()

# ── Run-level questions ───────────────────────────────────────────────────────

print("── Overall run eval ──")
run_scores = {
    'scope_accuracy':    prompt_score('Scope accuracy (did agent follow instructions?)'),
    'output_completeness': prompt_score('Output completeness (all assets + todos created?)'),
    'would_publish':     prompt_score('Would you publish any of these drafts as-is? [1=none, 5=all]'),
    'run_notes':         prompt_text('Run notes (what to improve?)'),
}
run_scores = {k: v for k, v in run_scores.items() if v is not None}

# ── Save ─────────────────────────────────────────────────────────────────────

date_str = datetime.now().strftime('%Y-%m-%d-%H%M')
filename = f"{date_str}-{args.brand}-{slugify(project_title)}.json"
output = {
    'date':          datetime.now().isoformat(),
    'brand':         args.brand,
    'project_id':    project_id,
    'project_title': project_title,
    'project_url':   project.get('url', ''),
    'assets':        eval_results,
    'run':           run_scores,
}
outpath = EVAL_DIR / filename
outpath.write_text(json.dumps(output, indent=2, ensure_ascii=False))

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n── Summary ──")
all_scores = []
for a in eval_results:
    for k, v in a['scores'].items():
        if k != 'notes' and isinstance(v, int):
            all_scores.append(v)

if all_scores:
    avg = sum(all_scores) / len(all_scores)
    print(f"  Average score across all assets: {avg:.1f} / 5")

print(f"  Eval saved to: .eval/{filename}\n")
