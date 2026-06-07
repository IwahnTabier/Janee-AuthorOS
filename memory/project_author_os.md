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
- `author_os.py` — entry point, main menu (menu option 6 = Opportunity Hunter)
- `db.py` — schema, connection, shared helpers; DB path configurable via AUTHOR_OS_DB env var
- `agents.py` — literary agent pipeline tracker
- `opportunities.py` — anthology/magazine/contest/speaking opportunities (submission tracking)
- `calendar_mod.py` — content calendar across platforms
- `reports.py` — weekly logs + YTD summary; shows top Opportunity Hunter prospects
- `opportunity_hunter.py` — Phase 2: discovery/scoring for podcasts, agents, publishers, festivals, reviewers, bloggers
- `Dockerfile` — Docker support with /data volume for db persistence
- `tests/test_opportunity_hunter.py` — 24 unit tests (scoring, CRUD, reports, sample data)
- `author_os.db` — SQLite database (git-ignored or kept locally)

## Schema tables
- `books` — 3 seeded on init
- `agents` — statuses: Wishlist → Queried → Partial/Full Requested → Offer/Rejected/Passed
- `opportunities` — types: Anthology, Magazine, Contest, Speaking, etc.; statuses: Open/Submitted/Accepted/Rejected
- `calendar` — scheduled content by platform/type/status
- `weekly_log` — manual word count + auto-derived stats from other tables
- `prospects` — Opportunity Hunter: 6 types (podcast/agent/publisher/festival/reviewer/blogger); 5 scoring criteria × 4 = 0–100; 23 sample entries loaded via menu option 9

## Opportunity Hunter scoring
Score = (audience_relevance + genre_fit + accessibility + potential_reach + publishing_value) × 5. Each criterion 0–4. Max 100. Threshold: 75+ = high priority.
