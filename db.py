"""Database connection, schema, and seed data."""
import sqlite3
import os
from datetime import date, timedelta

_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "author_os.db")
DB_PATH = os.environ.get('AUTHOR_OS_DB', _default_db)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init():
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                genre      TEXT DEFAULT 'Horror/Thriller',
                status     TEXT DEFAULT 'Published',
                notes      TEXT,
                created_at TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS agents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                agency        TEXT,
                email         TEXT,
                website       TEXT,
                genres        TEXT,
                status        TEXT DEFAULT 'Wishlist',
                query_date    TEXT,
                response_date TEXT,
                notes         TEXT,
                created_at    TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                type           TEXT NOT NULL,
                title          TEXT NOT NULL,
                publisher      TEXT,
                deadline       TEXT,
                pay            TEXT,
                status         TEXT DEFAULT 'Open',
                submitted_date TEXT,
                response_date  TEXT,
                book_id        INTEGER REFERENCES books(id),
                notes          TEXT,
                created_at     TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS calendar (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_date TEXT NOT NULL,
                platform       TEXT NOT NULL,
                content_type   TEXT NOT NULL,
                title          TEXT NOT NULL,
                body           TEXT,
                status         TEXT DEFAULT 'Planned',
                published_date TEXT,
                notes          TEXT,
                created_at     TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS weekly_log (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start         TEXT NOT NULL UNIQUE,
                words_written      INTEGER DEFAULT 0,
                queries_sent       INTEGER DEFAULT 0,
                submissions_sent   INTEGER DEFAULT 0,
                responses_received INTEGER DEFAULT 0,
                acceptances        INTEGER DEFAULT 0,
                rejections         INTEGER DEFAULT 0,
                notes              TEXT,
                created_at         TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS prospects (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                type                TEXT NOT NULL
                                    CHECK(type IN ('podcast','agent','publisher','festival','reviewer','blogger')),
                name                TEXT NOT NULL,
                url                 TEXT,
                contact_name        TEXT,
                contact_email       TEXT,
                status              TEXT NOT NULL DEFAULT 'new'
                                    CHECK(status IN ('new','contacted','responded','accepted','rejected','archived')),
                notes               TEXT,

                -- Scoring: five criteria rated 0-4 each. Score = sum * 5 (max 100).
                audience_relevance  INTEGER NOT NULL DEFAULT 0 CHECK(audience_relevance  BETWEEN 0 AND 4),
                genre_fit           INTEGER NOT NULL DEFAULT 0 CHECK(genre_fit           BETWEEN 0 AND 4),
                accessibility       INTEGER NOT NULL DEFAULT 0 CHECK(accessibility       BETWEEN 0 AND 4),
                potential_reach     INTEGER NOT NULL DEFAULT 0 CHECK(potential_reach     BETWEEN 0 AND 4),
                publishing_value    INTEGER NOT NULL DEFAULT 0 CHECK(publishing_value    BETWEEN 0 AND 4),
                score               INTEGER NOT NULL DEFAULT 0,

                -- Type-specific optional fields
                genre_focus         TEXT,
                accepts_queries     INTEGER,
                submission_deadline TEXT,

                discovered_date     TEXT NOT NULL DEFAULT (date('now')),
                created_at          TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_prospects_type   ON prospects(type);
            CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
            CREATE INDEX IF NOT EXISTS idx_prospects_score  ON prospects(score DESC);
        """)

        if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO books (title, genre, status) VALUES (?, ?, ?)",
                [
                    ("Caught in Cryptic", "Horror/Thriller", "Published"),
                    ("Falling Cryptic",   "Horror/Thriller", "Published"),
                    ("Nighty Night Dear", "Horror/Thriller", "Published"),
                ],
            )


def current_week_start():
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


def print_table(headers, rows):
    if not rows:
        print("  (no records found)")
        return
    rows = [tuple(r) for r in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val) if val is not None else ""))
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(v) if v is not None else "" for v in row]))
    print(sep)


def prompt(label, default=None):
    suffix = f" [{default}]" if default is not None else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val if val else (default or "")


def prompt_int(label, default=0):
    suffix = f" [{default}]"
    val = input(f"  {label}{suffix}: ").strip()
    try:
        return int(val) if val else default
    except ValueError:
        return default


def choose(label, options):
    print(f"\n  {label}:")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    val = input("  Choice: ").strip()
    try:
        idx = int(val) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return options[0]


def header(title):
    width = 50
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)
