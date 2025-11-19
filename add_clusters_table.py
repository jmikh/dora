#!/usr/bin/env python3
"""
Add clusters table and cluster_id column to insights table
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_clusters_schema() -> None:
    """Create clusters table and add cluster_id column to insights"""

    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if clusters table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='clusters';
    """)
    table_exists = cursor.fetchone() is not None

    if table_exists:
        print("✓ Table 'clusters' already exists")
    else:
        print("Creating 'clusters' table...")
        cursor.execute("""
            CREATE TABLE clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT NOT NULL,
                prompt_version INTEGER NOT NULL,
                embedding_type TEXT NOT NULL,
                n_components INTEGER,
                cluster_label TEXT,
                size INTEGER NOT NULL,
                created_at DATETIME NOT NULL
            );
        """)
        conn.commit()
        print("✅ Table 'clusters' created")

    # Check if cluster_id column exists in insights table
    cursor.execute("PRAGMA table_info(insights);")
    columns = [col[1] for col in cursor.fetchall()]

    if 'cluster_id' in columns:
        print("✓ Column 'cluster_id' already exists in insights table")
    else:
        print("Adding 'cluster_id' column to insights table...")
        cursor.execute("""
            ALTER TABLE insights
            ADD COLUMN cluster_id INTEGER;
        """)
        conn.commit()
        print("✅ Column 'cluster_id' added to insights table")

    # Show updated schema
    print("\n" + "="*60)
    print("UPDATED SCHEMA")
    print("="*60)

    print("\nClusters table:")
    cursor.execute("PRAGMA table_info(clusters);")
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]}")

    print("\nInsights table (cluster-related columns):")
    cursor.execute("PRAGMA table_info(insights);")
    for col in cursor.fetchall():
        if 'cluster' in col[1].lower() or col[1] in ['id', 'insight_type', 'prompt_version']:
            print(f"  {col[1]}: {col[2]}")

    conn.close()

    print("\n" + "="*60)
    print("✅ Schema migration complete!")
    print("="*60)


if __name__ == "__main__":
    add_clusters_schema()
