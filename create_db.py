#!/usr/bin/env python3
"""
Script to create SQLite database and load Noom Play Store reviews from CSV
"""

import sqlite3
import pandas as pd
from pathlib import Path

# File paths
CSV_FILE = Path(__file__).parent / "noom_playstore_reviews.csv"
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"

def create_database():
    """Create SQLite database and load data from CSV"""

    print(f"Reading CSV file: {CSV_FILE}")
    # Read CSV file
    df = pd.read_csv(CSV_FILE)
    print(f"Loaded {len(df)} reviews from CSV")

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Create SQLite connection
    print(f"\nCreating SQLite database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)

    # Create table with appropriate schema
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id TEXT UNIQUE NOT NULL,
        user_name TEXT,
        rating INTEGER NOT NULL,
        helpful_votes INTEGER DEFAULT 0,
        date TIMESTAMP NOT NULL,
        review_text TEXT,
        reply_content TEXT,
        version TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    print("Creating 'reviews' table...")
    conn.execute(create_table_sql)

    # Create indexes for better query performance
    print("Creating indexes...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rating ON reviews(rating);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON reviews(date);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_helpful_votes ON reviews(helpful_votes);")

    # Insert data from DataFrame to SQLite
    print(f"\nInserting {len(df)} reviews into database...")
    df.to_sql('reviews', conn, if_exists='replace', index=False,
              dtype={
                  'review_id': 'TEXT',
                  'user_name': 'TEXT',
                  'rating': 'INTEGER',
                  'helpful_votes': 'INTEGER',
                  'date': 'TIMESTAMP',
                  'review_text': 'TEXT',
                  'reply_content': 'TEXT',
                  'version': 'TEXT'
              })

    # Commit changes
    conn.commit()

    # Verify data
    print("\n" + "="*50)
    print("DATABASE VERIFICATION")
    print("="*50)

    cursor = conn.cursor()

    # Count total rows
    cursor.execute("SELECT COUNT(*) FROM reviews")
    count = cursor.fetchone()[0]
    print(f"\nTotal reviews in database: {count:,}")

    # Rating distribution
    print("\nRating Distribution:")
    cursor.execute("""
        SELECT rating, COUNT(*) as count
        FROM reviews
        GROUP BY rating
        ORDER BY rating
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} stars: {row[1]:,} reviews")

    # Date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM reviews")
    min_date, max_date = cursor.fetchone()
    print(f"\nDate range: {min_date} to {max_date}")

    # Sample review
    print("\n" + "="*50)
    print("SAMPLE REVIEW")
    print("="*50)
    cursor.execute("""
        SELECT user_name, rating, date, review_text
        FROM reviews
        ORDER BY date DESC
        LIMIT 1
    """)
    sample = cursor.fetchone()
    if sample:
        print(f"User: {sample[0]}")
        print(f"Rating: {'⭐' * sample[1]}")
        print(f"Date: {sample[2]}")
        print(f"Review: {sample[3][:150]}...")

    # Close connection
    conn.close()

    print("\n" + "="*50)
    print("✅ Database created successfully!")
    print(f"Location: {DB_FILE.absolute()}")
    print("="*50)

if __name__ == "__main__":
    create_database()
