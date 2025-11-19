#!/usr/bin/env python3
"""
Migration script to add company_name column to youtube_videos table
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_company_name_column():
    """Add company_name column to youtube_videos table and populate with 'wispr'"""
    print("=" * 80)
    print("ADDING COMPANY_NAME COLUMN TO YOUTUBE_VIDEOS TABLE")
    print("=" * 80)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check current schema
    print("\n🔍 Current youtube_videos table schema:")
    cursor.execute("PRAGMA table_info(youtube_videos)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    # Check if column already exists
    if 'company_name' in column_names:
        print("\n✅ company_name column already exists! Nothing to do.")
        conn.close()
        return

    # Get count of existing videos
    cursor.execute("SELECT COUNT(*) FROM youtube_videos")
    total_videos = cursor.fetchone()[0]
    print(f"\n📊 Found {total_videos} existing YouTube videos")

    # Add company_name column with default value
    print("\n🔧 Adding company_name column...")
    cursor.execute("""
        ALTER TABLE youtube_videos
        ADD COLUMN company_name TEXT NOT NULL DEFAULT 'wispr'
    """)

    # Verify all rows have the default value
    cursor.execute("SELECT COUNT(*) FROM youtube_videos WHERE company_name = 'wispr'")
    count_with_wispr = cursor.fetchone()[0]

    print(f"   ✅ Added company_name column")
    print(f"   ✅ Set company_name='wispr' for {count_with_wispr} videos")

    # Commit changes
    conn.commit()

    # Verify new schema
    print("\n✅ New youtube_videos table schema:")
    cursor.execute("PRAGMA table_info(youtube_videos)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    print(f"All {total_videos} YouTube videos now have company_name='wispr'")
    print("=" * 80)


if __name__ == "__main__":
    add_company_name_column()
