#!/usr/bin/env python3
"""
Add generated_insights boolean field to reviews table
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_generated_insights_field() -> None:
    """
    Add generated_insights field to reviews table and set to True for (wispr, appstore)
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("📊 Adding generated_insights field to reviews table...")
    print()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(reviews)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'generated_insights' in columns:
        print("⚠️  Column 'generated_insights' already exists!")
        print("   Updating values instead...")
    else:
        # Add generated_insights column (default False)
        print("➕ Adding 'generated_insights' column...")
        cursor.execute("""
            ALTER TABLE reviews
            ADD COLUMN generated_insights BOOLEAN DEFAULT 0;
        """)
        print("   ✅ Column added")

    print()
    print("🔄 Setting generated_insights=True for (wispr, appstore) reviews...")
    print()

    # Set generated_insights = True for wispr appstore reviews
    cursor.execute("""
        UPDATE reviews
        SET generated_insights = 1
        WHERE company_name = 'wispr' AND source = 'appstore';
    """)
    wispr_appstore_count = cursor.rowcount
    print(f"   ✅ Set generated_insights=True for {wispr_appstore_count:,} Wispr App Store reviews")

    # Commit changes
    conn.commit()
    print()
    print("💾 Changes committed to database")

    # Verify
    print()
    print("🔍 Verification:")
    cursor.execute("""
        SELECT company_name, source, generated_insights, COUNT(*) as count
        FROM reviews
        GROUP BY company_name, source, generated_insights
        ORDER BY company_name, source, generated_insights;
    """)

    results = cursor.fetchall()
    print()
    print("   Company    | Source       | Generated | Count")
    print("   " + "-" * 52)
    for company, source, generated, count in results:
        source_display = source if source else "(null)"
        generated_display = "True" if generated else "False"
        print(f"   {company:10} | {source_display:12} | {generated_display:9} | {count:,}")

    conn.close()

    print()
    print("=" * 60)
    print("✅ GENERATED_INSIGHTS FIELD ADDED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    add_generated_insights_field()
