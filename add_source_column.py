#!/usr/bin/env python3
"""
Add source column to reviews table and populate it based on company
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_source_column() -> None:
    """
    Add source column to reviews table and populate based on company
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("📊 Adding source column to reviews table...")
    print()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(reviews)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'source' in columns:
        print("⚠️  Column 'source' already exists!")
        print("   Updating values instead...")
    else:
        # Add source column
        print("➕ Adding 'source' column...")
        cursor.execute("""
            ALTER TABLE reviews
            ADD COLUMN source TEXT;
        """)
        print("   ✅ Column added")

    print()
    print("🔄 Updating source values based on company...")
    print()

    # Set source = 'playstore' for noom
    cursor.execute("""
        UPDATE reviews
        SET source = 'playstore'
        WHERE company_name = 'noom';
    """)
    noom_count = cursor.rowcount
    print(f"   ✅ Set source='playstore' for {noom_count:,} Noom reviews")

    # Set source = 'appstore' for wispr
    cursor.execute("""
        UPDATE reviews
        SET source = 'appstore'
        WHERE company_name = 'wispr';
    """)
    wispr_count = cursor.rowcount
    print(f"   ✅ Set source='appstore' for {wispr_count:,} Wispr reviews")

    # Commit changes
    conn.commit()
    print()
    print("💾 Changes committed to database")

    # Verify
    print()
    print("🔍 Verification:")
    cursor.execute("""
        SELECT company_name, source, COUNT(*) as count
        FROM reviews
        GROUP BY company_name, source
        ORDER BY company_name, source;
    """)

    results = cursor.fetchall()
    print()
    print("   Company    | Source     | Count")
    print("   " + "-" * 38)
    for company, source, count in results:
        source_display = source if source else "(null)"
        print(f"   {company:10} | {source_display:10} | {count:,}")

    conn.close()

    print()
    print("=" * 60)
    print("✅ SOURCE COLUMN ADDED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    add_source_column()
