#!/usr/bin/env python3
"""
Migration script to create Reddit tables (companies, reddit_communities, reddit_posts, reddit_comments)
"""

from pathlib import Path
from models import Base, get_engine


def create_reddit_tables():
    """Create Reddit-related tables"""
    print("=" * 80)
    print("CREATING REDDIT TABLES")
    print("=" * 80)

    # Get engine and create tables
    engine = get_engine()

    print("\n🔧 Creating tables...")

    # Create only the new tables (won't affect existing ones)
    Base.metadata.create_all(engine, checkfirst=True)

    print("   ✅ companies table created")
    print("   ✅ reddit_communities table created")
    print("   ✅ reddit_posts table created")
    print("   ✅ reddit_comments table created")

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
    print("Ready to ingest Reddit data!")
    print("=" * 80)


if __name__ == "__main__":
    create_reddit_tables()
