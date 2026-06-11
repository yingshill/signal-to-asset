# Brand OS — Creative Content Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-agent-blueviolet?logo=anthropic)](https://claude.ai/code)
[![Notion API](https://img.shields.io/badge/Notion-API%20v1-black?logo=notion)](https://developers.notion.com/)
[![Tests](https://img.shields.io/badge/tests-118%20passing-brightgreen)]()

Good ideas don't become content by themselves. There's a gap between capturing an insight and publishing it — and that gap is filled with repetitive work: drafting angles, reformatting per platform, creating tasks, linking everything in your workspace.

**Brand OS** closes that gap with an agentic workflow. It reads a source entry from your Notion knowledge base — an article, a course note, a GitHub repo, a podcast insight — extracts the core signal, and runs an end-to-end content pipeline: marketing plan → brand-specific draft assets → linked publish tasks, all written and saved automatically.

The result lands directly in your Notion workspace: a Marketing Project tied to the source, draft assets for the brand's default channels, and a ready-to-action to-do checklist. You review, refine, and publish. The pipeline handles everything else.

> **Owner:** Yingshi Liu · **Runtime:** Claude Code · **Multi-Brand OS**

---

## How it works

```mermaid
graph TD
    A["Source Entry (Notion)"] --> URL
    URL["Paste URL into Claude Code"] --> MM["Creative Content Manager Agent"]
    MM --> DNA["Brand DNA & Style Check"]
    DNA --> VG["AI Visual Generation (DALL-E 3)"]
    VG --> P["Notion Marketing Projects"]
    P --> AL["Marketing Asset Library"]
    AL --> AN["Analytics Feedback Loop"]
```

**Trigger:** paste any source entry URL into Claude Code.

---

## 🏗️ Multi-Brand Infrastructure

The system now supports managing multiple businesses:
- **`brands/`**: Independent DNA and Notion routing per business. Visual identity is owned by DesignLore.
- **Auto-Detection**: Automatic brand identification based on Notion source URL.
- **Analytics Sync**: Push real engagement data back into Notion.

See the [**Operations Guide**](OPERATIONS_GUIDE.md) for how to run the growth engine as a one-person founder.

---

## Agent modes

| Mode | Trigger | What it does |
|---|---|---|
| **Project Mode** | Paste a Notion page URL | Fetches entry, creates Marketing Project, approval gate, drafts brand-default assets + to-dos |
| **Asset Creation** | "draft assets for [topic]" | Drafts posts/carousels for specified channels |
| **To-Do Generation** | "generate to-dos for [asset]" | Creates Review → Design → Publish checklist |

### Knowledge Brand default assets — 4, no approval needed

Brand-specific `DNA.md` files can override this default set. For example, Youmi and KitchenOS use Instagram/XHS-led defaults instead of the LinkedIn-centric set below.

| # | Asset | Channel | Notes |
|---|---|---|---|
| 1 | LinkedIn (PM) | LinkedIn | Hook for product managers / operators / AI builders · under 1,300 chars |
| 2 | LinkedIn (DE) | LinkedIn | Hook for data / ML engineers · same insight, different angle |
| 3 | Xiaohongshu (XHS) | XHS | Caption + design brief + slide deck |
| 4 | Notion Publishing Website | General | Cleaned republish of source entry |

Extra channels (X, Substack, YouTube, etc.) require explicit user approval per run.

---

## Getting started

### Prerequisites

- Python 3.12+
- [Claude Code](https://claude.ai/code)
- A Notion integration with read/write access to your databases

### 1. Clone and install

```bash
git clone https://github.com/yingshill/brand_os.git
cd brand_os
pip3 install -r requirements.txt
```

### 2. Create a Notion integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → **New integration**
2. Name it `brand_os`, set capabilities to Read + Write
3. Copy the **Internal Integration Secret** → paste as `NOTION_TOKEN` in `.env`
4. Open each database in Notion → `...` → **Connections** → add `brand_os`

### 3. Fill in `.env`

```bash
NOTION_TOKEN=secret_...

# Source databases (read)
NOTION_DB_AI_DAILY_HITS=
NOTION_DB_GITHUB_TRENDING=
NOTION_DB_PODCAST_DIGEST=
NOTION_DB_COURSE_DIGEST=

# Output databases (write)
NOTION_DB_MARKETING_PROJECTS=
NOTION_DB_MARKETING_ASSETS=
NOTION_DB_MARKETING_TODOS=
```

> Get database IDs from the Notion page URL — the 32-char hex string before `?v=`.

### 4. Verify the connection

```bash
python3 scripts/test_run.py
```

Expect 13/13 tests passing. This checks token validity, all DB connections, and create/archive round-trips for project, asset, and to-do rows.

### 5. Open in Claude Code

```bash
claude .
```

Claude Code reads `CLAUDE.md` and activates as the Creative Content Manager. Paste any source entry URL to trigger Project Mode.

---

## Repo structure

```
brand_os/
├── CLAUDE.md                       ← agent instructions (loaded automatically by Claude Code)
├── ROADMAP.md                      ← milestones, backlog, artifact tracker
├── DECISIONS.md                    ← architecture and design decision log
├── requirements.txt
├── .env                            ← credentials (gitignored)
│
├── scripts/
│   ├── notion_client.py            ← Notion API base client (with 10-min file cache)
│   ├── fetch_entry.py              ← fetch and parse a source entry by URL
│   ├── create_project.py           ← find-or-create a Marketing Project row
│   ├── create_asset.py             ← create asset row + page body blocks
│   ├── create_todo.py              ← create task(s) in Marketing To-Do
│   ├── update_entry_status.py      ← update source entry status field
│   ├── test_run.py                 ← live integration test suite (13 checks)
│   └── eval_run.py                 ← human eval script (run after each Project Mode)
│
├── tests/
│   ├── test_notion_client.py       ← cache, extract_page_id, property helpers
│   ├── test_fetch_entry.py         ← field extraction, source DB identification
│   ├── test_create_project.py      ← fuzzy title matching, find-or-create logic
│   ├── test_create_asset.py        ← property building, content truncation, blocks
│   └── test_create_todo.py         ← single and batch todo creation, optional fields
│
├── artifacts/
│   ├── architecture-diagram/
│   │   ├── notion-light/           ← index.html + diagram.svg
│   │   └── dark-tech/              ← index.html + diagram.svg
│   ├── code-walkthrough-carousel/
│   │   └── notion-light/           ← index.html + diagram.svg
│   └── case-study/
│       └── notion-light/           ← index.html (carousel embedded)
│
├── docs/                           ← supplementary documentation
└── agent/                          ← legacy agent spec files
```

---

## Running tests

**Unit tests** (mocked, no Notion connection needed):

```bash
python3 -m pytest tests/ -v
# 62 tests, ~0.2s
```

**Integration tests** (live Notion API — requires `.env` filled):

```bash
python3 scripts/test_run.py
# 13 checks: token, all 7 DBs, create + archive for project/asset/todo
```

**Human eval** (run after each Project Mode session):

```bash
python3 scripts/eval_run.py
# Scores hook quality, content quality, channel fit (1–5) per asset
# Saves to .eval/<date>-<project-slug>.json
```

---

## Notion database access

| Database | Access | Purpose |
|---|---|---|
| AI Daily Hits | Read | Source entries |
| GitHub Daily Trending | Read | Source entries |
| Podcast & Video Digest | Read | Source entries |
| Course Digest | Read + Write | Source entries + status update |
| Marketing Projects | Write | Create / link project rows |
| Marketing Asset Library | Write | Create asset rows with page body |
| Marketing To-Do | Write | Create linked task rows |

All read operations are cached locally in `.cache/notion/` with a 10-minute TTL. Write operations bust the relevant cache entries automatically.

---

## Key design decisions

See [`DECISIONS.md`](DECISIONS.md) for the full log. Notable choices:

- **Trigger = URL paste**, not auto-trigger on Notion tag — keeps the agent human-initiated
- **Human approval gate** before any assets are saved — agent drafts, you decide
- **File-based cache** (not in-memory) — survives across separate Python processes
- **LinkedIn dual-audience rule** — when LinkedIn is in the brand default set, create PM + DE variants
- **Agent never publishes** — it creates Draft rows and Review tasks only

---

## License

MIT — see [`LICENSE`](LICENSE).
