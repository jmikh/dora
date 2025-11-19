#!/usr/bin/env python3
"""
Print reviews with their extracted insights for quality checking
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Review, Insight, get_session

def get_reviews_with_insights(
    session: Session,
    company_name: str,
    insight_type: Optional[str] = None,    limit: Optional[int] = None
) -> List[Review]:
    """
    Get reviews that have insights

    Args:
        session: SQLAlchemy session
        company_name: Company name to filter reviews
        insight_type: Filter by insight type (pain_point, feature_request, praise) or None for all        limit: Maximum number of reviews to fetch

    Returns:
        List of Review objects with insights loaded
    """
    query = (
        select(Review)
        .join(Insight, Review.review_id == Insight.review_id)
        .where(Review.company_name == company_name)
        .distinct()
        .order_by(Review.date.desc())
    )

    if insight_type:
        query = query.where(Insight.insight_type == insight_type)

    if prompt_version is not None:
        query = query.where(Insight.prompt_version == prompt_version)

    if limit:
        query = query.limit(limit)

    reviews = list(session.execute(query).scalars().all())

    # Load insights for each review
    for review in reviews:
        insights_query = select(Insight).where(Insight.review_id == review.review_id)
        if insight_type:
            insights_query = insights_query.where(Insight.insight_type == insight_type)
        if prompt_version is not None:
            insights_query = insights_query.where(Insight.prompt_version == prompt_version)
        insights_query = insights_query.order_by(Insight.insight_type)

        review.insights = list(session.execute(insights_query).scalars().all())

    return reviews

def print_review_insights_report(
    company_name: str,
    insight_type: Optional[str] = None,    limit: Optional[int] = 20
) -> None:
    """
    Print reviews with their insights for manual quality checking

    Args:
        company_name: Company name to filter reviews
        insight_type: Filter by insight type or None for all        limit: Maximum number of reviews to display
    """
    session = get_session()
    print(f"🏢 Company: {company_name}\n")

    # Get reviews with insights
    reviews = get_reviews_with_insights(session, company_name, insight_type, prompt_version, limit)

    if not reviews:
        print("\n❌ No reviews with insights found!")
        session.close()
        return

    # Print header
    type_filter = f" ({insight_type})" if insight_type else " (all types)"
    version_filter = f" - Prompt v{prompt_version}" if prompt_version else ""
    print("="*80)
    print(f"REVIEW INSIGHTS REPORT{type_filter}{version_filter}")
    print("="*80)
    print(f"Total reviews: {len(reviews)}")
    print("="*80)
    print()

    # Print each review and its insights
    for idx, review in enumerate(reviews, 1):
        print("="*80)
        print(f"REVIEW #{idx} - ID: {review.review_id}")
        print("="*80)
        print(f"User: {review.user_name}")
        print(f"Rating: {'⭐' * review.rating}")
        print(f"Date: {review.date}")
        print(f"Version: {review.version}")
        print()
        print("--- REVIEW TEXT ---")
        print(review.review_text)
        print()

        # Group insights by type
        pain_points = [i for i in review.insights if i.insight_type == "pain_point"]
        feature_requests = [i for i in review.insights if i.insight_type == "feature_request"]
        praises = [i for i in review.insights if i.insight_type == "praise"]
        use_cases = [i for i in review.insights if i.insight_type == "use_case"]

        print("--- EXTRACTED INSIGHTS ---")

        if pain_points:
            print(f"\n⚠️  PAIN POINTS ({len(pain_points)}):")
            for i, insight in enumerate(pain_points, 1):
                version = getattr(insight, 'prompt_version', 1)
                print(f"  {i}. [v{version}] {insight.insight_text}")

        if feature_requests:
            print(f"\n💡 FEATURE REQUESTS ({len(feature_requests)}):")
            for i, insight in enumerate(feature_requests, 1):
                version = getattr(insight, 'prompt_version', 1)
                print(f"  {i}. [v{version}] {insight.insight_text}")

        if praises:
            print(f"\n⭐ PRAISES ({len(praises)}):")
            for i, insight in enumerate(praises, 1):
                version = getattr(insight, 'prompt_version', 1)
                print(f"  {i}. [v{version}] {insight.insight_text}")

        if use_cases:
            print(f"\n🎯 USE CASES ({len(use_cases)}):")
            for i, insight in enumerate(use_cases, 1):
                version = getattr(insight, 'prompt_version', 1)
                print(f"  {i}. [v{version}] {insight.insight_text}")

        print("\n")

    session.close()

    # Summary
    print("="*80)
    print("END OF REPORT")
    print("="*80)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Print reviews with their extracted insights for quality checking"
    )
    parser.add_argument(
        "--type",
        type=str,
        help="Filter by insight type (e.g., pain_point, feature_request, praise, use_case; default: show all types)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of reviews to display (default: 20)"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'myfitnesspal')"
    )

    args = parser.parse_args()

    print_review_insights_report(
        company_name=args.company,
        insight_type=args.type,
        limit=args.limit
    )
