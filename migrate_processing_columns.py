#!/usr/bin/env python3
"""
Migrate ai_processed column to separate complaints_processed and use_cases_processed columns

This script:
1. Adds complaints_processed and use_cases_processed columns to reddit_content and reviews tables
2. Sets complaints_processed=True where ai_processed=True (migrating existing data)
3. Drops the old ai_processed column
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "dora.db"


def migrate_processing_columns():
    """Migrate from ai_processed to separate processing columns"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("=" * 80)
        print("MIGRATING PROCESSING COLUMNS")
        print("=" * 80)

        # 1. Add new columns to reddit_content
        print("\n1. Adding new columns to reddit_content...")
        try:
            cursor.execute("""
                ALTER TABLE reddit_content
                ADD COLUMN complaints_processed BOOLEAN DEFAULT FALSE
            """)
            print("   ✓ Added complaints_processed column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠ complaints_processed column already exists")
            else:
                raise

        try:
            cursor.execute("""
                ALTER TABLE reddit_content
                ADD COLUMN use_cases_processed BOOLEAN DEFAULT FALSE
            """)
            print("   ✓ Added use_cases_processed column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠ use_cases_processed column already exists")
            else:
                raise

        # 2. Add new columns to reviews
        print("\n2. Adding new columns to reviews...")
        try:
            cursor.execute("""
                ALTER TABLE reviews
                ADD COLUMN complaints_processed BOOLEAN DEFAULT FALSE
            """)
            print("   ✓ Added complaints_processed column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠ complaints_processed column already exists")
            else:
                raise

        try:
            cursor.execute("""
                ALTER TABLE reviews
                ADD COLUMN use_cases_processed BOOLEAN DEFAULT FALSE
            """)
            print("   ✓ Added use_cases_processed column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠ use_cases_processed column already exists")
            else:
                raise

        # 3. Migrate existing data (reddit_content)
        print("\n3. Migrating existing reddit_content data...")
        cursor.execute("""
            UPDATE reddit_content
            SET complaints_processed = TRUE
            WHERE ai_processed = TRUE
        """)
        reddit_migrated = cursor.rowcount
        print(f"   ✓ Set complaints_processed=TRUE for {reddit_migrated} reddit records")

        # 4. Migrate existing data (reviews)
        print("\n4. Migrating existing reviews data...")
        cursor.execute("""
            UPDATE reviews
            SET complaints_processed = TRUE
            WHERE ai_processed = TRUE
        """)
        reviews_migrated = cursor.rowcount
        print(f"   ✓ Set complaints_processed=TRUE for {reviews_migrated} review records")

        # 5. Drop old columns (SQLite doesn't support DROP COLUMN easily, so we'll note this)
        print("\n5. Note about ai_processed column:")
        print("   ⚠ SQLite doesn't support DROP COLUMN easily")
        print("   ⚠ The ai_processed column will remain but should not be used")
        print("   ⚠ Update your code to use complaints_processed and use_cases_processed instead")

        conn.commit()

        print("\n" + "=" * 80)
        print("✓ MIGRATION COMPLETE")
        print("=" * 80)
        print(f"Migrated {reddit_migrated} reddit records")
        print(f"Migrated {reviews_migrated} review records")
        print("\nNext steps:")
        print("1. Update models.py to use new columns")
        print("2. Update extraction scripts to set the appropriate processing flags")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_processing_columns()
