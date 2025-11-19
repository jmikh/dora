#!/usr/bin/env python3
"""
Ingest Wispr App Store reviews from CSV into database
"""

import csv
from datetime import datetime
from typing import Optional
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Review, get_session


def parse_appstore_date(date_str: str) -> datetime:
    """
    Parse Apple App Store ISO 8601 date format

    Args:
        date_str: Date string like "2025-11-14T21:09:45-07:00"

    Returns:
        datetime object
    """
    # Remove timezone suffix for simpler parsing
    # Format: "2025-11-14T21:09:45-07:00" -> "2025-11-14T21:09:45"
    if '+' in date_str or date_str.count('-') > 2:
        # Find the last occurrence of + or - (timezone indicator)
        for tz_char in ['+', '-']:
            if tz_char in date_str[-6:]:  # Check last 6 chars for timezone
                date_str = date_str.rsplit(tz_char, 1)[0]
                break

    return datetime.fromisoformat(date_str)


def ingest_wispr_csv(
    csv_file: str,
    company_name: str = "wispr",
    dry_run: bool = False
) -> None:
    """
    Ingest Wispr App Store reviews from CSV file

    Args:
        csv_file: Path to CSV file
        company_name: Company name to use (default: wispr)
        dry_run: If True, don't actually insert records
    """
    csv_path = Path(csv_file)

    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return

    print(f"📄 Reading CSV: {csv_file}")
    print(f"🏢 Company: {company_name}")
    print(f"🔍 Dry run: {dry_run}")
    print()

    # Create database session
    session = get_session()

    # Track statistics
    total_rows = 0
    inserted = 0
    duplicates = 0
    errors = 0

    # Read CSV file
    with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1

            try:
                # Extract fields from CSV
                review_id = row['id']
                user_name = row['userName']
                rating = int(row['score'])  # App Store uses 'score' not 'rating'
                date_str = row['date']
                version = row['version']

                # App Store has separate 'title' and 'text' columns
                # Combine them for review_text
                title = row.get('title', '').strip()
                text = row.get('text', '').strip()

                if title and text:
                    review_text = f"{title}\n\n{text}"
                elif title:
                    review_text = title
                else:
                    review_text = text

                # Parse date
                review_date = parse_appstore_date(date_str)

                # Check if review already exists
                existing = session.execute(
                    select(Review).where(Review.review_id == review_id)
                ).scalar_one_or_none()

                if existing:
                    duplicates += 1
                    if total_rows <= 5 or total_rows % 100 == 0:
                        print(f"⏭️  [{total_rows}] Duplicate: {review_id[:12]}...")
                    continue

                # Create Review object
                review = Review(
                    review_id=review_id,
                    company_name=company_name,
                    user_name=user_name,
                    rating=rating,
                    helpful_votes=0,  # App Store CSV doesn't have this
                    date=review_date,
                    review_text=review_text,
                    reply_content=None,  # App Store CSV doesn't have this
                    version=version
                )

                if not dry_run:
                    session.add(review)
                    inserted += 1
                else:
                    inserted += 1  # Count what would be inserted

                # Show progress for first few and every 100 rows
                if total_rows <= 5 or total_rows % 100 == 0:
                    stars = '⭐' * rating
                    print(f"✅ [{total_rows}] {stars} - {user_name[:20]}")
                    print(f"   {review_text[:60]}...")

            except Exception as e:
                errors += 1
                print(f"❌ [{total_rows}] Error processing row: {e}")
                print(f"   Row: {row}")
                continue

    # Commit changes if not dry run
    if not dry_run:
        session.commit()
        print(f"\n💾 Changes committed to database")
    else:
        print(f"\n🔍 DRY RUN - No changes made to database")

    session.close()

    # Print summary
    print()
    print("=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"Total rows processed: {total_rows}")
    print(f"Successfully inserted: {inserted}")
    print(f"Duplicates skipped: {duplicates}")
    print(f"Errors: {errors}")
    print("=" * 60)

    # Verify in database
    if not dry_run:
        session = get_session()
        count = session.execute(
            select(Review).where(Review.company_name == company_name)
        ).scalars().all()
        session.close()

        print(f"\n✅ Total {company_name} reviews in database: {len(count)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest Wispr App Store reviews from CSV"
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to CSV file"
    )
    parser.add_argument(
        "--company",
        type=str,
        default="wispr",
        help="Company name (default: wispr)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually insert records, just show what would happen"
    )

    args = parser.parse_args()

    ingest_wispr_csv(
        csv_file=args.csv,
        company_name=args.company,
        dry_run=args.dry_run
    )
