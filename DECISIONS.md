# Decisions — Brand OS

Architecture, stack, and design decisions logged as they were made.

---

## Agent runtime — Claude Code over custom Python orchestration
**Date:** 2026-05
**Context:** Needed a runtime that could read instructions, call tools, and interact with a human in a loop without building a custom orchestration layer.
**Options considered:** Custom Python agent loop · LangChain / LangGraph · Claude Code with CLAUDE.md
**Decision:** Claude Code with CLAUDE.md as the instruction file.
**Tradeoffs:** No custom code to maintain; agent behavior is fully described in plain English. Tradeoff is dependency on Claude Code CLI — not portable to a server or cron without the scheduled agent setup.

---

## Trigger mechanism — paste Notion URL into Claude Code chat
**Date:** 2026-05
**Context:** Needed a way for the agent to know which source entry to process.
**Options considered:** (A) Paste raw text from Notion · (B) Paste Notion page URL — agent fetches via API · (C) Tag-based trigger — agent polls for 📣 Project tag
**Decision:** Option B — paste the Notion page URL. Agent calls `fetch_entry.py` to retrieve structured data via the API.
**Tradeoffs:** Lowest friction (one paste), no polling loop needed, works with any source DB. Requires a valid Notion token. User must be in Claude Code to trigger.

---

## Approval gate — Claude Code chat, not Notion modals
**Date:** 2026-05
**Context:** The agent needs human approval before creating assets and tasks. Needed to decide where that interaction happens.
**Options considered:** Notion modal / comment · Separate approval UI · Claude Code chat (inline)
**Decision:** Approval happens entirely in Claude Code chat. Agent asks 4 questions (scope, hook, timeline, task list) and waits for a reply before proceeding.
**Tradeoffs:** Simple, no extra tooling. Means the full workflow lives in Claude Code — not accessible to non-technical collaborators.

---

## Notion API integration — thin Python wrappers, not an SDK
**Date:** 2026-05
**Context:** Needed to read/write Notion from the agent. Could use an existing SDK or write direct REST calls.
**Options considered:** `notion-client` Python SDK · Raw `requests` with a shared client module
**Decision:** Raw `requests` in a shared `notion_client.py` module. Each operation (query, create, update, append blocks) is a thin wrapper. Scripts are called by the agent via Bash.
**Tradeoffs:** Full control over request shape, no SDK version dependency. More boilerplate than an SDK. Scripts are stateless and independently testable.

---

## Agent name — Creative Content Manager (not Marketing Manager)
**Date:** 2026-05
**Context:** Original name was "Marketing Manager Agent." Felt too generic and didn't reflect that the agent's primary job is content creation, not campaign management.
**Options considered:** Marketing Manager · Content Manager · Creative Content Manager
**Decision:** Creative Content Manager.
**Tradeoffs:** More specific, better reflects the drafting-first workflow. Renamed globally across CLAUDE.md, architecture diagram, and all documentation.

---

## Default asset set — 4 assets per project, always
**Date:** 2026-05
**Context:** Needed to define what the agent produces by default without asking the user every time.
**Options considered:** Ask user each time · Fixed defaults + optional extras
**Decision:** 4 default assets always created without approval: LinkedIn (PM angle), LinkedIn (DE angle), XHS, Notion Website. Additional channels (X, Substack, YouTube) require explicit user approval.
**Tradeoffs:** Consistent output, no decision fatigue per project. LinkedIn always produces 2 assets (PM + DE) — this is a hard rule, no exceptions.

---

## Output hierarchy — agent → Marketing Projects → Asset Library + To-Do
**Date:** 2026-05
**Context:** Three output Notion databases: Marketing Projects, Asset Library, Marketing To-Do. Needed to define the data relationship and creation order.
**Options considered:** Flat — create all three in parallel · Hierarchical — project first, assets linked to project, tasks linked to assets
**Decision:** Hierarchical. Agent creates/finds a Marketing Project first, then creates assets linked to that project, then creates to-do tasks linked to each asset.
**Tradeoffs:** Clean relational structure in Notion. Means project creation is a blocking step — if it fails, nothing else runs.

---

## Artifact tooling — SVG + HTML portal, no Figma or Excalidraw
**Date:** 2026-05
**Context:** Needed a way to produce portfolio artifacts (diagrams, cards) without external design tools.
**Options considered:** Figma · Excalidraw · Mermaid (already in README) · Hand-coded SVG + HTML
**Decision:** Hand-coded SVG inlined in a self-contained HTML portal. Claude generates the SVG directly.
**Tradeoffs:** Fully portable, no tool dependency, versionable in git, themeable by swapping color values. Tradeoff is SVG authoring is verbose and hard to edit manually.

---

## Artifact theme system — 4 named themes + DesignLore custom
**Date:** 2026-05
**Context:** Artifacts need to match different placement contexts (light portfolio site, dark GitHub README, etc.).
**Options considered:** Single theme · Per-artifact ad hoc colors · Named theme system
**Decision:** 4 named themes (Notion Light, Notion Dark, Notion Parchment, Dark Tech) stored in `~/.claude/CLAUDE.md` + DesignLore custom themes from captured sites. Default is Notion Light.
**Tradeoffs:** Consistent visual language across all projects. Themes are defined once globally and reused. DesignLore integration allows capturing any site's palette for use in artifacts.

---

## Artifact versioning — per-theme subfolders, not flat files
**Date:** 2026-05
**Context:** Same artifact built in multiple themes needed a storage structure that didn't overwrite previous versions.
**Options considered:** Flat files with theme suffix (`diagram-dark-tech.svg`) · Subfolders per theme (`architecture-diagram/dark-tech/`)
**Decision:** Subfolders: `artifacts/<artifact-slug>/<theme-slug>/index.html` + `diagram.svg`.
**Tradeoffs:** Clean separation, easy to add new themes without touching existing ones. `_preview.html` and `_swatches.html` are scratch files in the artifacts root, never committed.

---

## Artifact preview workflow — temp file before committing
**Date:** 2026-05
**Context:** User needed to visually review an artifact before saving it to a versioned folder. Writing directly to the versioned path made iteration awkward.
**Options considered:** Show SVG as code in chat only · Write directly to versioned path · Write to a temp `_preview.html`, open in browser, commit on "save"
**Decision:** Write to `artifacts/_preview.html` on each iteration, open in browser immediately. Only write to the real versioned folder when the user explicitly says "save."
**Tradeoffs:** Fast visual feedback loop, no stale versioned files from abandoned iterations. Requires discipline not to reference `_preview.html` as a real artifact.

---

## Notion API caching — file-based, 10-minute TTL
**Date:** 2026-05-09
**Context:** Each script is a separate Python process called by Claude Code via Bash. In-memory caching doesn't survive across calls. Every invocation was hitting the Notion API fresh, including repeated `query_database` calls on large DBs.
**Options considered:** No cache · In-memory (per-process) · File-based with TTL
**Decision:** File-based cache in `.cache/notion/`. Read operations (`get_page`, `get_page_blocks`, `query_database`) cache with a 10-minute TTL. Write operations (`create_page`, `update_page`, `append_blocks`) never cache and bust related cache entries on write.
**Tradeoffs:** Survives across script calls within a session. `create_page` busts all cached queries for that DB so subsequent reads see the new row. TTL of 10 min is safe for a human-in-the-loop workflow — source entries don't change mid-session.

---

## Weekly planning mode — removed
**Date:** 2026-05-09
**Context:** `weekly_planning.py` was built to query the Asset Library for Status=Ready assets and create publish tasks. User confirmed this mode is not needed for the current workflow.
**Options considered:** Keep as optional mode · Remove entirely
**Decision:** Remove from CLAUDE.md modes and ROADMAP. Script file kept on disk but not referenced by the agent.
**Tradeoffs:** Simplifies the agent — fewer modes to maintain. Script can be reintroduced later if needed.

---

## Multi-brand routing — `brand` field on every stdin payload, no per-process flag
**Date:** 2026-05-19
**Context:** Each Notion-writing script is a separate Python process invoked by the agent. `notion_client.DB_IDS` is a module-level dict populated from `brands/default/config.json` at import time. Without an explicit signal per call, every script silently writes to the default brand — which is what was happening in `create_todo.py` and `log_run.py` before this fix.
**Options considered:** (A) Environment variable `BRAND_OS_BRAND` set by the agent before each Bash call · (B) CLI flag `--brand` on every script · (C) `"brand"` field in the stdin JSON payload, calling `set_brand()` early in the handler
**Decision:** Option C for all stdin-driven scripts; `--brand` argparse for the argv-driven ones (`weekly_planning`, `generate_post_mortem`, `list_published`, `eval_run`, `test_run`). Every script that performs a Notion write is required to call `set_brand()` before reading `DB_IDS`.
**Tradeoffs:** Brand selection is co-located with the payload — easy to grep for, easy to audit in `logs/runs.jsonl`. Cost is one extra line per script and the contract that the agent must always emit `"brand"`. Enforced by `CLAUDE.md` and by `scripts/list_brands.py` which fails CI if a brand has missing IDs.

---

## Foundational marketing DBs are global; brand isolation via `Project` relation
**Date:** 2026-05-19
**Context:** Multi-brand v1 had each brand's `config.json` repeat the IDs for `marketing_projects`, `marketing_assets`, `marketing_todos`. Same three DBs, copy-pasted across every brand. The user pointed out: those are foundational, every brand needs them, no point repeating. Then clarified the Notion structure: there is one **Projects DB** with one row per brand, and every Marketing Project row carries a `Project` relation pointing back to its brand's row.
**Options considered:** (A) Add a `Brand` Select property on every marketing row (new property, all brands tagged in-row) · (B) Use the existing Projects-DB relation already in Notion · (C) No isolation at all (one combined timeline, no tag).
**Decision:** Option B. The 3 foundational DBs come from `.env` only (`NOTION_DB_MARKETING_*`), shared by all brands. Each brand's config.json carries `notion.page_ids.brand_project` — the Projects-DB row ID for that brand. `create_project.py` sets the `Project` relation on every new Marketing Project row, scoping it to the brand. Assets and Todos inherit brand context up the existing project→asset→todo relation chain. `STYLE.json` is also dropped (visual identity owned by DesignLore).
**Tradeoffs:** Per-brand config shrinks dramatically (just `name` + `brand_project` + optional source DBs). Brand filtering in Notion uses the relation that's already there — no new property. Cost: `find_existing_project` must filter by `Project` relation to avoid cross-brand title collisions; `find_existing_todo` currently filters by task name only and could theoretically collide across brands, though in practice task names embed the project title. Flagged as follow-up.

---

## New brand — KitchenOS positioning & channel defaults
**Date:** 2026-05-19
**Context:** Stood up a third brand, `kitchenos`. Initial inputs were mixed — described as a "smart-home cooking app" but with an audience of "restaurant operators/chefs." Needed to reconcile the two before writing DNA.
**Options considered:** Prosumer / pro-grade-at-home · Crossover pros+home · Chef-led marketed to home · Truly chef/operator B2B. Voice: confident/technique-driven · warm/approachable · sleek product-forward · editorial/curator.
**Decision:** Positioning = **prosumer "pro-grade-at-home"** — a home cooking app that brings restaurant-level technique and systems to ambitious home cooks (the buyer); chefs are the aspiration/credibility anchor, not the core market. Voice = **warm + approachable** with quiet credibility. Default channels override the global LinkedIn-centric defaults: **Instagram (carousel + reel), Xiaohongshu, Notion Website**; LinkedIn is approval-gated (founder/B2B narrative only).
**Tradeoffs:** A focused buyer (ambitious home cook) keeps content sharp and avoids the trap of B2B restaurant-ops messaging the product isn't built for. Departing from the LinkedIn default means the "LinkedIn = 2 assets" hard rule does not apply to this brand's default set; this is a deliberate per-brand override recorded in `brands/kitchenos/DNA.md`. Brand is not yet "healthy" — awaiting the Notion Projects-DB row + page ID.

---

## Project tracking — ROADMAP.md + DECISIONS.md (not a single file)
**Date:** 2026-05
**Context:** Needed a way to track progress, backlog, artifacts, and design decisions. A single file mixes concerns.
**Options considered:** Single `ROADMAP.md` · `ROADMAP.md` + `DECISIONS.md` · Full ADR folder structure
**Decision:** Two files. `ROADMAP.md` for what/when (progress, backlog, artifacts). `DECISIONS.md` for why (architecture, stack, design choices). Full ADR folder structure was overkill for a solo project.
**Tradeoffs:** Clean separation of concerns, different read frequency. ROADMAP changes constantly; DECISIONS is append-only.


---

## Explicit brand selection is enforced at script boundaries
**Date:** 2026-06-11
**Context:** A Youmi insurance content idea exposed an operational risk: campaign ideas can originate inside any project repo, but Brand OS owns marketing plans/assets across multiple brands. If Brand OS accepts omitted-brand payloads or defaults CLI tools to `default`, a project can be created, logged, or routed under the wrong brand.
**Options considered:** Keep the prior instruction-only contract · Ask the user every time even when brand is inferable · Enforce explicit brand at script boundaries and fail fast when missing
**Decision:** Enforce explicit brand selection. Stdin-driven project/asset/todo/log/analytics/visual scripts now require a `brand` field. Brand-scoped CLI tools now require `--brand`; using the default brand remains possible only by passing `--brand default` intentionally.
**Tradeoffs:** Slightly more ceremony in commands and tests, but Brand OS can no longer silently route cross-brand work to `default`. The agent still identifies/infer-checks the brand in conversation before running scripts; the scripts are the final guardrail.
