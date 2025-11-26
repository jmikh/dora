#!/usr/bin/env python3
"""
Create complaints table
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def create_complaints_table():
    """Create complaints table"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='complaints'
        """)

        if cursor.fetchone():
            print("✓ Table 'complaints' already exists")
            return

        # Create the table
        print("="*80)
        print("CREATING complaints TABLE")
        print("="*80)

        print("\n1. Creating complaints table...")
        cursor.execute("""
            CREATE TABLE complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint TEXT NOT NULL,
                quote TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better query performance
        print("2. Creating indexes...")

        cursor.execute("""
            CREATE INDEX idx_complaints_source
            ON complaints(source_id, source_table)
        """)
        print("   ✓ Index on (source_id, source_table)")

        cursor.execute("""
            CREATE INDEX idx_complaints_complaint
            ON complaints(complaint)
        """)
        print("   ✓ Index on complaint")

        cursor.execute("""
            CREATE INDEX idx_complaints_source_table
            ON complaints(source_table)
        """)
        print("   ✓ Index on source_table")

        conn.commit()
        print("\n3. Verifying table creation...")

        # Verify the table was created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='complaints'
        """)

        if cursor.fetchone():
            print("   ✓ Table exists in database")

            # Show table schema
            cursor.execute("PRAGMA table_info(complaints)")
            columns = cursor.fetchall()
            print("\n4. Table schema:")
            for col in columns:
                print(f"     - {col[1]} ({col[2]}){' NOT NULL' if col[3] else ''}")

            # Show indexes
            cursor.execute("PRAGMA index_list(complaints)")
            indexes = cursor.fetchall()
            print("\n5. Indexes created:")
            for idx in indexes:
                print(f"     - {idx[1]}")

        else:
            print("   ✗ Error: Table was not created successfully")

        print("\n" + "="*80)
        print("✓ Successfully created 'complaints' table")
        print("="*80)

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_complaints_table()
