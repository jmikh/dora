#!/usr/bin/env python3
"""
Generate embeddings for insights using OpenAI
"""

import os
import json
from typing import List, Optional
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from models import Insight, get_session

# Load environment variables
load_dotenv()


def get_insights_without_embeddings(
    session: Session,
    insight_type: str = "pain_point",
    limit: Optional[int] = None
) -> List[Insight]:
    """
    Get insights that don't have embeddings yet

    Args:
        session: SQLAlchemy session
        insight_type: Type of insight to filter ('pain_point', 'feature_request', 'praise')
        limit: Maximum number of insights to fetch

    Returns:
        List of Insight objects
    """
    query = (
        select(Insight)
        .where(Insight.insight_type == insight_type)
        .where(Insight.embedding.is_(None))
        .order_by(Insight.review_date.desc())
    )

    if limit:
        query = query.limit(limit)

    return list(session.execute(query).scalars().all())


def generate_embedding(client: OpenAI, text: str) -> List[float]:
    """
    Generate embedding for a single text using OpenAI

    Args:
        client: OpenAI client instance
        text: Text to embed

    Returns:
        Embedding vector as list of floats
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",  # Cost-effective, good quality
        input=text
    )

    return response.data[0].embedding


def generate_embeddings(
    insight_type: str = "pain_point",
    limit: Optional[int] = None
) -> None:
    """
    Generate embeddings for insights without them

    Args:
        insight_type: Type of insight to process
        limit: Maximum number to process
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Create database session
    session = get_session()
    print(f"📊 Connected to database")

    # Get insights without embeddings
    insights = get_insights_without_embeddings(session, insight_type, limit)
    total_insights = len(insights)

    if total_insights == 0:
        print(f"\n✅ All {insight_type}s already have embeddings!")
        session.close()
        return

    print(f"\n🔍 Found {total_insights:,} {insight_type}s without embeddings")
    print("="*60)

    # Process insights
    processed = 0
    errors = 0

    for insight in insights:
        processed += 1

        try:
            # Generate embedding
            embedding = generate_embedding(client, insight.insight_text)

            # Store as JSON string
            insight.embedding = json.dumps(embedding)
            session.commit()

            print(f"[{processed}/{total_insights}] ✅ Generated embedding for insight {insight.id}")
            print(f"  └─ Text: {insight.insight_text[:80]}...")

        except Exception as e:
            errors += 1
            print(f"[{processed}/{total_insights}] ❌ Error for insight {insight.id}: {e}")
            session.rollback()
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "="*60)
    print("✅ EMBEDDING GENERATION COMPLETE")
    print("="*60)
    print(f"Insights processed: {processed:,}")
    print(f"Embeddings generated: {processed - errors:,}")
    print(f"Errors: {errors}")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings for insights")
    parser.add_argument(
        "--type",
        type=str,
        default="pain_point",
        choices=["pain_point", "feature_request", "praise"],
        help="Type of insight to process"
    )
    parser.add_argument("--limit", type=int, help="Limit number of insights to process")

    args = parser.parse_args()

    generate_embeddings(insight_type=args.type, limit=args.limit)
