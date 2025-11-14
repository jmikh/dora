#!/usr/bin/env python3
"""
Create the insights table in the SQLite database
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def create_insights_table() -> None:
    """Create the insights table with proper schema and indexes"""

    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)

    # Create insights table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id TEXT NOT NULL,
        insight_text TEXT NOT NULL,
        insight_type TEXT NOT NULL,
        review_date TIMESTAMP NOT NULL,
        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES reviews(review_id)
    );
    """

    print("Creating 'insights' table...")
    conn.execute(create_table_sql)

    # Create indexes for better query performance
    print("Creating indexes...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_review_id ON insights(review_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(insight_type);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_review_date ON insights(review_date);")

    # Commit changes
    conn.commit()

    # Verify table creation
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    cursor = conn.cursor()

    # Show table schema
    cursor.execute("PRAGMA table_info(insights);")
    columns = cursor.fetchall()

    print("\nTable schema:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    # Show indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='insights';")
    indexes = cursor.fetchall()

    print("\nIndexes:")
    for idx in indexes:
        print(f"  {idx[0]}")

    # Check existing data
    cursor.execute("SELECT COUNT(*) FROM insights")
    count = cursor.fetchone()[0]
    print(f"\nExisting insights: {count:,}")

    # Close connection
    conn.close()

    print("\n" + "="*60)
    print("✅ Insights table created successfully!")
    print("="*60)


if __name__ == "__main__":
    create_insights_table()
