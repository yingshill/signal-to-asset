# 🧭 Quick Decision Tree

Use before writing anything.

```mermaid
flowchart TD
    Q1{"Did user paste a<br/>Notion source URL?"}
    Q1 -->|No| N1["Only draft assets if explicitly requested.<br/>Otherwise clarify mode."]
    Q1 -->|Yes| Q2

    Q2{"Has user approved<br/>scope + angle +<br/>timeline + checklist?"}
    Q2 -->|No| N2["Ask for approval.<br/>Do NOT create asset/to-do rows yet."]
    Q2 -->|Yes| Q3

    Q3{"Do brand defaults<br/>include LinkedIn?"}
    Q3 -->|Yes| L["Create 2 LinkedIn assets:<br/>LinkedIn (PM) + LinkedIn (DE)"]
    Q3 -->|No| C["Create assets per brand defaults<br/>and approved scope"]

    L --> D["Create brand-default assets<br/>(Knowledge Brand: LinkedIn PM,<br/>LinkedIn DE, XHS,<br/>Notion Publishing Website)"]
    C --> D
```

## Decision rules in plain text

1. **Did the user paste a Notion source URL?**
   - **No** → Only draft assets if explicitly requested; otherwise clarify the mode.
   - **Yes** → Fetch the entry, detect brand, and ask the user to confirm.
2. **Has the user approved asset scope + angle + timeline + checklist?**
   - **No** → Ask for approval (do not create asset/to-do rows yet).
   - **Yes** → Create assets, then generate minimal to-dos.
3. **Do the brand defaults include LinkedIn?**
   - **Yes** → Create **two LinkedIn assets**: LinkedIn (PM) + LinkedIn (DE).
   - **No** → Create assets per brand defaults and approved scope.
4. **Knowledge Brand default assets:**
   - LinkedIn (PM)
   - LinkedIn (DE)
   - XHS
   - Notion Publishing Website
