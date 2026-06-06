"""Content calendar — plan and track posts across platforms."""
from datetime import date, timedelta
import db

PLATFORMS = ["Blog", "Instagram", "X/Twitter", "Facebook",
             "Newsletter", "TikTok", "YouTube", "Podcast", "Other"]
TYPES     = ["Post", "Story", "Reel", "Newsletter", "Blog Post",
             "Video", "Promo", "Review", "Interview", "Other"]
STATUSES  = ["Planned", "Drafted", "Scheduled", "Published", "Skipped"]


def menu():
    while True:
        db.header("CONTENT CALENDAR")
        print("  1. This week")
        print("  2. Next 30 days")
        print("  3. View by platform")
        print("  4. Add content item")
        print("  5. Mark as published")
        print("  6. Update status")
        print("  7. All upcoming")
        print("  0. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            _this_week()
        elif choice == "2":
            _next_n_days(30)
        elif choice == "3":
            _by_platform()
        elif choice == "4":
            _add()
        elif choice == "5":
            _mark_published()
        elif choice == "6":
            _update_status()
        elif choice == "7":
            _upcoming()
        elif choice == "0":
            break


def _this_week():
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    week_end   = (today + timedelta(days=6 - today.weekday())).isoformat()
    db.header(f"This Week  ({week_start} – {week_end})")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, platform, content_type, title, status "
            "FROM calendar "
            "WHERE scheduled_date BETWEEN ? AND ? "
            "ORDER BY scheduled_date, platform",
            (week_start, week_end),
        ).fetchall()
    db.print_table(["ID", "Date", "Platform", "Type", "Title", "Status"], rows)
    _show_overdue()
    input("\n  Press Enter to continue...")


def _next_n_days(n):
    today = date.today().isoformat()
    future = (date.today() + timedelta(days=n)).isoformat()
    db.header(f"Next {n} Days")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, platform, content_type, title, status "
            "FROM calendar "
            "WHERE scheduled_date BETWEEN ? AND ? "
            "ORDER BY scheduled_date, platform",
            (today, future),
        ).fetchall()
    db.print_table(["ID", "Date", "Platform", "Type", "Title", "Status"], rows)
    input("\n  Press Enter to continue...")


def _by_platform():
    platform = db.choose("Platform", PLATFORMS)
    db.header(f"Content — {platform}")
    today = date.today().isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, content_type, title, status "
            "FROM calendar "
            "WHERE platform = ? AND scheduled_date >= ? "
            "ORDER BY scheduled_date",
            (platform, today),
        ).fetchall()
    db.print_table(["ID", "Date", "Type", "Title", "Status"], rows)
    input("\n  Press Enter to continue...")


def _add():
    db.header("Add Content Item")
    scheduled_date = db.prompt("Date (YYYY-MM-DD)")
    if not scheduled_date:
        print("  Date required.")
        return
    platform     = db.choose("Platform", PLATFORMS)
    content_type = db.choose("Content type", TYPES)
    title        = db.prompt("Title / topic")
    if not title:
        print("  Title required.")
        return
    body  = db.prompt("Content / notes (optional)")
    notes = db.prompt("Additional notes")

    with db.connect() as conn:
        conn.execute(
            "INSERT INTO calendar (scheduled_date, platform, content_type, title, body, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (scheduled_date, platform, content_type, title,
             body or None, notes or None),
        )
    print(f"\n  '{title}' added to calendar.")
    input("  Press Enter to continue...")


def _mark_published():
    db.header("Mark as Published")
    today = date.today().isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, platform, title, status "
            "FROM calendar WHERE status != 'Published' "
            "ORDER BY scheduled_date",
        ).fetchall()
    db.print_table(["ID", "Date", "Platform", "Title", "Status"], rows)
    item_id = db.prompt("Item ID to mark published")
    if not item_id:
        return
    published_date = db.prompt(f"Published date (YYYY-MM-DD, blank = today)")
    if not published_date:
        published_date = today
    with db.connect() as conn:
        conn.execute(
            "UPDATE calendar SET status = 'Published', published_date = ? WHERE id = ?",
            (published_date, item_id),
        )
    print("  Marked as published.")
    input("  Press Enter to continue...")


def _update_status():
    db.header("Update Content Status")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, platform, title, status "
            "FROM calendar ORDER BY scheduled_date"
        ).fetchall()
    db.print_table(["ID", "Date", "Platform", "Title", "Status"], rows)
    item_id = db.prompt("Item ID")
    if not item_id:
        return
    new_status = db.choose("New status", STATUSES)
    with db.connect() as conn:
        conn.execute("UPDATE calendar SET status = ? WHERE id = ?", (new_status, item_id))
    print(f"  Updated to '{new_status}'.")
    input("  Press Enter to continue...")


def _upcoming():
    db.header("All Upcoming Content")
    today = date.today().isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, platform, content_type, title, status "
            "FROM calendar WHERE scheduled_date >= ? "
            "ORDER BY scheduled_date, platform",
            (today,),
        ).fetchall()
    db.print_table(["ID", "Date", "Platform", "Type", "Title", "Status"], rows)
    input("\n  Press Enter to continue...")


def _show_overdue():
    today = date.today().isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, scheduled_date, platform, title "
            "FROM calendar WHERE scheduled_date < ? AND status IN ('Planned','Drafted','Scheduled')",
            (today,),
        ).fetchall()
    if rows:
        print(f"\n  *** {len(rows)} OVERDUE item(s) ***")
        db.print_table(["ID", "Date", "Platform", "Title"], rows)
