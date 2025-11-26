#!/usr/bin/env python3
"""
Create competitor_mentions table
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def create_competitor_mentions_table():
    """Create competitor_mentions table"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='competitor_mentions'
        """)

        if cursor.fetchone():
            print("✓ Table 'competitor_mentions' already exists")
            return

        # Create the table
        print("Creating 'competitor_mentions' table...")
        cursor.execute("""
            CREATE TABLE competitor_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                content_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better query performance
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_competitor_mentions_competitor
            ON competitor_mentions(competitor_name)
        """)

        cursor.execute("""
            CREATE INDEX idx_competitor_mentions_content
            ON competitor_mentions(content_id, source_table)
        """)

        cursor.execute("""
            CREATE INDEX idx_competitor_mentions_source
            ON competitor_mentions(source_table)
        """)

        conn.commit()
        print("✓ Successfully created 'competitor_mentions' table")
        print("✓ Created indexes for better query performance")

        # Verify the table was created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='competitor_mentions'
        """)

        if cursor.fetchone():
            print("✓ Verified: Table exists in database")

            # Show table schema
            cursor.execute("PRAGMA table_info(competitor_mentions)")
            columns = cursor.fetchall()
            print("\nTable schema:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}){' NOT NULL' if col[3] else ''}")
        else:
            print("✗ Error: Table was not created successfully")

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_competitor_mentions_table()
