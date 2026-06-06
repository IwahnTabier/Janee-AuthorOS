---
name: project-author-os
description: Janee Butterfield Author OS — Python/SQLite system built for horror/thriller author tracking agents, opportunities, content, and weekly reports
metadata:
  type: project
---

Author OS built for Janee Butterfield (horror/thriller author of Caught in Cryptic, Falling Cryptic, Nighty Night Dear).

**Why:** Single system to replace scattered tracking across folders/docs.

**How to apply:** When modifying, keep zero external dependencies (stdlib + sqlite3 only). Run with `python3 author_os.py` from the project root.

## Files
- `author_os.py` — entry point, main menu
- `db.py` — schema, connection, shared helpers (print_table, prompt, choose, header)
- `agents.py` — literary agent pipeline tracker
- `opportunities.py` — anthology/magazine/contest/speaking opportunities
- `calendar_mod.py` — content calendar across platforms
- `reports.py` — weekly logs + YTD summary
- `author_os.db` — SQLite database (git-ignored or kept locally)

## Schema tables
- `books` — 3 seeded on init
- `agents` — statuses: Wishlist → Queried → Partial/Full Requested → Offer/Rejected/Passed
- `opportunities` — types: Anthology, Magazine, Contest, Speaking, etc.; statuses: Open/Submitted/Accepted/Rejected
- `calendar` — scheduled content by platform/type/status
- `weekly_log` — manual word count + auto-derived stats from other tables
