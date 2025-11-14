#!/usr/bin/env python3
"""
Add embeddings column to insights table
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_embeddings_column() -> None:
    """Add embeddings column to insights table"""

    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(insights);")
    columns = [col[1] for col in cursor.fetchall()]

    if 'embedding' in columns:
        print("✅ Embeddings column already exists")
        conn.close()
        return

    # Add embeddings column (stored as JSON string)
    print("Adding embeddings column to insights table...")
    cursor.execute("""
        ALTER TABLE insights
        ADD COLUMN embedding TEXT;
    """)

    conn.commit()

    # Verify
    cursor.execute("PRAGMA table_info(insights);")
    columns = cursor.fetchall()

    print("\n" + "="*60)
    print("UPDATED TABLE SCHEMA")
    print("="*60)
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    conn.close()

    print("\n" + "="*60)
    print("✅ Embeddings column added successfully!")
    print("="*60)


if __name__ == "__main__":
    add_embeddings_column()
