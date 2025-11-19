#!/usr/bin/env python3
"""
Add company_name column to reviews, insights, and clusters tables
Set all existing data to 'noom'
"""

import sqlite3
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def add_company_name_columns() -> None:
    """Add company_name column to all relevant tables"""

    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    tables_to_update = ["reviews", "insights", "clusters"]

    for table in tables_to_update:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col[1] for col in cursor.fetchall()]

        if 'company_name' in columns:
            print(f"✓ Table '{table}' already has 'company_name' column")
        else:
            print(f"Adding 'company_name' column to '{table}' table...")
            cursor.execute(f"""
                ALTER TABLE {table}
                ADD COLUMN company_name TEXT;
            """)
            conn.commit()
            print(f"✅ Column added to '{table}' table")

    # Update all existing data to 'noom'
    print("\n" + "="*60)
    print("SETTING EXISTING DATA TO 'noom'")
    print("="*60)

    for table in tables_to_update:
        # Count NULL entries
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE company_name IS NULL;")
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            print(f"\nUpdating {null_count:,} rows in '{table}' table...")
            cursor.execute(f"""
                UPDATE {table}
                SET company_name = 'noom'
                WHERE company_name IS NULL;
            """)
            conn.commit()
            print(f"✅ Updated {null_count:,} rows to company_name='noom'")
        else:
            print(f"\n✓ All rows in '{table}' already have company_name set")

    # Verify updates
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    for table in tables_to_update:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE company_name = 'noom';")
        noom_count = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        total_count = cursor.fetchone()[0]

        print(f"\n{table}:")
        print(f"  Total rows: {total_count:,}")
        print(f"  Noom rows: {noom_count:,}")

        if total_count == noom_count:
            print(f"  ✅ All rows set to 'noom'")
        else:
            print(f"  ⚠️  {total_count - noom_count} rows not set to 'noom'")

    # Show schema
    print("\n" + "="*60)
    print("UPDATED SCHEMA")
    print("="*60)

    for table in tables_to_update:
        print(f"\n{table} table:")
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            if 'company' in col[1].lower() or col[1] in ['id', 'review_id', 'cluster_id']:
                print(f"  {col[1]}: {col[2]}")

    conn.close()

    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    add_company_name_columns()
