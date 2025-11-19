#!/usr/bin/env python3
"""
Ingest Wispr Trustpilot reviews from JSON file into database
"""

import json
from pathlib import Path
from datetime import datetime
from models import Review, get_engine, Base, get_session
from sqlalchemy.exc import IntegrityError


def parse_trustpilot_date(date_str: str) -> datetime:
    """
    Parse Trustpilot ISO 8601 date format
    Example: "2025-11-17T09:04:37.000Z"
    """
    # Remove milliseconds and Z suffix, parse as UTC
    if date_str.endswith('Z'):
        date_str = date_str[:-1]  # Remove Z

    # Handle milliseconds
    if '.' in date_str:
        date_str = date_str.split('.')[0]  # Remove milliseconds

    return datetime.fromisoformat(date_str)


def ingest_trustpilot_reviews(json_file: Path) -> None:
    """
    Ingest Trustpilot reviews from JSON file

    Args:
        json_file: Path to JSON file containing Trustpilot reviews
    """
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)

    print(f"📊 Loading {len(reviews_data)} Trustpilot reviews...")
    print()

    # Create database tables if they don't exist
    engine = get_engine()
    Base.metadata.create_all(engine)

    session = get_session()

    inserted_count = 0
    skipped_count = 0
    error_count = 0

    for review_data in reviews_data:
        try:
            # Map Trustpilot fields to our Review model
            review_id = review_data['reviewId']

            # Combine title and description
            title = review_data.get('reviewTitle', '').strip()
            description = review_data.get('reviewDescription', '').strip()

            if title and description:
                review_text = f"{title}\n\n{description}"
            elif title:
                review_text = title
            elif description:
                review_text = description
            else:
                review_text = ""

            # Parse review date
            review_date = parse_trustpilot_date(review_data['reviewDate'])

            # Create Review object
            review = Review(
                review_id=review_id,
                company_name='wispr',
                source='trustpilot',
                user_name=review_data.get('reviewer', 'Anonymous'),
                rating=int(review_data['reviewRatingScore']),
                helpful_votes=0,  # Trustpilot doesn't provide this
                date=review_date,
                review_text=review_text,
                reply_content=review_data.get('reviewCompanyResponse', '').strip() or None,
                version=None  # Trustpilot doesn't provide app version
            )

            session.add(review)
            session.commit()
            inserted_count += 1

            # Print progress
            rating_stars = '⭐' * review.rating
            print(f"✅ [{inserted_count}/{len(reviews_data)}] {rating_stars} {review.user_name} - {review.date.strftime('%Y-%m-%d')}")

        except IntegrityError:
            session.rollback()
            skipped_count += 1
            print(f"⏭️  Skipped duplicate review: {review_id}")

        except Exception as e:
            session.rollback()
            error_count += 1
            print(f"❌ Error processing review {review_data.get('reviewId', 'unknown')}: {e}")

    session.close()

    print()
    print("=" * 60)
    print("📈 INGESTION SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully inserted: {inserted_count}")
    print(f"⏭️  Skipped (duplicates):  {skipped_count}")
    print(f"❌ Errors:               {error_count}")
    print(f"📊 Total processed:      {len(reviews_data)}")
    print()

    # Verify ingestion
    session = get_session()
    total_wispr_trustpilot = session.query(Review).filter(
        Review.company_name == 'wispr',
        Review.source == 'trustpilot'
    ).count()

    total_wispr = session.query(Review).filter(
        Review.company_name == 'wispr'
    ).count()

    session.close()

    print(f"🔍 Verification:")
    print(f"   Wispr Trustpilot reviews in database: {total_wispr_trustpilot}")
    print(f"   Total Wispr reviews in database:      {total_wispr}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest Wispr Trustpilot reviews from JSON file"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="reviews/wispr_trustpilot.json",
        help="Path to Trustpilot JSON file (default: reviews/wispr_trustpilot.json)"
    )

    args = parser.parse_args()

    json_file = Path(args.file)

    if not json_file.exists():
        print(f"❌ Error: File not found: {json_file}")
        exit(1)

    ingest_trustpilot_reviews(json_file)
