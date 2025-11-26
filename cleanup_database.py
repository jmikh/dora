#!/usr/bin/env python3
"""
Clean up database:
1. Drop insights table
2. Delete reviews where company_name != 'wispr'
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path(__file__).parent / "dora.db"

def cleanup_database():
    """Drop insights table and clean up non-Wispr reviews"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("="*80)
        print("DATABASE CLEANUP")
        print("="*80)

        # 1. Check insights table
        print("\n1. Checking insights table...")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='insights'
        """)

        if cursor.fetchone():
            # Count rows before dropping
            cursor.execute("SELECT COUNT(*) FROM insights")
            count = cursor.fetchone()[0]
            print(f"   Found insights table with {count} rows")

            # Drop the table
            print("   Dropping insights table...")
            cursor.execute("DROP TABLE insights")
            print("   ✓ Insights table dropped")
        else:
            print("   ℹ Insights table does not exist (already dropped)")

        # 2. Clean up reviews
        print("\n2. Cleaning up reviews table...")

        # Count reviews by company
        cursor.execute("""
            SELECT company_name, COUNT(*)
            FROM reviews
            GROUP BY company_name
        """)

        company_counts = cursor.fetchall()
        print("   Current reviews by company:")
        for company, count in company_counts:
            print(f"     - {company}: {count} reviews")

        # Count non-Wispr reviews
        cursor.execute("""
            SELECT COUNT(*)
            FROM reviews
            WHERE company_name != 'wispr'
        """)

        non_wispr_count = cursor.fetchone()[0]

        if non_wispr_count > 0:
            print(f"\n   Deleting {non_wispr_count} non-Wispr reviews...")
            cursor.execute("""
                DELETE FROM reviews
                WHERE company_name != 'wispr'
            """)
            print(f"   ✓ Deleted {non_wispr_count} reviews")
        else:
            print("   ℹ No non-Wispr reviews to delete")

        # Verify final state
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE company_name = 'wispr'")
        wispr_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_count = cursor.fetchone()[0]

        print("\n3. Final state:")
        print(f"   Total reviews: {total_count}")
        print(f"   Wispr reviews: {wispr_count}")
        print(f"   Non-Wispr reviews: {total_count - wispr_count}")

        # Commit changes
        conn.commit()
        print("\n✓ Database cleanup completed successfully")

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    cleanup_database()
