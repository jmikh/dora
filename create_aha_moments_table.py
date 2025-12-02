#!/usr/bin/env python3
"""
Create aha_moments table for storing extracted aha moments from YouTube videos
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"


def create_aha_moments_table():
    """Create aha_moments table and add aha_processed column to youtube_videos"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("CREATING aha_moments TABLE")
        print("="*80)

        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='aha_moments'
        """)

        if cursor.fetchone():
            print("Table 'aha_moments' already exists")
        else:
            # Create the table
            print("\n1. Creating aha_moments table...")
            cursor.execute("""
                CREATE TABLE aha_moments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    quote TEXT NOT NULL,
                    insight TEXT NOT NULL,
                    extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES youtube_videos(id)
                )
            """)

            # Create indexes
            print("2. Creating indexes...")

            cursor.execute("""
                CREATE INDEX idx_aha_moments_video_id
                ON aha_moments(video_id)
            """)
            print("   Index on video_id")

            conn.commit()
            print("\n3. Table created successfully")

            # Show table schema
            cursor.execute("PRAGMA table_info(aha_moments)")
            columns = cursor.fetchall()
            print("\n   Table schema:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"     - {col_name} ({col_type}){not_null}{default}")

        # Add aha_processed column to youtube_videos if not exists
        print("\n4. Adding aha_processed column to youtube_videos...")

        cursor.execute("PRAGMA table_info(youtube_videos)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'aha_processed' in columns:
            print("   Column 'aha_processed' already exists")
        else:
            cursor.execute("""
                ALTER TABLE youtube_videos
                ADD COLUMN aha_processed BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("   Column 'aha_processed' added")

        print("\n" + "="*80)
        print("MIGRATION COMPLETE")
        print("="*80)

    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    create_aha_moments_table()
