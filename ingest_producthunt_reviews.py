#!/usr/bin/env python3
"""
Ingest Wispr Product Hunt reviews from JSON file into database
"""

import json
from pathlib import Path
from datetime import datetime
from models import Review, get_engine, Base, get_session
from sqlalchemy.exc import IntegrityError
import hashlib


def generate_review_id(name: str, date: str, review_text: str) -> str:
    """
    Generate a unique review ID from review data
    Product Hunt reviews don't have unique IDs, so we create one
    """
    unique_string = f"{name}_{date}_{review_text[:50]}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def parse_producthunt_date(date_str: str) -> datetime:
    """
    Parse Product Hunt date format
    Example: "2025-11-16"
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def ingest_producthunt_reviews(json_file: Path) -> None:
    """
    Ingest Product Hunt reviews from JSON file

    Args:
        json_file: Path to JSON file containing Product Hunt reviews
    """
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)

    print(f"📊 Loading {len(reviews_data)} Product Hunt reviews...")
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
            # Generate unique review ID (Product Hunt doesn't provide one)
            review_id = generate_review_id(
                review_data['name'],
                review_data['date_inferred'],
                review_data['review_text']
            )

            # Use only review_text field (ignore whats_great and needs_improvement)
            review_text = review_data.get('review_text', '').strip()

            if not review_text:
                print(f"⚠️  Skipping review with no text from {review_data.get('name', 'unknown')}")
                skipped_count += 1
                continue

            # Parse review date
            review_date = parse_producthunt_date(review_data['date_inferred'])

            # Get helpful count (can be null)
            helpful_count = review_data.get('helpful_count')
            helpful_votes = helpful_count if helpful_count is not None else 0

            # Create Review object
            review = Review(
                review_id=review_id,
                company_name='wispr',
                source='producthunt',
                user_name=review_data.get('name', 'Anonymous'),
                rating=int(review_data['rating']),
                helpful_votes=helpful_votes,
                date=review_date,
                review_text=review_text,
                reply_content=None,  # Product Hunt data doesn't include company replies
                version=None  # Product Hunt data doesn't provide app version
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
            print(f"⏭️  Skipped duplicate review: {review_data.get('name', 'unknown')} - {review_data.get('date_inferred', 'unknown')}")

        except Exception as e:
            session.rollback()
            error_count += 1
            print(f"❌ Error processing review from {review_data.get('name', 'unknown')}: {e}")

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
    total_wispr_producthunt = session.query(Review).filter(
        Review.company_name == 'wispr',
        Review.source == 'producthunt'
    ).count()

    total_wispr = session.query(Review).filter(
        Review.company_name == 'wispr'
    ).count()

    session.close()

    print(f"🔍 Verification:")
    print(f"   Wispr Product Hunt reviews in database: {total_wispr_producthunt}")
    print(f"   Total Wispr reviews in database:        {total_wispr}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest Wispr Product Hunt reviews from JSON file"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="reviews/wispr_producthunt.json",
        help="Path to Product Hunt JSON file (default: reviews/wispr_producthunt.json)"
    )

    args = parser.parse_args()

    json_file = Path(args.file)

    if not json_file.exists():
        print(f"❌ Error: File not found: {json_file}")
        exit(1)

    ingest_producthunt_reviews(json_file)
