#!/usr/bin/env python3
"""
Create use_cases table for storing extracted use cases
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"


def create_use_cases_table():
    """Create use_cases table"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("CREATING use_cases TABLE")
        print("="*80)

        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='use_cases'
        """)

        if cursor.fetchone():
            print("✓ Table 'use_cases' already exists")
            return

        # Create the table
        print("\n1. Creating use_cases table...")
        cursor.execute("""
            CREATE TABLE use_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                use_case TEXT NOT NULL,
                quote TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        print("2. Creating indexes...")

        cursor.execute("""
            CREATE INDEX idx_use_cases_source
            ON use_cases(source_id, source_table)
        """)
        print("   ✓ Index on source_id, source_table")

        cursor.execute("""
            CREATE INDEX idx_use_cases_use_case
            ON use_cases(use_case)
        """)
        print("   ✓ Index on use_case")

        conn.commit()
        print("\n3. Verifying table creation...")

        # Verify the table was created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='use_cases'
        """)

        if cursor.fetchone():
            print("   ✓ Table exists in database")

            # Show table schema
            cursor.execute("PRAGMA table_info(use_cases)")
            columns = cursor.fetchall()
            print("\n4. Table schema:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"     - {col_name} ({col_type}){not_null}{default}")

            # Show indexes
            cursor.execute("PRAGMA index_list(use_cases)")
            indexes = cursor.fetchall()
            print("\n5. Indexes created:")
            for idx in indexes:
                print(f"     - {idx[1]} (unique: {bool(idx[2])})")

        else:
            print("   ✗ Error: Table was not created successfully")

        print("\n" + "="*80)
        print("✓ Successfully created 'use_cases' table")
        print("="*80)
        print("\nTable structure:")
        print("- Stores extracted use cases from Reddit and reviews")
        print("- Each use case is an atomic, singular action")
        print("- Links back to source content via source_id and source_table")

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_use_cases_table()
