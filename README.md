# Author OS — Janee Butterfield

An Author Operating System for Janee Butterfield, horror and thriller author of *Caught in Cryptic*, *Falling Cryptic*, and *Nighty Night Dear*.

---

## Purpose

Centralize author operations, track opportunities, manage the agent pipeline, schedule content, and generate weekly activity reports — all in one local system.

---

## Modules

| Module | Purpose |
|--------|---------|
| **Opportunity Tracker** | Track anthology, magazine, contest, speaking, and interview submissions |
| **Literary Agent Database** | Manage query pipeline — wishlist through offer |
| **Content Calendar** | Plan and publish blog, social, newsletter, and podcast content |
| **Weekly Report** | Log activity and generate weekly summaries |
| **My Books** | Manage published works |
| **Opportunity Hunter** | Discover and score prospects: podcasts, agents, publishers, festivals, reviewers, bloggers |

---

## Opportunity Hunter

The Opportunity Hunter (Phase 2) is a discovery and scoring system for identifying high-value opportunities to grow Janee's author platform.

### Opportunity Types

- Podcasts — guest appearance opportunities
- Literary Agents — agents open to queries in horror/thriller
- Publishers — traditional and indie publishers
- Festivals & Conventions — in-person networking events
- Reviewers — publications that review horror/thriller books
- Bloggers — horror/thriller book bloggers and influencers

### Scoring Model

Each prospect is rated on five criteria (0–4 each). Total score = sum × 5, giving a 0–100 range.

| Criterion | 0 | 1 | 2 | 3 | 4 |
|-----------|---|---|---|---|---|
| **Audience Relevance** | None | Small segment | Mixed | Primarily H/T | Pure H/T |
| **Genre Fit** | None | Partial | Moderate | Good | Perfect |
| **Accessibility** | Closed | Very hard | Moderate | Open | Welcoming |
| **Potential Reach** | <100 | 100–1K | 1K–10K | 10K–100K | 100K+ |
| **Publishing Value** | None | Brand only | Networking | Industry visibility | Direct path to deal |

**Score tiers:**
- 75–100 — High priority, act immediately
- 60–74 — Strong, worth pursuing
- 40–59 — Moderate, monitor
- Below 40 — Low priority

### Prospect Status Flow

```
new → contacted → responded → accepted
                             → rejected
any → archived
```

### Weekly Report

From the Opportunity Hunter menu, option 7 generates a markdown report covering:
- Summary counts by type and status
- Top prospects scored 60+
- Prospects needing follow-up (contacted 14+ days ago)
- Upcoming submission deadlines
- New prospects added this week

Reports can be saved to the `reports/` directory.

---

## Setup

### Local

```bash
python3 author_os.py
```

On first run, the database and all tables are created automatically.

To load sample data into the Opportunity Hunter:

```
Opportunity Hunter → 9. Load sample data
```

### Docker

```bash
docker build -t author-os .
docker run -it -v author-os-data:/data author-os
```

The database is stored in the `/data` volume and persists across container restarts. Override the path:

```bash
docker run -it -v /your/path:/data -e AUTHOR_OS_DB=/data/author_os.db author-os
```

---

## Running Tests

```bash
python3 -m pytest tests/ -v
# or
python3 -m unittest discover tests/
```

---

## Database

Single SQLite file (`author_os.db`). Tables:

| Table | Description |
|-------|-------------|
| `books` | Published works |
| `agents` | Literary agent pipeline |
| `opportunities` | Submission opportunities |
| `calendar` | Content calendar |
| `weekly_log` | Weekly activity log |
| `prospects` | Opportunity Hunter discovery database |

Configurable via `AUTHOR_OS_DB` environment variable.

---

## Security Notes

- No credentials stored in the database or source code
- No automatic posting or outreach
- All actions require explicit user input
- No network requests — fully local

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full phased plan.

- **Phase 1** — Foundation (complete): Author OS, opportunity tracking, agent pipeline, content calendar, reporting
- **Phase 2** — Opportunity Hunter (complete): Discovery database, scoring model, weekly reports, sample data
- **Phase 3** — Author Platform Growth: Social media, newsletter, website content
- **Phase 4** — Publisher Readiness: Agent database, query assets, media kit
- **Phase 5** — Automation: Automated reporting, content prep, opportunity discovery
