#!/usr/bin/env python3
"""
Ingest Wispr Microsoft Store reviews from JSON file into database
"""

import json
from pathlib import Path
from datetime import datetime
from models import Review, get_engine, Base, get_session
from sqlalchemy.exc import IntegrityError
import hashlib


def generate_review_id(author: str, date: str, title: str) -> str:
    """
    Generate a unique review ID from review data
    Microsoft reviews don't have unique IDs, so we create one
    """
    unique_string = f"{author}_{date}_{title}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def parse_microsoft_date(date_str: str) -> datetime:
    """
    Parse Microsoft date format
    Example: "2025-03-18"
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def ingest_microsoft_reviews(json_file: Path) -> None:
    """
    Ingest Microsoft Store reviews from JSON file

    Args:
        json_file: Path to JSON file containing Microsoft Store reviews
    """
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)

    print(f"📊 Loading {len(reviews_data)} Microsoft Store reviews...")
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
            # Generate unique review ID (Microsoft doesn't provide one)
            review_id = generate_review_id(
                review_data['author'],
                review_data['date'],
                review_data['title']
            )

            # Combine title and review text
            title = review_data.get('title', '').strip()
            review_text_body = review_data.get('review', '').strip()

            if title and review_text_body:
                review_text = f"{title}\n\n{review_text_body}"
            elif title:
                review_text = title
            elif review_text_body:
                review_text = review_text_body
            else:
                review_text = ""

            # Parse review date
            review_date = parse_microsoft_date(review_data['date'])

            # Calculate helpful votes (up - down)
            helpful_up = review_data.get('helpful_up', 0)
            helpful_down = review_data.get('helpful_down', 0)
            helpful_votes = helpful_up - helpful_down

            # Create Review object
            review = Review(
                review_id=review_id,
                company_name='wispr',
                source='microsoft',
                user_name=review_data.get('author', 'Anonymous'),
                rating=int(review_data['rating']),
                helpful_votes=helpful_votes,
                date=review_date,
                review_text=review_text,
                reply_content=None,  # Microsoft data doesn't include company replies
                version=None  # Microsoft data doesn't provide app version
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
            print(f"⏭️  Skipped duplicate review: {review_data.get('author', 'unknown')} - {review_data.get('date', 'unknown')}")

        except Exception as e:
            session.rollback()
            error_count += 1
            print(f"❌ Error processing review from {review_data.get('author', 'unknown')}: {e}")

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
    total_wispr_microsoft = session.query(Review).filter(
        Review.company_name == 'wispr',
        Review.source == 'microsoft'
    ).count()

    total_wispr = session.query(Review).filter(
        Review.company_name == 'wispr'
    ).count()

    session.close()

    print(f"🔍 Verification:")
    print(f"   Wispr Microsoft reviews in database: {total_wispr_microsoft}")
    print(f"   Total Wispr reviews in database:     {total_wispr}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest Wispr Microsoft Store reviews from JSON file"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="reviews/wispr_microsoft_apps.json",
        help="Path to Microsoft Store JSON file (default: reviews/wispr_microsoft_apps.json)"
    )

    args = parser.parse_args()

    json_file = Path(args.file)

    if not json_file.exists():
        print(f"❌ Error: File not found: {json_file}")
        exit(1)

    ingest_microsoft_reviews(json_file)
