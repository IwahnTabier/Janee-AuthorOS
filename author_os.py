#!/usr/bin/env python3
"""
Author OS — Janee Butterfield
Horror & Thriller Author Operating System
"""
import sys
import db
import agents
import opportunities
import calendar_mod
import reports
import opportunity_hunter


def main_menu():
    while True:
        print("\n" + "=" * 50)
        print("   JANEE BUTTERFIELD — AUTHOR OPERATING SYSTEM")
        print("=" * 50)
        print("   Books: Caught in Cryptic  |  Falling Cryptic")
        print("          Nighty Night Dear")
        print("=" * 50)
        print("   1. Opportunity Tracker")
        print("   2. Literary Agent Database")
        print("   3. Content Calendar")
        print("   4. Weekly Report")
        print("   5. My Books")
        print("   6. Opportunity Hunter")
        print("   0. Exit")
        print("=" * 50)
        choice = input("\n   Choice: ").strip()

        if choice == "1":
            opportunities.menu()
        elif choice == "2":
            agents.menu()
        elif choice == "3":
            calendar_mod.menu()
        elif choice == "4":
            reports.menu()
        elif choice == "5":
            _books()
        elif choice == "6":
            opportunity_hunter.menu()
        elif choice == "0":
            print("\n   Until next time, Janee.\n")
            sys.exit(0)


def _books():
    db.header("MY BOOKS")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, title, genre, status, notes FROM books ORDER BY id"
        ).fetchall()
    db.print_table(["ID", "Title", "Genre", "Status", "Notes"], rows)

    print("\n  1. Add notes to a book")
    print("  0. Back")
    choice = input("\n  Choice: ").strip()
    if choice == "1":
        book_id = db.prompt("Book ID")
        notes   = db.prompt("Notes")
        with db.connect() as conn:
            conn.execute("UPDATE books SET notes = ? WHERE id = ?", (notes, book_id))
        print("  Notes saved.")
    input("  Press Enter to continue...")


if __name__ == "__main__":
    db.init()
    main_menu()
