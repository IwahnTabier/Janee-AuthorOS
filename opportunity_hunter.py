"""Opportunity Hunter — discover and score prospects for podcasts, agents, publishers, festivals, reviewers, and bloggers."""
from datetime import date, timedelta
import os
import db

TYPES = ['podcast', 'agent', 'publisher', 'festival', 'reviewer', 'blogger']

TYPE_DISPLAY = {
    'podcast':   'Podcasts',
    'agent':     'Literary Agents',
    'publisher': 'Publishers',
    'festival':  'Festivals & Conventions',
    'reviewer':  'Reviewers',
    'blogger':   'Bloggers',
}

STATUSES = ['new', 'contacted', 'responded', 'accepted', 'rejected', 'archived']

# Five scoring criteria mapped directly to CLAUDE.md reporting standards.
# Each is rated 0–4. Total score = sum × 5, giving a 0–100 range.
SCORE_CRITERIA = [
    ('audience_relevance', 'Audience Relevance', [
        '0 - No horror/thriller audience',
        '1 - Small or tangential horror/thriller segment',
        '2 - Mixed audience with meaningful horror/thriller segment',
        '3 - Primarily horror/thriller audience',
        '4 - Pure horror/thriller focus',
    ]),
    ('genre_fit', 'Genre Fit', [
        '0 - No genre alignment',
        '1 - Partial fit (adjacent genres only)',
        '2 - Moderate fit',
        '3 - Good genre alignment',
        '4 - Perfect fit — horror/thriller specialist',
    ]),
    ('accessibility', 'Accessibility', [
        '0 - Closed / not accepting / invitation only',
        '1 - Very difficult to access',
        '2 - Moderate effort required',
        '3 - Open, straightforward to apply',
        '4 - Actively welcoming indie and emerging authors',
    ]),
    ('potential_reach', 'Potential Reach', [
        '0 - Fewer than 100 people',
        '1 - 100 – 1,000 people',
        '2 - 1,000 – 10,000 people',
        '3 - 10,000 – 100,000 people',
        '4 - 100,000+ people',
    ]),
    ('publishing_value', 'Publishing Value', [
        '0 - No publishing value',
        '1 - Minor brand or reader exposure',
        '2 - Networking or community building',
        '3 - Meaningful industry visibility',
        '4 - Direct path toward agent representation or publishing deal',
    ]),
]


def compute_score(audience_relevance, genre_fit, accessibility, potential_reach, publishing_value):
    return (audience_relevance + genre_fit + accessibility + potential_reach + publishing_value) * 5


def menu():
    while True:
        db.header("OPPORTUNITY HUNTER")
        print("  1. View by type")
        print("  2. Top prospects (score 75+)")
        print("  3. Needs follow-up (14+ days)")
        print("  4. Add prospect")
        print("  5. Update prospect")
        print("  6. Archive prospect")
        print("  7. Weekly opportunity report")
        print("  8. Stats")
        print("  9. Load sample data")
        print("  0. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            _view_by_type()
        elif choice == "2":
            _top_prospects()
        elif choice == "3":
            _needs_followup()
        elif choice == "4":
            _add()
        elif choice == "5":
            _update()
        elif choice == "6":
            _archive()
        elif choice == "7":
            generate_report()
        elif choice == "8":
            _stats()
        elif choice == "9":
            _seed()
        elif choice == "0":
            break


def _view_by_type():
    db.header("View Prospects by Type")
    for i, t in enumerate(TYPES, 1):
        print(f"  {i}. {TYPE_DISPLAY[t]}")
    print("  7. All types")
    print("  0. Back")
    choice = input("\n  Choice: ").strip()

    try:
        idx = int(choice)
    except ValueError:
        return

    if idx == 0:
        return
    elif idx == 7:
        selected_type = None
    elif 1 <= idx <= len(TYPES):
        selected_type = TYPES[idx - 1]
    else:
        return

    title = TYPE_DISPLAY.get(selected_type, "All Prospects") if selected_type else "All Prospects"
    status_filter = input("  Filter by status (blank = all active): ").strip().lower() or None
    if status_filter and status_filter not in STATUSES:
        status_filter = None

    with db.connect() as conn:
        query = "SELECT id, type, name, score, status, url, contact_name, discovered_date FROM prospects WHERE 1=1"
        params = []
        if selected_type:
            query += " AND type = ?"
            params.append(selected_type)
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        else:
            query += " AND status != 'archived'"
        query += " ORDER BY score DESC, name"
        rows = conn.execute(query, params).fetchall()

    db.header(title)
    db.print_table(
        ["ID", "Type", "Name", "Score", "Status", "URL", "Contact", "Discovered"],
        [(r['id'], r['type'], r['name'], r['score'], r['status'],
          (r['url'] or '')[:40], r['contact_name'] or '', r['discovered_date'])
         for r in rows],
    )
    input("\n  Press Enter to continue...")


def _top_prospects():
    db.header("Top Prospects (Score 75+)")
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT id, type, name, score, status, url
            FROM prospects
            WHERE score >= 75 AND status != 'archived'
            ORDER BY score DESC, type, name
        """).fetchall()

    if not rows:
        print("\n  No prospects with score 75+ yet.")
        input("  Press Enter to continue...")
        return

    db.print_table(
        ["ID", "Type", "Name", "Score", "Status", "URL"],
        [(r['id'], TYPE_DISPLAY[r['type']], r['name'], r['score'], r['status'],
          (r['url'] or '')[:50])
         for r in rows],
    )
    input("\n  Press Enter to continue...")


def _needs_followup():
    db.header("Needs Follow-Up (contacted 14+ days ago)")
    cutoff = (date.today() - timedelta(days=14)).isoformat()
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT id, type, name, score, updated_at, contact_name
            FROM prospects
            WHERE status = 'contacted' AND updated_at <= ?
            ORDER BY score DESC
        """, (cutoff,)).fetchall()

    if not rows:
        print("\n  No prospects need follow-up right now.")
        input("  Press Enter to continue...")
        return

    db.print_table(
        ["ID", "Type", "Name", "Score", "Last Updated", "Contact"],
        [(r['id'], TYPE_DISPLAY[r['type']], r['name'], r['score'],
          r['updated_at'][:10], r['contact_name'] or '')
         for r in rows],
    )
    input("\n  Press Enter to continue...")


def _add():
    db.header("Add Prospect")

    opp_type = db.choose("Opportunity type", TYPES)
    name = db.prompt("Name")
    if not name:
        print("  Name required.")
        return

    url           = db.prompt("URL / website")
    contact_name  = db.prompt("Contact name")
    contact_email = db.prompt("Contact email")
    notes         = db.prompt("Notes")

    genre_focus        = None
    accepts_queries    = None
    submission_deadline = None

    if opp_type in ('podcast', 'festival', 'reviewer', 'blogger'):
        genre_focus = db.prompt("Genre focus (e.g. horror, thriller, both)")

    if opp_type in ('agent', 'publisher'):
        aq = db.prompt("Accepts queries? (y/n)")
        accepts_queries = 1 if aq.lower().startswith('y') else 0
        submission_deadline = db.prompt("Submission deadline (YYYY-MM-DD or note, optional)")

    if opp_type == 'festival':
        submission_deadline = db.prompt("Application deadline (YYYY-MM-DD, optional)")

    print("\n  --- SCORING (rate each criterion 0–4) ---")
    scores = {}
    for field, label, levels in SCORE_CRITERIA:
        print(f"\n  {label}:")
        for level in levels:
            print(f"    {level}")
        val = input("  Score (0–4): ").strip()
        try:
            scores[field] = max(0, min(4, int(val)))
        except ValueError:
            scores[field] = 0

    score = compute_score(**scores)
    print(f"\n  Computed score: {score}/100")

    with db.connect() as conn:
        conn.execute("""
            INSERT INTO prospects (
                type, name, url, contact_name, contact_email, status, notes,
                audience_relevance, genre_fit, accessibility, potential_reach, publishing_value,
                score, genre_focus, accepts_queries, submission_deadline
            ) VALUES (?, ?, ?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp_type, name,
            url or None, contact_name or None, contact_email or None,
            notes or None,
            scores['audience_relevance'], scores['genre_fit'],
            scores['accessibility'], scores['potential_reach'], scores['publishing_value'],
            score,
            genre_focus or None, accepts_queries, submission_deadline or None,
        ))
    print(f"\n  '{name}' added. Score: {score}/100.")
    input("  Press Enter to continue...")


def _update():
    db.header("Update Prospect")
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT id, type, name, score, status
            FROM prospects WHERE status != 'archived'
            ORDER BY type, name
        """).fetchall()
    db.print_table(
        ["ID", "Type", "Name", "Score", "Status"],
        [(r['id'], r['type'], r['name'], r['score'], r['status']) for r in rows],
    )

    prospect_id = db.prompt("Prospect ID to update")
    if not prospect_id:
        return

    with db.connect() as conn:
        row = conn.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
    if not row:
        print("  Not found.")
        input("  Press Enter to continue...")
        return

    print(f"\n  Updating: {row['name']} ({row['type']})  |  Current score: {row['score']}/100")
    print("  (Press Enter to keep current value)\n")

    name          = db.prompt("Name", row['name']) or row['name']
    url           = db.prompt("URL", row['url'] or '') or row['url']
    contact_name  = db.prompt("Contact name", row['contact_name'] or '') or row['contact_name']
    contact_email = db.prompt("Contact email", row['contact_email'] or '') or row['contact_email']
    notes         = db.prompt("Notes", row['notes'] or '') or row['notes']
    new_status    = db.choose("Status", STATUSES)

    rescore = input("\n  Re-score this prospect? (y/N): ").strip().lower()
    if rescore == 'y':
        print("\n  --- RE-SCORING ---")
        scores = {}
        for field, label, levels in SCORE_CRITERIA:
            print(f"\n  {label} (current: {row[field]}):")
            for level in levels:
                print(f"    {level}")
            val = input("  Score (0–4): ").strip()
            try:
                scores[field] = max(0, min(4, int(val)))
            except ValueError:
                scores[field] = row[field]
        score = compute_score(**scores)
    else:
        scores = {
            'audience_relevance': row['audience_relevance'],
            'genre_fit':          row['genre_fit'],
            'accessibility':      row['accessibility'],
            'potential_reach':    row['potential_reach'],
            'publishing_value':   row['publishing_value'],
        }
        score = row['score']

    with db.connect() as conn:
        conn.execute("""
            UPDATE prospects SET
                name = ?, url = ?, contact_name = ?, contact_email = ?,
                status = ?, notes = ?,
                audience_relevance = ?, genre_fit = ?, accessibility = ?,
                potential_reach = ?, publishing_value = ?, score = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            name, url, contact_name, contact_email, new_status, notes,
            scores['audience_relevance'], scores['genre_fit'], scores['accessibility'],
            scores['potential_reach'], scores['publishing_value'], score,
            prospect_id,
        ))
    print(f"\n  Updated. Score: {score}/100  Status: {new_status}")
    input("  Press Enter to continue...")


def _archive():
    db.header("Archive Prospect")
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT id, type, name, score, status
            FROM prospects WHERE status != 'archived'
            ORDER BY type, name
        """).fetchall()
    db.print_table(
        ["ID", "Type", "Name", "Score", "Status"],
        [(r['id'], r['type'], r['name'], r['score'], r['status']) for r in rows],
    )

    prospect_id = db.prompt("Prospect ID to archive")
    if not prospect_id:
        return

    with db.connect() as conn:
        row = conn.execute("SELECT name FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
    if not row:
        print("  Not found.")
        input("  Press Enter to continue...")
        return

    confirm = input(f"  Archive '{row['name']}'? This is reversible via Update. (y/N): ").strip().lower()
    if confirm != 'y':
        print("  Cancelled.")
        input("  Press Enter to continue...")
        return

    with db.connect() as conn:
        conn.execute(
            "UPDATE prospects SET status = 'archived', updated_at = datetime('now') WHERE id = ?",
            (prospect_id,),
        )
    print(f"  '{row['name']}' archived.")
    input("  Press Enter to continue...")


def generate_report(save_path=None):
    """Generate a weekly opportunity report in markdown. Prints to screen or writes to file."""
    today      = date.today()
    week_num   = today.isocalendar()[1]
    year       = today.isocalendar()[0]
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    week_end   = (today + timedelta(days=6 - today.weekday())).isoformat()

    with db.connect() as conn:
        total_active = conn.execute(
            "SELECT COUNT(*) FROM prospects WHERE status != 'archived'"
        ).fetchone()[0]

        new_this_week = conn.execute(
            "SELECT COUNT(*) FROM prospects WHERE discovered_date >= ?",
            (week_start,),
        ).fetchone()[0]

        by_type = conn.execute("""
            SELECT type, COUNT(*) as count
            FROM prospects WHERE status != 'archived'
            GROUP BY type ORDER BY type
        """).fetchall()

        by_status = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM prospects GROUP BY status ORDER BY count DESC
        """).fetchall()

        top_prospects = conn.execute("""
            SELECT id, type, name, score, status, url, notes
            FROM prospects
            WHERE score >= 60 AND status != 'archived'
            ORDER BY score DESC, type, name
            LIMIT 40
        """).fetchall()

        followup_cutoff = (today - timedelta(days=14)).isoformat()
        needs_followup = conn.execute("""
            SELECT id, type, name, score, updated_at, contact_name
            FROM prospects
            WHERE status = 'contacted' AND updated_at <= ?
            ORDER BY score DESC
        """, (followup_cutoff,)).fetchall()

        new_prospects = conn.execute("""
            SELECT id, type, name, score, url
            FROM prospects
            WHERE discovered_date >= ?
            ORDER BY score DESC
        """, (week_start,)).fetchall()

        upcoming_deadlines = conn.execute("""
            SELECT name, type, submission_deadline
            FROM prospects
            WHERE submission_deadline IS NOT NULL
              AND submission_deadline >= ?
              AND submission_deadline <= date(?, '+60 days')
              AND status NOT IN ('rejected', 'archived')
            ORDER BY submission_deadline
        """, (today.isoformat(), today.isoformat())).fetchall()

    lines = [
        f"# Opportunity Hunter — Weekly Report",
        f"",
        f"**Author:** Janee Butterfield  ",
        f"**Week:** {week_start} – {week_end} (Week {week_num}, {year})  ",
        f"**Generated:** {today.isoformat()}",
        f"",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total Active Prospects | {total_active} |",
        f"| New This Week | {new_this_week} |",
        f"| Needs Follow-Up | {len(needs_followup)} |",
        "",
        "**By Type:**",
        "",
        "| Type | Count |",
        "|------|-------|",
    ]

    type_counts = {r['type']: r['count'] for r in by_type}
    for t in TYPES:
        lines.append(f"| {TYPE_DISPLAY[t]} | {type_counts.get(t, 0)} |")

    lines += [
        "",
        "**By Status:**",
        "",
        "| Status | Count |",
        "|--------|-------|",
    ]
    for r in by_status:
        lines.append(f"| {r['status'].capitalize()} | {r['count']} |")

    lines += ["", "---", "", "## Top Prospects (Score 60+)", ""]

    if top_prospects:
        for t in TYPES:
            type_rows = [r for r in top_prospects if r['type'] == t]
            if not type_rows:
                continue
            lines.append(f"### {TYPE_DISPLAY[t]}")
            lines += [
                "",
                "| Score | Name | Status | URL | Notes |",
                "|-------|------|--------|-----|-------|",
            ]
            for r in type_rows:
                url   = r['url'] or ''
                notes = (r['notes'] or '').replace('\n', ' ')[:80]
                lines.append(f"| {r['score']} | {r['name']} | {r['status']} | {url} | {notes} |")
            lines.append("")
    else:
        lines += ["_No prospects scored 60+ yet. Add and score some prospects._", ""]

    lines += ["---", ""]

    if needs_followup:
        lines += [
            "## Action Required — Needs Follow-Up",
            "",
            "Contacted 14+ days ago with no status update:",
            "",
            "| ID | Type | Name | Score | Last Updated | Contact |",
            "|----|------|------|-------|-------------|---------|",
        ]
        for r in needs_followup:
            lines.append(
                f"| {r['id']} | {TYPE_DISPLAY[r['type']]} | {r['name']} "
                f"| {r['score']} | {r['updated_at'][:10]} | {r['contact_name'] or ''} |"
            )
        lines += ["", "---", ""]

    if upcoming_deadlines:
        lines += [
            "## Upcoming Deadlines (next 60 days)",
            "",
            "| Name | Type | Deadline |",
            "|------|------|----------|",
        ]
        for r in upcoming_deadlines:
            lines.append(f"| {r['name']} | {TYPE_DISPLAY[r['type']]} | {r['submission_deadline']} |")
        lines += ["", "---", ""]

    if new_prospects:
        lines += [
            "## New This Week",
            "",
            "| Score | Type | Name | URL |",
            "|-------|------|------|-----|",
        ]
        for r in new_prospects:
            lines.append(
                f"| {r['score']} | {TYPE_DISPLAY[r['type']]} | {r['name']} | {r['url'] or ''} |"
            )
        lines += ["", "---", ""]

    report = '\n'.join(lines)

    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        with open(save_path, 'w') as f:
            f.write(report)
        print(f"  Report saved to: {save_path}")
    else:
        db.header(f"OPPORTUNITY REPORT  Week {week_num}, {year}")
        print()
        print(report)
        print()
        save = input("  Save as markdown file? (y/N): ").strip().lower()
        if save == 'y':
            os.makedirs("reports", exist_ok=True)
            filename = f"reports/opportunity_report_{year}-W{week_num:02d}.md"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"  Saved to: {filename}")
        input("\n  Press Enter to continue...")

    return report


def get_top_prospects_summary(limit=5):
    """Return top active prospects for inclusion in other reports."""
    with db.connect() as conn:
        return conn.execute("""
            SELECT type, name, score, status, url, accepts_queries
            FROM prospects
            WHERE status NOT IN ('rejected', 'archived')
            ORDER BY score DESC
            LIMIT ?
        """, (limit,)).fetchall()


def _stats():
    db.header("Opportunity Hunter Stats")

    with db.connect() as conn:
        total  = conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM prospects WHERE status != 'archived'").fetchone()[0]
        avg    = conn.execute("SELECT AVG(score) FROM prospects WHERE status != 'archived'").fetchone()[0] or 0
        high   = conn.execute(
            "SELECT COUNT(*) FROM prospects WHERE score >= 75 AND status != 'archived'"
        ).fetchone()[0]

        by_type = conn.execute("""
            SELECT type, COUNT(*) as total, AVG(score) as avg_score, MAX(score) as max_score
            FROM prospects WHERE status != 'archived'
            GROUP BY type ORDER BY avg_score DESC
        """).fetchall()

        by_status = conn.execute("""
            SELECT status, COUNT(*) as count FROM prospects GROUP BY status ORDER BY count DESC
        """).fetchall()

    print(f"\n  Total prospects:      {total}")
    print(f"  Active:               {active}")
    print(f"  High priority (75+):  {high}")
    print(f"  Average score:        {avg:.1f}")

    if by_type:
        print()
        db.print_table(
            ["Type", "Count", "Avg Score", "Max Score"],
            [(TYPE_DISPLAY[r['type']], r['total'], f"{r['avg_score']:.0f}", r['max_score'])
             for r in by_type],
        )

    if by_status:
        print()
        db.print_table(
            ["Status", "Count"],
            [(r['status'].capitalize(), r['count']) for r in by_status],
        )

    input("\n  Press Enter to continue...")


SAMPLE_DATA = [
    # Podcasts
    {
        'type': 'podcast', 'name': 'No Sleep Podcast',
        'url': 'https://www.nosleeppodcast.com',
        'contact_name': 'David Cummings (Producer)',
        'notes': 'Premier horror fiction podcast. Largest horror audio fiction audience online. Accepts original horror fiction submissions.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 2, 'potential_reach': 4, 'publishing_value': 3,
        'genre_focus': 'horror',
    },
    {
        'type': 'podcast', 'name': 'This Is Horror',
        'url': 'https://www.thisishorror.co.uk/podcast/',
        'contact_name': 'Michael David Wilson (Host)',
        'notes': 'UK-based horror podcast. Author interviews. Well-connected in horror community. Good industry credibility.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 4,
        'genre_focus': 'horror',
    },
    {
        'type': 'podcast', 'name': 'The Horror Show with Brian Keene',
        'url': 'https://briankeene.com/podcast/',
        'contact_name': 'Brian Keene (Host)',
        'notes': 'Brian Keene is a prominent horror author. Guests are typically established horror authors. Strong industry credibility.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 2, 'potential_reach': 3, 'publishing_value': 4,
        'genre_focus': 'horror',
    },
    {
        'type': 'podcast', 'name': 'Scream Queens',
        'url': 'https://screamqueenspodcast.com',
        'notes': 'Celebrates women in horror. Indie-author friendly. Good audience alignment.',
        'audience_relevance': 4, 'genre_fit': 3, 'accessibility': 4, 'potential_reach': 2, 'publishing_value': 2,
        'genre_focus': 'horror',
    },
    {
        'type': 'podcast', 'name': 'Thriller Writers Podcast',
        'url': 'https://thrillerfest.com',
        'notes': 'ITW-affiliated. Interviews thriller authors. Good for genre visibility in the thriller community.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 2, 'potential_reach': 3, 'publishing_value': 3,
        'genre_focus': 'thriller',
    },
    # Literary Agents
    {
        'type': 'agent', 'name': 'DongWon Song — Howard Morhaim Literary',
        'url': 'https://www.hmorhaim.com/agents/dongwon-song/',
        'contact_name': 'DongWon Song',
        'notes': 'Represents horror, dark SFF, literary fiction. Active on MSWL. Very respected in horror community. Query via QueryManager.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 4, 'publishing_value': 4,
        'accepts_queries': 1, 'genre_focus': 'horror',
    },
    {
        'type': 'agent', 'name': 'Eddie Schneider — JABberwocky Literary',
        'url': 'https://www.jabberwockyliterary.com/agents',
        'contact_name': 'Eddie Schneider',
        'notes': 'Represents horror and dark fiction. Strong horror genre focus. Query via email per guidelines.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 4,
        'accepts_queries': 1, 'genre_focus': 'horror',
    },
    {
        'type': 'agent', 'name': 'Stacia Decker — Donald Maass Literary',
        'url': 'https://donaldmaass.com/agents/',
        'contact_name': 'Stacia Decker',
        'notes': 'Specializes in thrillers and dark literary fiction. Donald Maass is a top-tier agency. Competitive.',
        'audience_relevance': 4, 'genre_fit': 3, 'accessibility': 2, 'potential_reach': 4, 'publishing_value': 4,
        'accepts_queries': 1, 'genre_focus': 'thriller',
    },
    {
        'type': 'agent', 'name': 'Rachel Brooks — BookEnds Literary',
        'url': 'https://bookendsliterary.com',
        'contact_name': 'Rachel Brooks',
        'notes': 'Represents adult horror and thriller. BookEnds is well-regarded. Active on social media.',
        'audience_relevance': 4, 'genre_fit': 3, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 4,
        'accepts_queries': 1, 'genre_focus': 'horror',
    },
    # Publishers
    {
        'type': 'publisher', 'name': 'Cemetery Dance Publications',
        'url': 'https://www.cemeterydance.com',
        'notes': 'Premier indie horror publisher. Novels, novellas, short collections. King, Straub, Masterton on their list. High prestige.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 4,
        'accepts_queries': 1, 'genre_focus': 'horror',
    },
    {
        'type': 'publisher', 'name': 'Tor Nightfire (Macmillan)',
        'url': 'https://us.macmillan.com/torbooks/nightfire/',
        'notes': "Macmillan's dedicated horror imprint. Major traditional publisher. Submission via literary agent only.",
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 1, 'potential_reach': 4, 'publishing_value': 4,
        'accepts_queries': 0, 'genre_focus': 'horror',
    },
    {
        'type': 'publisher', 'name': 'Flame Tree Press',
        'url': 'https://www.flametreepress.com',
        'notes': 'UK-based genre publisher. Horror and thriller novels. Accepts unagented queries. Good production quality.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 3,
        'accepts_queries': 1, 'genre_focus': 'horror',
    },
    {
        'type': 'publisher', 'name': 'Dark Regions Press',
        'url': 'https://www.darkregions.com',
        'notes': 'Independent horror publisher. Novels and collections. Accepts submissions directly. Respected in horror community.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 4, 'potential_reach': 2, 'publishing_value': 3,
        'accepts_queries': 1, 'genre_focus': 'horror',
    },
    # Festivals & Conventions
    {
        'type': 'festival', 'name': 'StokerCon',
        'url': 'https://stokercon.com',
        'notes': 'Annual convention of the Horror Writers Association (HWA). Bram Stoker Awards presented here. Premier networking event for horror authors.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 4,
        'genre_focus': 'horror',
    },
    {
        'type': 'festival', 'name': 'ThrillerFest',
        'url': 'https://thrillerfest.com',
        'notes': 'Annual International Thriller Writers conference. Strong agent and editor presence. Includes PitchFest for in-person pitches.',
        'audience_relevance': 4, 'genre_fit': 3, 'accessibility': 2, 'potential_reach': 3, 'publishing_value': 4,
        'genre_focus': 'thriller',
    },
    {
        'type': 'festival', 'name': 'Killer Nashville',
        'url': 'https://www.killernashville.com',
        'notes': 'Thriller and mystery conference. Approachable for emerging authors. Includes pitching sessions with agents.',
        'audience_relevance': 4, 'genre_fit': 3, 'accessibility': 4, 'potential_reach': 2, 'publishing_value': 3,
        'genre_focus': 'thriller',
    },
    {
        'type': 'festival', 'name': 'World Horror Convention',
        'url': 'https://worldhorrorconvention.com',
        'notes': 'Annual rotating horror convention. Strong horror community attendance. Good networking with authors, editors, and publishers.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 3,
        'genre_focus': 'horror',
    },
    # Reviewers
    {
        'type': 'reviewer', 'name': 'Cemetery Dance Magazine',
        'url': 'https://www.cemeterydance.com/magazine/',
        'notes': 'Premier horror review publication. Reviews and interviews. Very high industry credibility in the horror genre.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 4,
        'genre_focus': 'horror',
    },
    {
        'type': 'reviewer', 'name': 'LitReactor',
        'url': 'https://litreactor.com',
        'notes': 'Literary community with horror focus. Reviews, interviews, craft essays. Engaged horror reader and writer audience.',
        'audience_relevance': 4, 'genre_fit': 3, 'accessibility': 3, 'potential_reach': 3, 'publishing_value': 2,
        'genre_focus': 'horror',
    },
    {
        'type': 'reviewer', 'name': 'Locus Magazine',
        'url': 'https://locusmag.com',
        'notes': 'Industry standard SF/F/Horror review publication. Placement here signals legitimacy to agents and editors.',
        'audience_relevance': 3, 'genre_fit': 3, 'accessibility': 2, 'potential_reach': 3, 'publishing_value': 4,
        'genre_focus': 'horror',
    },
    # Bloggers
    {
        'type': 'blogger', 'name': 'Dread Central',
        'url': 'https://www.dreadcentral.com',
        'notes': 'Major horror media website. Large audience. Covers books, film, TV. High reach for horror genre.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 2, 'potential_reach': 4, 'publishing_value': 2,
        'genre_focus': 'horror',
    },
    {
        'type': 'blogger', 'name': 'Horror DNA',
        'url': 'https://www.horrordna.com',
        'notes': 'Dedicated horror review site. Covers books and media. Open to indie authors for review requests.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 4, 'potential_reach': 2, 'publishing_value': 2,
        'genre_focus': 'horror',
    },
    {
        'type': 'blogger', 'name': 'The Haunted Reading Room',
        'url': 'https://thehauntedreadingroom.com',
        'notes': 'Dedicated horror book review blog. Active on BookTok and Bookstagram. Open to indie authors.',
        'audience_relevance': 4, 'genre_fit': 4, 'accessibility': 4, 'potential_reach': 2, 'publishing_value': 2,
        'genre_focus': 'horror',
    },
]


def _seed():
    db.header("Load Sample Data")
    with db.connect() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]

    if existing > 0:
        print(f"\n  {existing} prospect(s) already in database.")
        confirm = input("  Load sample data anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("  Cancelled.")
            input("  Press Enter to continue...")
            return

    loaded = 0
    with db.connect() as conn:
        for entry in SAMPLE_DATA:
            score = compute_score(
                entry['audience_relevance'], entry['genre_fit'],
                entry['accessibility'], entry['potential_reach'], entry['publishing_value'],
            )
            conn.execute("""
                INSERT INTO prospects (
                    type, name, url, contact_name, notes,
                    audience_relevance, genre_fit, accessibility, potential_reach, publishing_value,
                    score, genre_focus, accepts_queries
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry['type'], entry['name'],
                entry.get('url'), entry.get('contact_name'), entry.get('notes'),
                entry['audience_relevance'], entry['genre_fit'],
                entry['accessibility'], entry['potential_reach'], entry['publishing_value'],
                score,
                entry.get('genre_focus'), entry.get('accepts_queries'),
            ))
            loaded += 1

    print(f"\n  Loaded {loaded} sample prospects.")
    input("  Press Enter to continue...")
