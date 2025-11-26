#!/usr/bin/env python3
"""
Create complaint_embeddings table
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def create_complaint_embeddings_table():
    """Create complaint_embeddings table with foreign keys"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='complaint_embeddings'
        """)

        if cursor.fetchone():
            print("✓ Table 'complaint_embeddings' already exists")
            return

        # Create the table
        print("="*80)
        print("CREATING complaint_embeddings TABLE")
        print("="*80)

        print("\n1. Creating complaint_embeddings table...")
        cursor.execute("""
            CREATE TABLE complaint_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                complaint_text TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                embedding TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints(id)
            )
        """)

        # Create indexes
        print("2. Creating indexes...")

        cursor.execute("""
            CREATE INDEX idx_complaint_embeddings_complaint_id
            ON complaint_embeddings(complaint_id)
        """)
        print("   ✓ Index on complaint_id")

        cursor.execute("""
            CREATE INDEX idx_complaint_embeddings_dimensions
            ON complaint_embeddings(dimensions)
        """)
        print("   ✓ Index on dimensions")

        # Create unique constraint on (complaint_id, dimensions)
        cursor.execute("""
            CREATE UNIQUE INDEX idx_complaint_embeddings_unique
            ON complaint_embeddings(complaint_id, dimensions)
        """)
        print("   ✓ Unique index on (complaint_id, dimensions)")

        conn.commit()
        print("\n3. Verifying table creation...")

        # Verify the table was created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='complaint_embeddings'
        """)

        if cursor.fetchone():
            print("   ✓ Table exists in database")

            # Show table schema
            cursor.execute("PRAGMA table_info(complaint_embeddings)")
            columns = cursor.fetchall()
            print("\n4. Table schema:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"     - {col_name} ({col_type}){not_null}{default}")

            # Show indexes
            cursor.execute("PRAGMA index_list(complaint_embeddings)")
            indexes = cursor.fetchall()
            print("\n5. Indexes created:")
            for idx in indexes:
                print(f"     - {idx[1]} (unique: {bool(idx[2])})")

            # Show foreign keys
            cursor.execute("PRAGMA foreign_key_list(complaint_embeddings)")
            fkeys = cursor.fetchall()
            print("\n6. Foreign keys:")
            for fk in fkeys:
                print(f"     - complaint_id → {fk[2]}.{fk[4]}")

        else:
            print("   ✗ Error: Table was not created successfully")

        print("\n" + "="*80)
        print("✓ Successfully created 'complaint_embeddings' table")
        print("="*80)
        print("\nTable structure:")
        print("- Stores embeddings for complaints")
        print("- Multiple dimensions per complaint (1536, 50, 20)")
        print("- Unique constraint: (complaint_id, dimensions)")
        print("- Foreign key to complaints table")

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_complaint_embeddings_table()
