#!/usr/bin/env python3
"""
Extract insights from Noom app reviews using OpenAI structured output
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from models import Review, Insight, get_session

# Load environment variables from .env file
load_dotenv()

# File paths
PROMPT_FILE = Path(__file__).parent / "extraction_prompt.txt"


# Pydantic models for structured output
class ReviewInsights(BaseModel):
    """Structured output schema for review insights"""
    pain_points: List[str]
    feature_requests: List[str]
    praises: List[str]


def load_prompt() -> str:
    """Load the extraction prompt from file"""
    with open(PROMPT_FILE, 'r') as f:
        return f.read()


def get_unprocessed_reviews(session: Session, limit: Optional[int] = None, offset: int = 0) -> List[Review]:
    """
    Get reviews that haven't been processed yet

    Args:
        session: SQLAlchemy session
        limit: Maximum number of reviews to fetch
        offset: Number of reviews to skip (for pagination)

    Returns:
        List of Review objects
    """
    # Subquery to get review_ids that have already been processed
    processed_review_ids = select(Insight.review_id).distinct()

    # Query for unprocessed reviews
    query = (
        select(Review)
        .where(Review.review_id.notin_(processed_review_ids))
        .where(Review.review_text.isnot(None))
        .where(Review.review_text != "")
        .order_by(Review.date.desc())
    )

    if offset > 0:
        query = query.offset(offset)

    if limit:
        query = query.limit(limit)

    return list(session.execute(query).scalars().all())


def extract_insights_from_review(
    client: OpenAI,
    system_prompt: str,
    review: Review
) -> ReviewInsights:
    """
    Use OpenAI to extract insights from a single review

    Args:
        client: OpenAI client instance
        system_prompt: The extraction prompt
        review: Review object

    Returns:
        ReviewInsights object with extracted lists
    """
    user_message = f"""Review (Rating: {review.rating}/5):
{review.review_text}"""

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # Using mini for cost-effectiveness
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        response_format=ReviewInsights,
        temperature=0.3  # Lower temperature for more consistent extraction
    )

    return completion.choices[0].message.parsed


def store_insights(
    session: Session,
    review: Review,
    insights: ReviewInsights
) -> int:
    """
    Store extracted insights in the database

    Args:
        session: SQLAlchemy session
        review: Review object
        insights: ReviewInsights object

    Returns:
        Number of insights stored
    """
    count = 0
    current_time = datetime.now()

    # Store pain points
    for pain_point in insights.pain_points:
        insight = Insight(
            review_id=review.review_id,
            insight_text=pain_point,
            insight_type="pain_point",
            review_date=review.date,
            extracted_at=current_time
        )
        session.add(insight)
        count += 1

    # Store feature requests
    for feature_request in insights.feature_requests:
        insight = Insight(
            review_id=review.review_id,
            insight_text=feature_request,
            insight_type="feature_request",
            review_date=review.date,
            extracted_at=current_time
        )
        session.add(insight)
        count += 1

    # Store praises
    for praise in insights.praises:
        insight = Insight(
            review_id=review.review_id,
            insight_text=praise,
            insight_type="praise",
            review_date=review.date,
            extracted_at=current_time
        )
        session.add(insight)
        count += 1

    session.commit()
    return count


def process_reviews(limit: Optional[int] = None, offset: int = 0) -> None:
    """
    Main function to process reviews and extract insights

    Args:
        limit: Maximum number of reviews to process (None for all)
        offset: Number of reviews to skip (for batch processing)
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Load prompt
    system_prompt = load_prompt()
    print(f"📄 Loaded extraction prompt from {PROMPT_FILE}")

    # Create database session
    session = get_session()
    print(f"📊 Connected to database")

    # Get unprocessed reviews
    reviews = get_unprocessed_reviews(session, limit, offset)
    total_reviews = len(reviews)

    if total_reviews == 0:
        print("\n✅ All reviews have been processed!")
        session.close()
        return

    offset_msg = f" (skipping first {offset:,})" if offset > 0 else ""
    print(f"\n🔍 Found {total_reviews:,} reviews to process{offset_msg}")
    print("="*60)

    # Process reviews
    total_insights = 0
    processed = 0
    errors = 0

    for review in reviews:
        processed += 1

        try:
            # Extract insights using OpenAI
            insights = extract_insights_from_review(client, system_prompt, review)

            # Store insights in database
            insight_count = store_insights(session, review, insights)
            total_insights += insight_count

            # Progress update
            pp_count = len(insights.pain_points)
            fr_count = len(insights.feature_requests)
            pr_count = len(insights.praises)

            print(f"[{processed}/{total_reviews}] Review {review.review_id[:8]}... | "
                  f"⚠️  {pp_count} | 💡 {fr_count} | ⭐ {pr_count} | "
                  f"Total: {total_insights}")

            # Show sample if insights found
            if insight_count > 0:
                if insights.pain_points:
                    print(f"  └─ Pain: {insights.pain_points[0][:80]}...")
                if insights.feature_requests:
                    print(f"  └─ Request: {insights.feature_requests[0][:80]}...")
                if insights.praises:
                    print(f"  └─ Praise: {insights.praises[0][:80]}...")

        except Exception as e:
            errors += 1
            print(f"[{processed}/{total_reviews}] ❌ Error processing {review.review_id[:8]}...: {e}")
            session.rollback()  # Rollback on error
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "="*60)
    print("✅ PROCESSING COMPLETE")
    print("="*60)
    print(f"Reviews processed: {processed:,}")
    print(f"Total insights extracted: {total_insights:,}")
    print(f"Errors: {errors}")
    if processed > 0:
        print(f"Average insights per review: {total_insights/processed:.2f}")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract insights from reviews using OpenAI")
    parser.add_argument("--limit", type=int, help="Limit number of reviews to process")
    parser.add_argument("--offset", type=int, default=0, help="Number of reviews to skip (for batch processing)")
    parser.add_argument("--test", action="store_true", help="Test mode: process only 5 reviews")

    args = parser.parse_args()
    limit = 3 if not args.limit else args.limit

    if not args.test:
        process_reviews(limit=limit, offset=args.offset)
    else:
         # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Load prompt
        system_prompt = load_prompt()
        print(f"📄 Loaded extraction prompt from {PROMPT_FILE}")

        review = Review(rating=2, review_text="Step counting works maybe 1 out of every 3 days. Meanwhile Noom blowing up my spam folder trying to sell me a Premium plan, 2 or 3 emails a day, and \"personal\" emails from theor CEO or someone, when their freebie doesn't even come close to working. lol, totally.")
        extracted = extract_insights_from_review(client, system_prompt, review)
        print(extracted)


