#!/usr/bin/env python3
"""
Migrate clusters table to make insight_type nullable
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def migrate_clusters_table():
    """Make insight_type nullable in clusters table"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("MIGRATING clusters TABLE")
        print("="*80)

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='clusters'
        """)

        if not cursor.fetchone():
            print("✓ Table 'clusters' doesn't exist yet")
            return

        # Check current schema
        cursor.execute("PRAGMA table_info(clusters)")
        columns = cursor.fetchall()
        print("\n1. Current schema:")
        for col in columns:
            print(f"   {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")

        # Backup existing data
        print("\n2. Backing up existing data...")
        cursor.execute("SELECT COUNT(*) FROM clusters")
        count = cursor.fetchone()[0]
        print(f"   Found {count} existing clusters")

        if count > 0:
            cursor.execute("""
                CREATE TABLE clusters_backup AS
                SELECT * FROM clusters
            """)
            print("   ✓ Created backup table")

        # Drop old table
        print("\n3. Dropping old clusters table...")
        cursor.execute("DROP TABLE clusters")

        # Create new table with nullable insight_type
        print("\n4. Creating new clusters table...")
        cursor.execute("""
            CREATE TABLE clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                insight_type TEXT,
                embedding_type TEXT NOT NULL,
                n_components INTEGER,
                cluster_label TEXT,
                cluster_summary TEXT,
                size INTEGER NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
        print("   ✓ Table created")

        # Restore data if there was any
        if count > 0:
            print("\n5. Restoring data...")
            cursor.execute("""
                INSERT INTO clusters
                SELECT * FROM clusters_backup
            """)
            print(f"   ✓ Restored {count} clusters")

            # Drop backup table
            cursor.execute("DROP TABLE clusters_backup")
            print("   ✓ Dropped backup table")

        # Create indexes
        print("\n6. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_clusters_company
            ON clusters(company_name)
        """)
        print("   ✓ Index on company_name")

        cursor.execute("""
            CREATE INDEX idx_clusters_type
            ON clusters(insight_type)
        """)
        print("   ✓ Index on insight_type")

        cursor.execute("""
            CREATE INDEX idx_clusters_embedding
            ON clusters(embedding_type, n_components)
        """)
        print("   ✓ Index on (embedding_type, n_components)")

        conn.commit()

        # Verify new schema
        print("\n7. New schema:")
        cursor.execute("PRAGMA table_info(clusters)")
        columns = cursor.fetchall()
        for col in columns:
            not_null = " NOT NULL" if col[3] else ""
            print(f"   {col[1]} ({col[2]}){not_null}")

        print("\n" + "="*80)
        print("✓ Successfully migrated 'clusters' table")
        print("="*80)
        print("\nChanges:")
        print("- insight_type: NOT NULL → NULL (nullable)")
        print("- This allows clustering complaints without insight_type")

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    migrate_clusters_table()
