#!/usr/bin/env python3
"""
Migration script to add polymorphic source fields to insights table

Adds:
- source_type (TEXT, default 'review')
- source_id (TEXT)

Updates existing insights to have source_type='review' and source_id=review_id
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_polymorphic_source_columns():
    """Add source_type and source_id columns to insights table"""
    print("=" * 80)
    print("ADDING POLYMORPHIC SOURCE COLUMNS TO INSIGHTS TABLE")
    print("=" * 80)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check current schema
    print("\n🔍 Current insights table schema:")
    cursor.execute("PRAGMA table_info(insights)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    # Check if columns already exist
    if 'source_type' in column_names and 'source_id' in column_names:
        print("\n✅ Columns already exist! Nothing to do.")
        conn.close()
        return

    # Get count of existing insights
    cursor.execute("SELECT COUNT(*) FROM insights")
    total_insights = cursor.fetchone()[0]
    print(f"\n📊 Found {total_insights} existing insights")

    # SQLite doesn't support adding columns with NOT NULL and no default easily
    # So we'll recreate the table
    print("\n🔧 Recreating insights table with new columns...")

    # Create new table with updated schema
    cursor.execute("""
        CREATE TABLE insights_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT,
            company_name TEXT NOT NULL,
            insight_text TEXT NOT NULL,
            insight_type TEXT NOT NULL,
            review_date DATETIME NOT NULL,
            extracted_at DATETIME NOT NULL,
            embedding TEXT,
            cluster_id INTEGER,
            source_type TEXT NOT NULL DEFAULT 'review',
            source_id TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (review_id) REFERENCES reviews(review_id),
            FOREIGN KEY (cluster_id) REFERENCES clusters(id)
        )
    """)

    # Copy data from old table, setting source_type='review' and source_id=review_id
    print("📋 Migrating existing insights...")
    cursor.execute("""
        INSERT INTO insights_new (
            id, review_id, company_name, insight_text, insight_type,
            review_date, extracted_at, embedding, cluster_id,
            source_type, source_id
        )
        SELECT
            id, review_id, company_name, insight_text, insight_type,
            review_date, extracted_at, embedding, cluster_id,
            'review' as source_type,
            review_id as source_id
        FROM insights
    """)

    migrated = cursor.rowcount
    print(f"   ✅ Migrated {migrated} insights")

    # Drop old table and rename new one
    print("🔄 Replacing old table...")
    cursor.execute("DROP TABLE insights")
    cursor.execute("ALTER TABLE insights_new RENAME TO insights")

    # Commit changes
    conn.commit()

    # Verify new schema
    print("\n✅ New insights table schema:")
    cursor.execute("PRAGMA table_info(insights)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    # Verify data
    cursor.execute("""
        SELECT source_type, COUNT(*) as count
        FROM insights
        GROUP BY source_type
    """)
    print("\n📊 Insights by source type:")
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]} insights")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    print(f"Total insights migrated: {migrated}")
    print("All existing insights now have source_type='review'")
    print("Ready to extract insights from YouTube videos!")
    print("=" * 80)


if __name__ == "__main__":
    add_polymorphic_source_columns()
