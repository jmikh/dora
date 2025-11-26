#!/usr/bin/env python3
"""
Add ai_processed column to reddit_content and reviews tables
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def add_ai_processed_column():
    """Add ai_processed boolean column (default false) to reddit_content and reviews tables"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("ADDING ai_processed COLUMN")
        print("="*80)

        # 1. Add to reddit_content table
        print("\n1. Checking reddit_content table...")
        cursor.execute("PRAGMA table_info(reddit_content)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'ai_processed' not in column_names:
            print("   Adding ai_processed column to reddit_content...")
            cursor.execute("""
                ALTER TABLE reddit_content
                ADD COLUMN ai_processed BOOLEAN DEFAULT 0
            """)

            # Count records
            cursor.execute("SELECT COUNT(*) FROM reddit_content")
            count = cursor.fetchone()[0]
            print(f"   ✓ Added ai_processed column to {count} reddit_content records")
        else:
            print("   ✓ Column ai_processed already exists in reddit_content")

        # 2. Add to reviews table
        print("\n2. Checking reviews table...")
        cursor.execute("PRAGMA table_info(reviews)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'ai_processed' not in column_names:
            print("   Adding ai_processed column to reviews...")
            cursor.execute("""
                ALTER TABLE reviews
                ADD COLUMN ai_processed BOOLEAN DEFAULT 0
            """)

            # Count records
            cursor.execute("SELECT COUNT(*) FROM reviews")
            count = cursor.fetchone()[0]
            print(f"   ✓ Added ai_processed column to {count} review records")
        else:
            print("   ✓ Column ai_processed already exists in reviews")

        conn.commit()

        # 3. Verify the columns were added
        print("\n3. Verifying columns...")

        # Verify reddit_content
        cursor.execute("PRAGMA table_info(reddit_content)")
        columns = cursor.fetchall()
        ai_processed_col = [col for col in columns if col[1] == 'ai_processed']
        if ai_processed_col:
            print(f"   ✓ reddit_content.ai_processed: {ai_processed_col[0][2]} (default: {ai_processed_col[0][4]})")

        # Verify reviews
        cursor.execute("PRAGMA table_info(reviews)")
        columns = cursor.fetchall()
        ai_processed_col = [col for col in columns if col[1] == 'ai_processed']
        if ai_processed_col:
            print(f"   ✓ reviews.ai_processed: {ai_processed_col[0][2]} (default: {ai_processed_col[0][4]})")

        # 4. Sample data
        print("\n4. Sample data:")

        cursor.execute("SELECT id, ai_processed FROM reddit_content LIMIT 3")
        reddit_samples = cursor.fetchall()
        print("   reddit_content samples:")
        for sample in reddit_samples:
            print(f"     - {sample[0]}: ai_processed={sample[1]}")

        cursor.execute("SELECT review_id, ai_processed FROM reviews LIMIT 3")
        review_samples = cursor.fetchall()
        print("   reviews samples:")
        for sample in review_samples:
            print(f"     - {sample[0][:20]}...: ai_processed={sample[1]}")

        print("\n" + "="*80)
        print("✓ Successfully added ai_processed column to both tables")
        print("="*80)

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    add_ai_processed_column()
