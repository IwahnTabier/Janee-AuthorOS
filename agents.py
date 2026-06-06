"""Literary agent database — track queries, requests, and pipeline status."""
import db

STATUSES = ["Wishlist", "Queried", "Partial Requested", "Full Requested",
            "Offer", "Closed", "Rejected", "Passed"]


def menu():
    while True:
        db.header("LITERARY AGENT DATABASE")
        print("  1. View all agents")
        print("  2. View by status")
        print("  3. Add agent")
        print("  4. Update agent status")
        print("  5. Edit agent notes")
        print("  6. Pipeline summary")
        print("  0. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            _list_all()
        elif choice == "2":
            _list_by_status()
        elif choice == "3":
            _add()
        elif choice == "4":
            _update_status()
        elif choice == "5":
            _edit_notes()
        elif choice == "6":
            _pipeline_summary()
        elif choice == "0":
            break


def _list_all():
    db.header("All Agents")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, name, agency, status, query_date, response_date "
            "FROM agents ORDER BY status, name"
        ).fetchall()
    db.print_table(["ID", "Name", "Agency", "Status", "Queried", "Response"], rows)
    input("\n  Press Enter to continue...")


def _list_by_status():
    status = db.choose("Filter by status", STATUSES + ["All"])
    db.header(f"Agents — {status}")
    with db.connect() as conn:
        if status == "All":
            rows = conn.execute(
                "SELECT id, name, agency, status, query_date, response_date "
                "FROM agents ORDER BY name"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, agency, status, query_date, response_date "
                "FROM agents WHERE status = ? ORDER BY name",
                (status,),
            ).fetchall()
    db.print_table(["ID", "Name", "Agency", "Status", "Queried", "Response"], rows)
    input("\n  Press Enter to continue...")


def _add():
    db.header("Add Agent")
    name    = db.prompt("Full name")
    if not name:
        print("  Name required.")
        return
    agency  = db.prompt("Agency")
    email   = db.prompt("Email")
    website = db.prompt("Website")
    genres  = db.prompt("Genres they represent")
    status  = db.choose("Initial status", STATUSES)
    query_date = db.prompt("Query date (YYYY-MM-DD, blank = today)")
    if not query_date and status not in ("Wishlist",):
        from datetime import date
        query_date = date.today().isoformat()
    notes = db.prompt("Notes")

    with db.connect() as conn:
        conn.execute(
            "INSERT INTO agents (name, agency, email, website, genres, status, "
            "query_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, agency, email, website, genres, status, query_date or None, notes or None),
        )
    print(f"\n  Agent '{name}' added.")
    input("  Press Enter to continue...")


def _update_status():
    db.header("Update Agent Status")
    _list_all()
    agent_id = db.prompt("Agent ID to update")
    if not agent_id:
        return
    with db.connect() as conn:
        row = conn.execute("SELECT name, status FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not row:
        print("  Agent not found.")
        input("  Press Enter to continue...")
        return

    print(f"\n  Agent: {row['name']}  |  Current status: {row['status']}")
    new_status = db.choose("New status", STATUSES)
    response_date = db.prompt("Response date (YYYY-MM-DD, blank = today)")
    if not response_date:
        from datetime import date
        response_date = date.today().isoformat()

    with db.connect() as conn:
        conn.execute(
            "UPDATE agents SET status = ?, response_date = ? WHERE id = ?",
            (new_status, response_date, agent_id),
        )
    print(f"\n  Updated to '{new_status}'.")
    input("  Press Enter to continue...")


def _edit_notes():
    db.header("Edit Agent Notes")
    _list_all()
    agent_id = db.prompt("Agent ID")
    if not agent_id:
        return
    with db.connect() as conn:
        row = conn.execute("SELECT name, notes FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not row:
        print("  Agent not found.")
        input("  Press Enter to continue...")
        return

    print(f"\n  Agent: {row['name']}")
    print(f"  Current notes: {row['notes'] or '(none)'}")
    new_notes = db.prompt("New notes (blank to keep current)")
    if new_notes:
        with db.connect() as conn:
            conn.execute("UPDATE agents SET notes = ? WHERE id = ?", (new_notes, agent_id))
        print("  Notes updated.")
    input("  Press Enter to continue...")


def _pipeline_summary():
    db.header("Agent Pipeline Summary")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM agents GROUP BY status ORDER BY status"
        ).fetchall()
    db.print_table(["Status", "Count"], rows)

    with db.connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM agents WHERE status IN "
            "('Queried','Partial Requested','Full Requested','Offer')"
        ).fetchone()[0]
    print(f"\n  Total agents tracked: {total}")
    print(f"  Active in pipeline:   {active}")
    input("\n  Press Enter to continue...")
