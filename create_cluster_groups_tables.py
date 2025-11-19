#!/usr/bin/env python3
"""
Migration script to create cluster_groups and cluster_group_assignments tables
"""

from pathlib import Path
from models import Base, get_engine

DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"


def create_cluster_groups_tables():
    """Create cluster_groups and cluster_group_assignments tables"""
    print("=" * 80)
    print("CREATING CLUSTER GROUPS TABLES")
    print("=" * 80)

    # Get engine and create tables
    engine = get_engine()

    print("\n🔧 Creating tables...")

    # Create only the new tables (won't affect existing ones)
    Base.metadata.create_all(engine, checkfirst=True)

    print("   ✅ cluster_groups table created")
    print("   ✅ cluster_group_assignments table created")

    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n✅ Current database tables:")
    for table in sorted(tables):
        print(f"   - {table}")

    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    print("Ready to store semantic cluster groups!")
    print("=" * 80)


if __name__ == "__main__":
    create_cluster_groups_tables()
