# 📣 Project Mode

Triggered when the user pastes a Notion source entry URL into Claude Code and confirms the detected entry and brand.

## Step-by-step

1. **Note the entry's metadata** — `Title`, `Core Insight`, `Why It Matters`.
2. **Detect the brand** from the source database. If detection fails, ask the user which brand to use and load that brand's `DNA.md`.
3. **Check the entry's database for a `Project` relation column** pointing to the Projects DB.
4. **If the `Project` relation column exists:**
   - Search Projects for an existing row in the **📣 Marketing Projects** data source that matches the topic.
   - **Match found** → link the entry to that project row via the `Project` relation.
   - **No match** → create a new row in **📣 Marketing Projects** (not Engineering / Ops / Learning) with:
     - **Name** — the entry's `Title`
     - **Positioning Statement** — derived from `Core Insight` + `Why It Matters`
     - **Status** — `Planning`
     - **Priority** — `🟡 Medium`
     - **Tier** — `🔵 Tier 3` (default)
     Then link the source entry to the new project row via the `Project` relation.
5. **If the `Project` relation column does not yet exist** on that database, append a note to the **Agent Performance Insights** callout in the **AI Command Center** with the entry title and core insight, flagging it as a candidate project for manual review.
6. **Always set the source entry's `Status` to `In Progress`** after the user confirms the project.
7. **Fill the Marketing Project page body** using the **📋 Marketing Plan Template** when the template page is configured. Load the template page, follow its structure and rules, and replace all bracketed placeholders with real content derived from the source entry.
8. **Human approval gates (required).** Before creating any asset rows or task rows in the databases, pause and ask the user to approve:
   - (a) **asset scope** — which channels get an asset
   - (b) **hook / angle**
   - (c) **timeline** — target publish week + draft deadline
   - (d) **task list** — confirm which checklist items are needed

   Revise if the user does not approve.
9. **Default assets.** Use the brand's `DNA.md` default channel set. For Knowledge Brand, every project includes these 4 default assets:

   | # | Asset | Channel | Type |
   |---|---|---|---|
   | 1 | LinkedIn (PM) | LinkedIn | Post / Carousel |
   | 2 | LinkedIn (DE) | LinkedIn | Post / Carousel |
   | 3 | XHS | XHS | Post + Carousel |
   | 4 | Notion Publishing Website | General | Article |

   Additional channels beyond the brand defaults require user approval.

## Notion Publishing Website — generation rules

- **How to generate:** Load the source entry's page body (from whichever of the 4 source databases it sits in). Copy the content body, **removing personal reflection sections** (✏️ My Notes, Practice/Application, Questions Raised) and agent scaffolding — keep only the learning content itself.
- **Metadata header.** At the top of the page, add a source info block:
  - **Source** — database name (e.g., "📖 Course Digest", "🎙️ Podcast & Video Digest")
  - **Title** — source entry title
  - **URL** — original source URL
  - **Other metadata** — platform, instructor, difficulty, date — whatever is available and useful for the reader
- **Independent page.** The website page is created as an **independent standalone page** (not inline content in the asset row). Link it into the asset's page body using a `<page>` block or mention.
- **Asset row.** Create a row in Marketing Asset Library with `Channel = General`, `Type = Article`, and link the independent page in the page body.
- **No new longform content** unless explicitly asked — this is a cleaned republish of existing content.
- **Human review required** before any distribution assets move to `Ready`.
