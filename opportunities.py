"""Opportunity tracker — anthologies, magazines, contests, speaking, etc."""
from datetime import date
import db

TYPES    = ["Anthology", "Magazine", "Contest", "Speaking", "Interview",
            "Review Request", "Feature", "Podcast", "Other"]
STATUSES = ["Open", "Submitted", "Accepted", "Rejected", "Withdrawn", "Expired"]


def menu():
    while True:
        db.header("OPPORTUNITY TRACKER")
        print("  1. View open opportunities")
        print("  2. View upcoming deadlines")
        print("  3. View all opportunities")
        print("  4. Add opportunity")
        print("  5. Update status")
        print("  6. Summary by type")
        print("  0. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            _list_by_status("Open")
        elif choice == "2":
            _upcoming_deadlines()
        elif choice == "3":
            _list_all()
        elif choice == "4":
            _add()
        elif choice == "5":
            _update_status()
        elif choice == "6":
            _summary()
        elif choice == "0":
            break


def _list_all():
    db.header("All Opportunities")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT o.id, o.type, o.title, o.publisher, o.deadline, o.pay, "
            "o.status, b.title as book "
            "FROM opportunities o "
            "LEFT JOIN books b ON o.book_id = b.id "
            "ORDER BY o.deadline NULLS LAST, o.status"
        ).fetchall()
    db.print_table(
        ["ID", "Type", "Title", "Publisher", "Deadline", "Pay", "Status", "Book"],
        rows,
    )
    input("\n  Press Enter to continue...")


def _list_by_status(status):
    db.header(f"Opportunities — {status}")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT o.id, o.type, o.title, o.publisher, o.deadline, o.pay, "
            "b.title as book "
            "FROM opportunities o "
            "LEFT JOIN books b ON o.book_id = b.id "
            "WHERE o.status = ? "
            "ORDER BY o.deadline NULLS LAST",
            (status,),
        ).fetchall()
    db.print_table(["ID", "Type", "Title", "Publisher", "Deadline", "Pay", "Book"], rows)
    input("\n  Press Enter to continue...")


def _upcoming_deadlines():
    db.header("Upcoming Deadlines (next 90 days)")
    today = date.today().isoformat()
    ninety = date.today().replace(day=date.today().day).isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, type, title, publisher, deadline, pay, status "
            "FROM opportunities "
            "WHERE deadline >= ? AND deadline <= date(?, '+90 days') "
            "AND status IN ('Open', 'Submitted') "
            "ORDER BY deadline",
            (today, today),
        ).fetchall()
    db.print_table(["ID", "Type", "Title", "Publisher", "Deadline", "Pay", "Status"], rows)

    overdue = _check_overdue()
    if overdue:
        print(f"\n  *** {len(overdue)} PAST DEADLINE (still marked Open): ***")
        db.print_table(["ID", "Title", "Deadline"], overdue)
    input("\n  Press Enter to continue...")


def _check_overdue():
    today = date.today().isoformat()
    with db.connect() as conn:
        return conn.execute(
            "SELECT id, title, deadline FROM opportunities "
            "WHERE deadline < ? AND status = 'Open'",
            (today,),
        ).fetchall()


def _add():
    db.header("Add Opportunity")
    opp_type  = db.choose("Type", TYPES)
    title     = db.prompt("Title / publication name")
    if not title:
        print("  Title required.")
        return
    publisher = db.prompt("Publisher / organizer")
    deadline  = db.prompt("Deadline (YYYY-MM-DD)")
    pay       = db.prompt("Payment / rate")
    notes     = db.prompt("Notes")

    book_id = _pick_book()

    with db.connect() as conn:
        conn.execute(
            "INSERT INTO opportunities (type, title, publisher, deadline, pay, "
            "book_id, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (opp_type, title, publisher or None, deadline or None,
             pay or None, book_id, notes or None),
        )
    print(f"\n  Opportunity '{title}' added.")
    input("  Press Enter to continue...")


def _pick_book():
    with db.connect() as conn:
        books = conn.execute("SELECT id, title FROM books").fetchall()
    print("\n  Link to a book? (optional)")
    for b in books:
        print(f"    {b['id']}. {b['title']}")
    print("    0. None")
    val = input("  Choice: ").strip()
    try:
        bid = int(val)
        return bid if bid > 0 else None
    except ValueError:
        return None


def _update_status():
    db.header("Update Opportunity Status")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, title, status, deadline FROM opportunities ORDER BY deadline NULLS LAST"
        ).fetchall()
    db.print_table(["ID", "Title", "Status", "Deadline"], rows)

    opp_id = db.prompt("Opportunity ID to update")
    if not opp_id:
        return
    with db.connect() as conn:
        row = conn.execute(
            "SELECT title, status FROM opportunities WHERE id = ?", (opp_id,)
        ).fetchone()
    if not row:
        print("  Not found.")
        input("  Press Enter to continue...")
        return

    print(f"\n  Opportunity: {row['title']}  |  Current status: {row['status']}")
    new_status = db.choose("New status", STATUSES)

    response_date = None
    submitted_date = None
    if new_status == "Submitted":
        submitted_date = db.prompt("Submission date (YYYY-MM-DD, blank = today)")
        if not submitted_date:
            submitted_date = date.today().isoformat()
    elif new_status in ("Accepted", "Rejected", "Withdrawn"):
        response_date = db.prompt("Response date (YYYY-MM-DD, blank = today)")
        if not response_date:
            response_date = date.today().isoformat()

    with db.connect() as conn:
        conn.execute(
            "UPDATE opportunities SET status = ?, submitted_date = COALESCE(?, submitted_date), "
            "response_date = COALESCE(?, response_date) WHERE id = ?",
            (new_status, submitted_date, response_date, opp_id),
        )
    print(f"\n  Updated to '{new_status}'.")
    input("  Press Enter to continue...")


def _summary():
    db.header("Opportunity Summary by Type")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT type, "
            "SUM(CASE WHEN status='Open' THEN 1 ELSE 0 END) as open, "
            "SUM(CASE WHEN status='Submitted' THEN 1 ELSE 0 END) as submitted, "
            "SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END) as accepted, "
            "SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END) as rejected "
            "FROM opportunities GROUP BY type ORDER BY type"
        ).fetchall()
    db.print_table(["Type", "Open", "Submitted", "Accepted", "Rejected"], rows)
    input("\n  Press Enter to continue...")
