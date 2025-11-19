#!/usr/bin/env python3
"""
Migration script to remove prompt_version columns from insights and clusters tables
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def remove_prompt_version_columns():
    """Remove prompt_version columns from insights and clusters tables"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("=" * 80)
    print("REMOVING PROMPT_VERSION COLUMNS FROM DATABASE")
    print("=" * 80)

    # Check if columns exist
    print("\n🔍 Checking current schema...")

    cursor.execute("PRAGMA table_info(insights)")
    insights_columns = {row[1]: row for row in cursor.fetchall()}

    cursor.execute("PRAGMA table_info(clusters)")
    clusters_columns = {row[1]: row for row in cursor.fetchall()}

    has_insights_pv = 'prompt_version' in insights_columns
    has_clusters_pv = 'prompt_version' in clusters_columns

    print(f"   insights.prompt_version exists: {has_insights_pv}")
    print(f"   clusters.prompt_version exists: {has_clusters_pv}")

    if not has_insights_pv and not has_clusters_pv:
        print("\n✅ No prompt_version columns found. Nothing to do!")
        conn.close()
        return

    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the tables
    # For insights table
    if has_insights_pv:
        print("\n🔧 Removing prompt_version from insights table...")

        # Create new table without prompt_version
        cursor.execute("""
            CREATE TABLE insights_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT NOT NULL,
                company_name TEXT NOT NULL,
                insight_text TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                review_date DATETIME NOT NULL,
                extracted_at DATETIME NOT NULL,
                embedding TEXT,
                cluster_id INTEGER,
                FOREIGN KEY (review_id) REFERENCES reviews(review_id),
                FOREIGN KEY (cluster_id) REFERENCES clusters(id)
            )
        """)

        # Copy data (excluding prompt_version)
        cursor.execute("""
            INSERT INTO insights_new
            (id, review_id, company_name, insight_text, insight_type, review_date,
             extracted_at, embedding, cluster_id)
            SELECT id, review_id, company_name, insight_text, insight_type, review_date,
                   extracted_at, embedding, cluster_id
            FROM insights
        """)

        # Drop old table and rename new one
        cursor.execute("DROP TABLE insights")
        cursor.execute("ALTER TABLE insights_new RENAME TO insights")

        print("   ✅ Removed prompt_version from insights table")

    # For clusters table
    if has_clusters_pv:
        print("\n🔧 Removing prompt_version from clusters table...")

        # Create new table without prompt_version
        cursor.execute("""
            CREATE TABLE clusters_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                embedding_type TEXT NOT NULL,
                n_components INTEGER,
                cluster_label TEXT,
                cluster_summary TEXT,
                size INTEGER NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)

        # Copy data (excluding prompt_version)
        cursor.execute("""
            INSERT INTO clusters_new
            (id, company_name, insight_type, embedding_type, n_components,
             cluster_label, cluster_summary, size, created_at)
            SELECT id, company_name, insight_type, embedding_type, n_components,
                   cluster_label, cluster_summary, size, created_at
            FROM clusters
        """)

        # Drop old table and rename new one
        cursor.execute("DROP TABLE clusters")
        cursor.execute("ALTER TABLE clusters_new RENAME TO clusters")

        print("   ✅ Removed prompt_version from clusters table")

    # Commit changes
    conn.commit()

    # Verify final schema
    print("\n📊 Verifying new schema...")

    cursor.execute("PRAGMA table_info(insights)")
    insights_columns_new = [row[1] for row in cursor.fetchall()]
    print(f"   insights columns: {', '.join(insights_columns_new)}")

    cursor.execute("PRAGMA table_info(clusters)")
    clusters_columns_new = [row[1] for row in cursor.fetchall()]
    print(f"   clusters columns: {', '.join(clusters_columns_new)}")

    # Close connection
    conn.close()

    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    print("prompt_version columns have been removed from insights and clusters tables")
    print("All data has been preserved")
    print("=" * 80)


if __name__ == "__main__":
    import sys

    print("⚠️  WARNING: This will modify the database schema!")
    print("   This migration will remove prompt_version columns from:")
    print("   - insights table")
    print("   - clusters table")
    print()

    response = input("Continue? [y/N]: ")

    if response.lower() != 'y':
        print("❌ Migration cancelled")
        sys.exit(0)

    remove_prompt_version_columns()
