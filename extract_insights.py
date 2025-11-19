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

from models import Review, Insight, YouTubeVideo, get_session

# Load environment variables from .env file
load_dotenv()

# Pydantic models for structured output
class ReviewInsights(BaseModel):
    """Structured output schema for review insights (v1 and v2)"""

    pain_points: List[str]
    feature_requests: List[str]
    praises: List[str]


class ReviewInsightsV3(BaseModel):
    """Structured output schema for review insights v3 (includes use cases)"""

    pain_points: List[str]
    feature_requests: List[str]
    use_cases: List[str]


def load_prompt(prompt_version: int = 1) -> str:
    """
    Load the extraction prompt from file

    Args:
        prompt_version: Version of prompt to use (1, 2, or 3)

    Returns:
        Prompt text
    """
    prompt_file = Path(__file__).parent / f"extraction_prompt{prompt_version if prompt_version > 1 else ''}.txt"
    with open(prompt_file, "r") as f:
        return f.read()


def get_reviews_to_process(
    session: Session, company_name: str, limit: Optional[int] = None, force: bool = False
) -> List[Review]:
    """
    Get reviews to process based on generated_insights flag

    Args:
        session: SQLAlchemy session
        company_name: Company name to filter reviews
        limit: Maximum number of reviews to fetch
        force: If True, get all reviews regardless of generated_insights flag

    Returns:
        List of Review objects
    """
    # Query for reviews to process
    query = (
        select(Review)
        .where(Review.company_name == company_name)
        .where(Review.review_text.isnot(None))
        .where(Review.review_text != "")
        .order_by(Review.date.desc())
    )

    # Filter by generated_insights flag unless force=True
    if not force:
        query = query.where(Review.generated_insights == False)

    if limit:
        query = query.limit(limit)

    return list(session.execute(query).scalars().all())


def extract_insights_from_review(
    client: OpenAI, system_prompt: str, review: Review, prompt_version: int = 2
):
    """
    Use OpenAI to extract insights from a single review

    Args:
        client: OpenAI client instance
        system_prompt: The extraction prompt
        review: Review object
        prompt_version: Version of prompt (determines response format)

    Returns:
        ReviewInsights or ReviewInsightsV3 object with extracted lists
    """
    user_message = f"""Review (Rating: {review.rating}/5):
{review.review_text}"""

    # Use appropriate response format based on prompt version
    response_format = ReviewInsightsV3 if prompt_version == 3 else ReviewInsights

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # Using mini for cost-effectiveness
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=response_format,
        temperature=0.3,  # Lower temperature for more consistent extraction
    )

    return completion.choices[0].message.parsed


def delete_existing_insights(session: Session, review_id: str) -> int:
    """
    Delete all existing insights for a review (used with --force)

    Args:
        session: SQLAlchemy session
        review_id: Review ID to delete insights for

    Returns:
        Number of insights deleted
    """
    deleted = session.query(Insight).filter(Insight.review_id == review_id).delete()
    session.commit()
    return deleted


def store_insights(session: Session, review: Review, insights, company_name: str, prompt_version: int = 1) -> int:
    """
    Store extracted insights in the database and mark review as processed

    Args:
        session: SQLAlchemy session
        review: Review object
        insights: ReviewInsights or ReviewInsightsV3 object
        company_name: Company name
        prompt_version: Version of prompt used for extraction

    Returns:
        Number of insights stored
    """
    count = 0
    current_time = datetime.now()

    # Store pain points
    for pain_point in insights.pain_points:
        insight = Insight(
            review_id=review.review_id,
            company_name=company_name,
            insight_text=pain_point,
            insight_type="pain_point",
            review_date=review.date,
            extracted_at=current_time,
            source_type='review',
            source_id=review.review_id,
        )
        session.add(insight)
        count += 1

    # Store feature requests
    for feature_request in insights.feature_requests:
        insight = Insight(
            review_id=review.review_id,
            company_name=company_name,
            insight_text=feature_request,
            insight_type="feature_request",
            review_date=review.date,
            extracted_at=current_time,
            source_type='review',
            source_id=review.review_id,
        )
        session.add(insight)
        count += 1

    # Store praises (v1, v2) or use_cases (v3)
    if hasattr(insights, 'praises'):
        for praise in insights.praises:
            insight = Insight(
                review_id=review.review_id,
                company_name=company_name,
                insight_text=praise,
                insight_type="praise",
                review_date=review.date,
                extracted_at=current_time,
                source_type='review',
                source_id=review.review_id,
            )
            session.add(insight)
            count += 1

    if hasattr(insights, 'use_cases'):
        for use_case in insights.use_cases:
            insight = Insight(
                review_id=review.review_id,
                company_name=company_name,
                insight_text=use_case,
                insight_type="use_case",
                review_date=review.date,
                extracted_at=current_time,
                source_type='review',
                source_id=review.review_id,
            )
            session.add(insight)
            count += 1

    # Mark review as processed
    review.generated_insights = True
    session.add(review)

    session.commit()
    return count


def process_reviews(company_name: str, limit: Optional[int] = None, force: bool = False, prompt_version: int = 1) -> None:
    """
    Main function to process reviews and extract insights

    Args:
        company_name: Company name to process reviews for
        limit: Maximum number of reviews to process (None for all)
        force: If True, regenerate insights for all reviews (delete existing first)
        prompt_version: Version of prompt to use (1, 2, or 3)
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Load prompt
    system_prompt = load_prompt(prompt_version)
    prompt_file = f"extraction_prompt{prompt_version if prompt_version > 1 else ''}.txt"
    print(f"📄 Loaded extraction prompt from {prompt_file}")

    # Create database session
    session = get_session()
    print(f"📊 Connected to database")
    print(f"🏢 Company: {company_name}")
    if force:
        print(f"🔄 Force mode: Will regenerate insights for ALL reviews")

    # Get reviews to process
    reviews = get_reviews_to_process(session, company_name, limit, force)
    total_reviews = len(reviews)

    if total_reviews == 0:
        if force:
            print("\n✅ No reviews found for this company!")
        else:
            print("\n✅ All reviews have been processed! Use --force to regenerate.")
        session.close()
        return

    print(f"\n🔍 Found {total_reviews:,} reviews to process")
    print("=" * 60)

    # Process reviews
    total_insights = 0
    total_deleted = 0
    processed = 0
    errors = 0

    for review in reviews:
        processed += 1

        try:
            # If force mode, delete existing insights first
            if force:
                deleted = delete_existing_insights(session, review.review_id)
                if deleted > 0:
                    total_deleted += deleted
                    print(f"[{processed}/{total_reviews}] 🗑️  Deleted {deleted} existing insights for {review.review_id[:8]}...")

            # Extract insights using OpenAI
            insights = extract_insights_from_review(client, system_prompt, review, prompt_version)

            # Store insights in database (also marks review as processed)
            insight_count = store_insights(session, review, insights, company_name, prompt_version)
            total_insights += insight_count

            # Progress update
            pp_count = len(insights.pain_points)
            fr_count = len(insights.feature_requests)

            # Handle v3 (use_cases) vs v1/v2 (praises)
            if hasattr(insights, 'use_cases'):
                uc_count = len(insights.use_cases)
                print(
                    f"[{processed}/{total_reviews}] Review {review.review_id[:8]}... | "
                    f"⚠️  {pp_count} | 💡 {fr_count} | 🎯 {uc_count} | "
                    f"Total: {total_insights}"
                )
            else:
                pr_count = len(insights.praises)
                print(
                    f"[{processed}/{total_reviews}] Review {review.review_id[:8]}... | "
                    f"⚠️  {pp_count} | 💡 {fr_count} | ⭐ {pr_count} | "
                    f"Total: {total_insights}"
                )

            # Show sample if insights found
            if insight_count > 0:
                if insights.pain_points:
                    print(f"  └─ Pain: {insights.pain_points[0][:80]}...")
                if insights.feature_requests:
                    print(f"  └─ Request: {insights.feature_requests[0][:80]}...")
                if hasattr(insights, 'praises') and insights.praises:
                    print(f"  └─ Praise: {insights.praises[0][:80]}...")
                if hasattr(insights, 'use_cases') and insights.use_cases:
                    print(f"  └─ Use Case: {insights.use_cases[0][:80]}...")

        except Exception as e:
            errors += 1
            print(
                f"[{processed}/{total_reviews}] ❌ Error processing {review.review_id[:8]}...: {e}"
            )
            session.rollback()  # Rollback on error
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "=" * 60)
    print("✅ PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Reviews processed: {processed:,}")
    if force and total_deleted > 0:
        print(f"Previous insights deleted: {total_deleted:,}")
    print(f"Total insights extracted: {total_insights:,}")
    print(f"Errors: {errors}")
    if processed > 0:
        print(f"Average insights per review: {total_insights/processed:.2f}")
    print("=" * 60)


def get_youtube_videos_to_process(
    session: Session, company_name: str, limit: Optional[int] = None
) -> List[YouTubeVideo]:
    """
    Get YouTube videos to process (those with subtitles or descriptions)

    Args:
        session: SQLAlchemy session
        company_name: Company name (for consistency, though not filtered)
        limit: Maximum number of videos to fetch

    Returns:
        List of YouTubeVideo objects with subtitle_srt or text
    """
    query = (
        select(YouTubeVideo)
        .where(
            (YouTubeVideo.subtitle_srt.isnot(None)) |
            (YouTubeVideo.text.isnot(None))
        )
        .order_by(YouTubeVideo.view_count.desc())
    )

    if limit:
        query = query.limit(limit)

    return list(session.execute(query).scalars().all())


def extract_insights_from_youtube_video(
    client: OpenAI, system_prompt: str, video: YouTubeVideo, prompt_version: int = 3
):
    """
    Use OpenAI to extract insights from a YouTube video (subtitles + description)

    Args:
        client: OpenAI client instance
        system_prompt: The extraction prompt
        video: YouTubeVideo object
        prompt_version: Version of prompt (determines response format)

    Returns:
        ReviewInsights or ReviewInsightsV3 object with extracted lists
    """
    # Combine subtitle and description text
    content_parts = []

    if video.title:
        content_parts.append(f"Video Title: {video.title}")

    if video.text:
        content_parts.append(f"\nVideo Description:\n{video.text}")

    if video.subtitle_srt:
        # Extract text from SRT (skip timestamps)
        subtitle_lines = []
        for line in video.subtitle_srt.split('\n'):
            # Skip line numbers, timestamps, and empty lines
            if line.strip() and not line.strip().isdigit() and '-->' not in line:
                subtitle_lines.append(line.strip())

        if subtitle_lines:
            content_parts.append(f"\nVideo Transcript:\n{' '.join(subtitle_lines)}")

    if not content_parts:
        # No content to analyze
        return ReviewInsightsV3(pain_points=[], feature_requests=[], use_cases=[])

    user_message = f"""YouTube Video (Views: {video.view_count:,}):
{chr(10).join(content_parts)}"""

    # Use appropriate response format based on prompt version
    response_format = ReviewInsightsV3 if prompt_version == 3 else ReviewInsights

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=response_format,
        temperature=0.3,
    )

    return completion.choices[0].message.parsed


def store_youtube_insights(
    session: Session, video: YouTubeVideo, insights, company_name: str
) -> int:
    """
    Store extracted insights from YouTube video in the database

    Args:
        session: SQLAlchemy session
        video: YouTubeVideo object
        insights: ReviewInsights or ReviewInsightsV3 object
        company_name: Company name

    Returns:
        Number of insights stored
    """
    count = 0
    current_time = datetime.now()

    # Store pain points
    for pain_point in insights.pain_points:
        insight = Insight(
            review_id=None,  # Not from a review
            company_name=company_name,
            insight_text=pain_point,
            insight_type="pain_point",
            review_date=video.date,  # Use video upload date
            extracted_at=current_time,
            source_type='youtube_video',
            source_id=video.id,
        )
        session.add(insight)
        count += 1

    # Store feature requests
    for feature_request in insights.feature_requests:
        insight = Insight(
            review_id=None,
            company_name=company_name,
            insight_text=feature_request,
            insight_type="feature_request",
            review_date=video.date,
            extracted_at=current_time,
            source_type='youtube_video',
            source_id=video.id,
        )
        session.add(insight)
        count += 1

    # Store praises (v1, v2) or use_cases (v3)
    if hasattr(insights, 'praises'):
        for praise in insights.praises:
            insight = Insight(
                review_id=None,
                company_name=company_name,
                insight_text=praise,
                insight_type="praise",
                review_date=video.date,
                extracted_at=current_time,
                source_type='youtube_video',
                source_id=video.id,
            )
            session.add(insight)
            count += 1

    if hasattr(insights, 'use_cases'):
        for use_case in insights.use_cases:
            insight = Insight(
                review_id=None,
                company_name=company_name,
                insight_text=use_case,
                insight_type="use_case",
                review_date=video.date,
                extracted_at=current_time,
                source_type='youtube_video',
                source_id=video.id,
            )
            session.add(insight)
            count += 1

    session.commit()
    return count


def process_youtube_videos(
    company_name: str, limit: Optional[int] = None, prompt_version: int = 3
) -> None:
    """
    Main function to process YouTube videos and extract insights

    Args:
        company_name: Company name for insight attribution
        limit: Maximum number of videos to process (None for all)
        prompt_version: Version of prompt to use (1, 2, or 3)
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Load prompt
    system_prompt = load_prompt(prompt_version)
    prompt_file = f"extraction_prompt{prompt_version if prompt_version > 1 else ''}.txt"
    print(f"📄 Loaded extraction prompt from {prompt_file}")

    # Create database session
    session = get_session()
    print(f"📊 Connected to database")
    print(f"🏢 Company: {company_name}")
    print(f"🎬 Processing YouTube videos")

    # Get videos to process
    videos = get_youtube_videos_to_process(session, company_name, limit)
    total_videos = len(videos)

    if total_videos == 0:
        print("\n✅ No YouTube videos with subtitles/descriptions found!")
        session.close()
        return

    print(f"\n🔍 Found {total_videos:,} YouTube videos to process")
    print("=" * 60)

    # Process videos
    total_insights = 0
    processed = 0
    errors = 0

    for video in videos:
        processed += 1

        try:
            # Extract insights using OpenAI
            insights = extract_insights_from_youtube_video(client, system_prompt, video, prompt_version)

            # Store insights in database
            insight_count = store_youtube_insights(session, video, insights, company_name)
            total_insights += insight_count

            # Progress update
            pp_count = len(insights.pain_points)
            fr_count = len(insights.feature_requests)

            # Handle v3 (use_cases) vs v1/v2 (praises)
            if hasattr(insights, 'use_cases'):
                uc_count = len(insights.use_cases)
                print(
                    f"[{processed}/{total_videos}] Video {video.id} ({video.view_count:,} views) | "
                    f"⚠️  {pp_count} | 💡 {fr_count} | 🎯 {uc_count} | "
                    f"Total: {total_insights}"
                )
            else:
                pr_count = len(insights.praises)
                print(
                    f"[{processed}/{total_videos}] Video {video.id} ({video.view_count:,} views) | "
                    f"⚠️  {pp_count} | 💡 {fr_count} | ⭐ {pr_count} | "
                    f"Total: {total_insights}"
                )

            # Show sample if insights found
            if insight_count > 0:
                print(f"  └─ Title: {video.title[:60]}...")
                if insights.pain_points:
                    print(f"  └─ Pain: {insights.pain_points[0][:80]}...")
                if insights.feature_requests:
                    print(f"  └─ Request: {insights.feature_requests[0][:80]}...")
                if hasattr(insights, 'use_cases') and insights.use_cases:
                    print(f"  └─ Use Case: {insights.use_cases[0][:80]}...")

        except Exception as e:
            errors += 1
            print(
                f"[{processed}/{total_videos}] ❌ Error processing {video.id}: {e}"
            )
            session.rollback()
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "=" * 60)
    print("✅ PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Videos processed: {processed:,}")
    print(f"Total insights extracted: {total_insights:,}")
    print(f"Errors: {errors}")
    if processed > 0:
        print(f"Average insights per video: {total_insights/processed:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract insights from reviews or YouTube videos using OpenAI"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'wispr')"
    )
    parser.add_argument("--limit", type=int, help="Limit number of items to process")
    parser.add_argument(
        "--source",
        type=str,
        choices=['reviews', 'youtube'],
        default='reviews',
        help="Source to extract insights from: 'reviews' or 'youtube' (default: reviews)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="[Reviews only] Regenerate insights for ALL reviews (deletes existing insights first)"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode: process only test reviews"
    )
    parser.add_argument(
        "--prompt-version",
        type=int,
        default=3,
        help="Prompt version to use: 1 (extraction_prompt.txt), 2 (extraction_prompt2.txt), or 3 (extraction_prompt3.txt with use_cases)"
    )

    args = parser.parse_args()
    limit = args.limit if args.limit else None

    if not args.test:
        if args.source == 'youtube':
            # Process YouTube videos
            process_youtube_videos(
                company_name=args.company,
                limit=limit,
                prompt_version=args.prompt_version
            )
        else:
            # Process reviews (default)
            process_reviews(
                company_name=args.company,
                limit=limit,
                force=args.force,
                prompt_version=args.prompt_version
            )
    else:
        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Load prompt
        system_prompt = load_prompt(args.prompt_version)
        prompt_file = f"extraction_prompt{args.prompt_version if args.prompt_version > 1 else ''}.txt"
        print(f"📄 Loaded extraction prompt from {prompt_file}")

        test_reviews = [
            'Step counting works maybe 1 out of every 3 days. Meanwhile Noom blowing up my spam folder trying to sell me a Premium plan, 2 or 3 emails a day, and "personal" emails from theor CEO or someone, when their freebie doesn\'t even come close to working. lol, totally.',
            "Would give more stars if the bar video scanner actually worked and the database of food items for the log was consistent. edit: dropped a star because aforementioned issue continues to be a problem, and is getting worse.",
            "App has been miscalculating my steps for a week now. I try to manually update, but it doesn't save. It's just making up it's own numbers.",
            "Constantly not counting steps. Super aggravating and needs a fix. Have to force stop and hope the step counting restarts."

        ]
        for idx, review_text in enumerate(test_reviews, 1):
            review = Review(rating=2, review_text=review_text)
            extracted = extract_insights_from_review(client, system_prompt, review, args.prompt_version)

            print("\n" + "="*80)
            print(f"TEST REVIEW #{idx}")
            print("="*80)
            print(f"Review: {review.review_text}")
            print()

            if extracted.pain_points:
                print(f"⚠️  PAIN POINTS ({len(extracted.pain_points)}):")
                for i, pain in enumerate(extracted.pain_points, 1):
                    print(f"  {i}. {pain}")
            else:
                print("⚠️  PAIN POINTS: (none)")

            if extracted.feature_requests:
                print(f"\n💡 FEATURE REQUESTS ({len(extracted.feature_requests)}):")
                for i, feature in enumerate(extracted.feature_requests, 1):
                    print(f"  {i}. {feature}")
            else:
                print("\n💡 FEATURE REQUESTS: (none)")

            if hasattr(extracted, 'praises'):
                if extracted.praises:
                    print(f"\n⭐ PRAISES ({len(extracted.praises)}):")
                    for i, praise in enumerate(extracted.praises, 1):
                        print(f"  {i}. {praise}")
                else:
                    print("\n⭐ PRAISES: (none)")

            if hasattr(extracted, 'use_cases'):
                if extracted.use_cases:
                    print(f"\n🎯 USE CASES ({len(extracted.use_cases)}):")
                    for i, use_case in enumerate(extracted.use_cases, 1):
                        print(f"  {i}. {use_case}")
                else:
                    print("\n🎯 USE CASES: (none)")
