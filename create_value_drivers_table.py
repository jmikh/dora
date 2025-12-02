#!/usr/bin/env python3
"""
Create value_drivers table for storing extracted value drivers
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"


def create_value_drivers_table():
    """Create value_drivers table and add value_drivers_processed columns"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("CREATING value_drivers TABLE")
        print("="*80)

        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='value_drivers'
        """)

        if cursor.fetchone():
            print("Table 'value_drivers' already exists")
        else:
            # Create the table
            print("\n1. Creating value_drivers table...")
            cursor.execute("""
                CREATE TABLE value_drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value_driver TEXT NOT NULL,
                    quote TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_table TEXT NOT NULL,
                    extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            print("2. Creating indexes...")

            cursor.execute("""
                CREATE INDEX idx_value_drivers_source
                ON value_drivers(source_id, source_table)
            """)
            print("   Index on source_id, source_table")

            cursor.execute("""
                CREATE INDEX idx_value_drivers_value_driver
                ON value_drivers(value_driver)
            """)
            print("   Index on value_driver")

            conn.commit()
            print("\n3. Table created successfully")

            # Show table schema
            cursor.execute("PRAGMA table_info(value_drivers)")
            columns = cursor.fetchall()
            print("\n   Table schema:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"     - {col_name} ({col_type}){not_null}{default}")

        # Add value_drivers_processed column to reddit_content if not exists
        print("\n4. Adding value_drivers_processed column to reddit_content...")

        cursor.execute("PRAGMA table_info(reddit_content)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'value_drivers_processed' in columns:
            print("   Column already exists in reddit_content")
        else:
            cursor.execute("""
                ALTER TABLE reddit_content
                ADD COLUMN value_drivers_processed BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("   Column added to reddit_content")

        # Add value_drivers_processed column to reviews if not exists
        print("\n5. Adding value_drivers_processed column to reviews...")

        cursor.execute("PRAGMA table_info(reviews)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'value_drivers_processed' in columns:
            print("   Column already exists in reviews")
        else:
            cursor.execute("""
                ALTER TABLE reviews
                ADD COLUMN value_drivers_processed BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("   Column added to reviews")

        print("\n" + "="*80)
        print("MIGRATION COMPLETE")
        print("="*80)

    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_value_drivers_table()
