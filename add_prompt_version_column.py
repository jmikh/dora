#!/usr/bin/env python3
"""
Add prompt_version column to insights table and set existing entries to version 1
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_prompt_version_column() -> None:
    """Add prompt_version column and set existing entries to 1"""

    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(insights);")
    columns = [col[1] for col in cursor.fetchall()]

    if 'prompt_version' in columns:
        print("✅ Column 'prompt_version' already exists")
        conn.close()
        return

    # Add prompt_version column
    print("Adding 'prompt_version' column...")
    cursor.execute("""
        ALTER TABLE insights
        ADD COLUMN prompt_version INTEGER DEFAULT 1;
    """)

    # Update existing entries to version 1
    print("Setting existing entries to version 1...")
    cursor.execute("""
        UPDATE insights
        SET prompt_version = 1
        WHERE prompt_version IS NULL;
    """)

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM insights WHERE prompt_version = 1")
    count = cursor.fetchone()[0]

    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    print(f"Entries with prompt_version = 1: {count:,}")

    # Show updated schema
    cursor.execute("PRAGMA table_info(insights);")
    columns = cursor.fetchall()

    print("\nUpdated table schema:")
    for col in columns:
        if col[1] == 'prompt_version':
            print(f"  {col[1]}: {col[2]} (NEW)")
        else:
            print(f"  {col[1]}: {col[2]}")

    conn.close()

    print("\n" + "="*60)
    print("✅ Column added and existing entries updated!")
    print("="*60)


if __name__ == "__main__":
    add_prompt_version_column()
