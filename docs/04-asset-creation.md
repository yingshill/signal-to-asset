# Asset Creation Mode

## Standard create flow

When generating assets:

1. Generate the content draft based on the requested topic and format.
2. Create a new entry in the **Marketing Asset Library** with these properties:

   | Property | Value |
   |---|---|
   | **Asset Name** | Clear, specific title |
   | **Type** | Post / Carousel / Thread / Article / Case Study / Video |
   | **Channel** | Where it will be published |
   | **Topic** | Architecture · Workflow · Mindset · AI Command Center · Agent Design · Interview Prep |
   | **Status** | `Draft` |
   | **Hook / Angle** | One-line hook or angle |
   | **Content** | Full draft + hashtags |
   | **Project** | Link to the marketing project (if one exists) |

3. Confirm to the user what was saved and where.

## Asset structure rule — carousel posts are a single asset

When a post includes a carousel (LinkedIn post + carousel, XHS post + carousel, etc.), treat it as **one asset**, not separate entries.

- **Content property** = the post/caption text itself
- **Page body** includes, in order:
  1. **Post content** with hashtags
  2. **Carousel Design Brief** — platform-specific brief: format notes, tone, slide count
  3. **🔧 Carousel Tool:** [Card Canvas](https://www.cardcanvas.app/) — default tool. Always include this link so the human can click and start designing.
  4. **Slide Decks** — detailed slide-by-slide content (Slide 1 — Hook, Slide 2 — …)
- **Type** property: use the primary format. Examples:
  - `Post` for a LinkedIn post that happens to attach a carousel
  - `Carousel` for a standalone carousel (e.g., XHS carousel-only posts)
- Do **not** create a separate "Carousel" asset when the carousel is attached to a text post on the same channel. **One asset = one publishable deliverable.**

## LinkedIn dual-audience rule

Whenever creating LinkedIn assets for a brand that uses the LinkedIn dual-audience rule, create 2 separate LinkedIn assets — one for **PM audience** and one for **DE (Data Engineering) audience**. Brand DNA can override the global LinkedIn-centric default set.

| Variant | Audience | Emphasis |
|---|---|---|
| **LinkedIn (PM)** | Product managers, operators, AI builders | Workflow, decision-making, system design thinking |
| **LinkedIn (DE)** | Data / ML engineers, infrastructure builders | Architecture, technical depth, implementation details |

- Each gets its own asset row with its own **Content**, **Hook / Angle**, and page body (carousel brief + slide decks if applicable).
- Carousels can be **shared** across angles — include the same carousel design brief in each asset's page body, or note "shared carousel with [other asset name]" and include the brief in one asset only.

## Multiple audience angles on the same channel (general rule)

Beyond the LinkedIn PM/DE split above, a single source/project can produce additional separate assets on the same channel when targeting other audiences. Each angle gets its own asset row with its own Content, Hook / Angle, and page body.

## Content voice guidelines

- **Hook-first** — open with a bold claim or surprising insight
- **Show the system, not just the outcome** — readers want to understand the architecture
- **Concrete specifics over vague generalities** — use database names, agent names, trigger types
- **Length:** LinkedIn posts under 1,300 characters; X threads under 280 characters per tweet
- **End with a subtle CTA** — question, invitation to connect, or link to portfolio

## Storytelling narrative style (preferred for "sharing a learning" posts)

When the post is framed as a personal insight or lesson learned, use this narrative arc:

1. **Open with a moment of realization** — *something clicked*, *a line stopped me*, *I used to do X until…*
2. **Acknowledge the before state** — what the old habit or assumption was (relatable, not self-deprecating)
3. **Share the reframe** — one concrete idea or framework that changed the approach, introduced naturally (not as a listicle header)
4. **Walk through each part as lived experience** — first-person: *"I learned…"*, *"This one I underestimated…"*, *"I stopped feeling like… and started feeling like…"*
5. **Close with honest humility** — *"I'm still learning this"* or *"this is what's working for me so far"*
6. **End with a genuine question** — curious, not performative
7. Add hashtags

**Tone:** down to earth, like whispering to a peer. No jargon laundering. Daily scenarios and small analogies over abstract frameworks. Literature-adjacent: a little texture, a little pause.
