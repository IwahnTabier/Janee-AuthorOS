"""Weekly reporting — log activity and generate weekly summaries."""
from datetime import date, timedelta
import db
import opportunity_hunter as oh


def menu():
    while True:
        db.header("WEEKLY REPORTS")
        print("  1. This week's report")
        print("  2. Log this week's activity")
        print("  3. View past reports")
        print("  4. Year-to-date summary")
        print("  0. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            _this_week_report()
        elif choice == "2":
            _log_week()
        elif choice == "3":
            _past_reports()
        elif choice == "4":
            _ytd_summary()
        elif choice == "0":
            break


def _this_week_report():
    week_start = db.current_week_start()
    week_end   = (date.fromisoformat(week_start) + timedelta(days=6)).isoformat()

    db.header(f"WEEKLY REPORT  {week_start} – {week_end}")

    # Auto-pull from other tables
    with db.connect() as conn:
        submitted = conn.execute(
            "SELECT COUNT(*) FROM opportunities WHERE submitted_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]
        responses = conn.execute(
            "SELECT COUNT(*) FROM opportunities WHERE response_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]
        accepted = conn.execute(
            "SELECT COUNT(*) FROM opportunities "
            "WHERE status = 'Accepted' AND response_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]
        rejected = conn.execute(
            "SELECT COUNT(*) FROM opportunities "
            "WHERE status = 'Rejected' AND response_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]
        queries_sent = conn.execute(
            "SELECT COUNT(*) FROM agents WHERE query_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]
        agent_responses = conn.execute(
            "SELECT COUNT(*) FROM agents WHERE response_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]
        content_published = conn.execute(
            "SELECT COUNT(*) FROM calendar WHERE published_date BETWEEN ? AND ?",
            (week_start, week_end),
        ).fetchone()[0]

        log = conn.execute(
            "SELECT * FROM weekly_log WHERE week_start = ?", (week_start,)
        ).fetchone()

    words = log["words_written"] if log else 0
    notes = log["notes"] if log else ""

    print(f"\n  WRITING")
    print(f"    Words written:      {words:,}")
    print(f"\n  SUBMISSIONS & QUERIES")
    print(f"    Submissions sent:   {submitted}")
    print(f"    Agent queries sent: {queries_sent}")
    print(f"    Responses received: {responses + agent_responses}")
    print(f"      Acceptances:      {accepted}")
    print(f"      Rejections:       {rejected}")
    print(f"\n  CONTENT")
    print(f"    Items published:    {content_published}")

    if notes:
        print(f"\n  NOTES")
        print(f"    {notes}")

    # Open opportunities with upcoming deadlines
    today = date.today().isoformat()
    with db.connect() as conn:
        upcoming = conn.execute(
            "SELECT title, deadline FROM opportunities "
            "WHERE status = 'Open' AND deadline >= ? "
            "ORDER BY deadline LIMIT 5",
            (today,),
        ).fetchall()
    if upcoming:
        print(f"\n  UPCOMING DEADLINES")
        for opp in upcoming:
            print(f"    {opp['deadline']}  {opp['title']}")

    top = oh.get_top_prospects_summary(limit=5)
    if top:
        print(f"\n  TOP PROSPECTS (Opportunity Hunter)")
        for p in top:
            queries = " [open queries]" if p['accepts_queries'] else ""
            print(f"    [{p['score']:3d}] {oh.TYPE_DISPLAY[p['type']]:<25} {p['name']}{queries}")

    input("\n  Press Enter to continue...")


def _log_week():
    week_start = db.current_week_start()
    db.header(f"Log Week of {week_start}")

    with db.connect() as conn:
        existing = conn.execute(
            "SELECT * FROM weekly_log WHERE week_start = ?", (week_start,)
        ).fetchone()

    if existing:
        print(f"  Existing log found. Updating.")
        words = db.prompt_int("Words written this week", existing["words_written"])
        notes = db.prompt("Notes / highlights", existing["notes"] or "")
        with db.connect() as conn:
            conn.execute(
                "UPDATE weekly_log SET words_written = ?, notes = ? WHERE week_start = ?",
                (words, notes or None, week_start),
            )
    else:
        words = db.prompt_int("Words written this week", 0)
        notes = db.prompt("Notes / highlights")
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO weekly_log (week_start, words_written, notes) VALUES (?, ?, ?)",
                (week_start, words, notes or None),
            )
    print("  Week logged.")
    input("  Press Enter to continue...")


def _past_reports():
    db.header("Past Weekly Logs")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT week_start, words_written, notes FROM weekly_log "
            "ORDER BY week_start DESC LIMIT 12"
        ).fetchall()
    db.print_table(["Week Start", "Words Written", "Notes"], rows)
    input("\n  Press Enter to continue...")


def _ytd_summary():
    year = date.today().year
    year_start = f"{year}-01-01"
    year_end   = f"{year}-12-31"

    db.header(f"Year-to-Date Summary — {year}")

    with db.connect() as conn:
        total_words = conn.execute(
            "SELECT SUM(words_written) FROM weekly_log WHERE week_start >= ?",
            (year_start,),
        ).fetchone()[0] or 0

        total_submitted = conn.execute(
            "SELECT COUNT(*) FROM opportunities WHERE submitted_date BETWEEN ? AND ?",
            (year_start, year_end),
        ).fetchone()[0]

        total_accepted = conn.execute(
            "SELECT COUNT(*) FROM opportunities "
            "WHERE status = 'Accepted' AND response_date BETWEEN ? AND ?",
            (year_start, year_end),
        ).fetchone()[0]

        total_rejected = conn.execute(
            "SELECT COUNT(*) FROM opportunities "
            "WHERE status = 'Rejected' AND response_date BETWEEN ? AND ?",
            (year_start, year_end),
        ).fetchone()[0]

        total_queries = conn.execute(
            "SELECT COUNT(*) FROM agents WHERE query_date BETWEEN ? AND ?",
            (year_start, year_end),
        ).fetchone()[0]

        total_published = conn.execute(
            "SELECT COUNT(*) FROM calendar WHERE published_date BETWEEN ? AND ?",
            (year_start, year_end),
        ).fetchone()[0]

    accept_rate = (
        f"{(total_accepted / total_submitted * 100):.1f}%"
        if total_submitted > 0 else "N/A"
    )

    print(f"\n  WRITING")
    print(f"    Total words written:     {total_words:,}")
    print(f"\n  SUBMISSIONS")
    print(f"    Total submitted:         {total_submitted}")
    print(f"    Accepted:                {total_accepted}")
    print(f"    Rejected:                {total_rejected}")
    print(f"    Acceptance rate:         {accept_rate}")
    print(f"\n  AGENTS")
    print(f"    Queries sent:            {total_queries}")
    print(f"\n  CONTENT")
    print(f"    Items published:         {total_published}")

    input("\n  Press Enter to continue...")
