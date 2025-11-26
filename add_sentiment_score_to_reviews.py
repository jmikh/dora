#!/usr/bin/env python3
"""
Add sentiment_score column to reviews table
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def add_sentiment_score_to_reviews():
    """Add sentiment_score column (nullable int) to reviews table"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("ADDING sentiment_score COLUMN TO reviews TABLE")
        print("="*80)

        # Check if column already exists
        print("\n1. Checking reviews table...")
        cursor.execute("PRAGMA table_info(reviews)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'sentiment_score' not in column_names:
            print("   Adding sentiment_score column to reviews...")
            cursor.execute("""
                ALTER TABLE reviews
                ADD COLUMN sentiment_score INTEGER
            """)

            # Count records
            cursor.execute("SELECT COUNT(*) FROM reviews")
            count = cursor.fetchone()[0]
            print(f"   ✓ Added sentiment_score column to {count} review records")
        else:
            print("   ✓ Column sentiment_score already exists in reviews")

        conn.commit()

        # Verify the column was added
        print("\n2. Verifying column...")
        cursor.execute("PRAGMA table_info(reviews)")
        columns = cursor.fetchall()
        sentiment_col = [col for col in columns if col[1] == 'sentiment_score']
        if sentiment_col:
            print(f"   ✓ reviews.sentiment_score: {sentiment_col[0][2]} (nullable: {not sentiment_col[0][3]})")

        # Sample data
        print("\n3. Sample data:")
        cursor.execute("SELECT review_id, rating, sentiment_score FROM reviews LIMIT 5")
        samples = cursor.fetchall()
        print("   Review samples (review_id, rating, sentiment_score):")
        for sample in samples:
            review_id_short = sample[0][:20] if len(sample[0]) > 20 else sample[0]
            print(f"     - {review_id_short}: rating={sample[1]}, sentiment_score={sample[2]}")

        print("\n" + "="*80)
        print("✓ Successfully added sentiment_score column to reviews table")
        print("="*80)
        print("\nNote: sentiment_score will be populated by AI extraction")
        print("      It may differ from the actual rating to test AI accuracy")

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    add_sentiment_score_to_reviews()
