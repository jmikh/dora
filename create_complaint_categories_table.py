#!/usr/bin/env python3
"""
Create complaint_categories table for storing LLM-based categorizations
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def create_complaint_categories_table():
    """Create complaint_categories table"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("CREATING complaint_categories TABLE")
        print("="*80)

        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='complaint_categories'
        """)

        if cursor.fetchone():
            print("✓ Table 'complaint_categories' already exists")
            return

        # Create the table
        print("\n1. Creating complaint_categories table...")
        cursor.execute("""
            CREATE TABLE complaint_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT NOT NULL,
                classified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints(id),
                UNIQUE(complaint_id)
            )
        """)

        # Create indexes
        print("2. Creating indexes...")

        cursor.execute("""
            CREATE INDEX idx_complaint_categories_complaint_id
            ON complaint_categories(complaint_id)
        """)
        print("   ✓ Index on complaint_id")

        cursor.execute("""
            CREATE INDEX idx_complaint_categories_category
            ON complaint_categories(category)
        """)
        print("   ✓ Index on category")

        conn.commit()
        print("\n3. Verifying table creation...")

        # Verify the table was created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='complaint_categories'
        """)

        if cursor.fetchone():
            print("   ✓ Table exists in database")

            # Show table schema
            cursor.execute("PRAGMA table_info(complaint_categories)")
            columns = cursor.fetchall()
            print("\n4. Table schema:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"     - {col_name} ({col_type}){not_null}{default}")

            # Show indexes
            cursor.execute("PRAGMA index_list(complaint_categories)")
            indexes = cursor.fetchall()
            print("\n5. Indexes created:")
            for idx in indexes:
                print(f"     - {idx[1]} (unique: {bool(idx[2])})")

            # Show foreign keys
            cursor.execute("PRAGMA foreign_key_list(complaint_categories)")
            fkeys = cursor.fetchall()
            print("\n6. Foreign keys:")
            for fk in fkeys:
                print(f"     - complaint_id → {fk[2]}.{fk[4]}")

        else:
            print("   ✗ Error: Table was not created successfully")

        print("\n" + "="*80)
        print("✓ Successfully created 'complaint_categories' table")
        print("="*80)
        print("\nTable structure:")
        print("- Stores LLM-based categorizations of complaints")
        print("- One category per complaint (unique constraint)")
        print("- Includes confidence score and reasoning")
        print("- Foreign key to complaints table")

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_complaint_categories_table()
