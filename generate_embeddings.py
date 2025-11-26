#!/usr/bin/env python3
"""
Generate embeddings for complaints or use cases using OpenAI and save to database
"""

import os
import json
from typing import List, Literal
from openai import OpenAI
from sqlalchemy import and_
from dotenv import load_dotenv

from models import (
    Complaint, ComplaintEmbedding,
    UseCase, UseCaseEmbedding,
    Company, RedditContent, Review, get_session
)

# Load environment variables
load_dotenv()


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
        model="text-embedding-3-small",  # Cost-effective, good quality (1536 dimensions)
        input=text
    )

    return response.data[0].embedding


def generate_complaint_embeddings(session, client: OpenAI, company, limit: int = None) -> None:
    """Generate embeddings for complaints"""
    # Get complaint IDs that don't have embeddings yet
    existing_complaint_ids = set(
        session.query(ComplaintEmbedding.complaint_id)
        .filter(ComplaintEmbedding.dimensions == 1536)
        .distinct()
        .all()
    )
    existing_complaint_ids = {cid[0] for cid in existing_complaint_ids}

    # Get complaints from Reddit
    reddit_complaints = (
        session.query(Complaint.id, Complaint.complaint)
        .join(RedditContent, and_(
            Complaint.source_id == RedditContent.id,
            Complaint.source_table == 'reddit_content'
        ))
        .filter(RedditContent.company_id == company.id)
        .filter(~Complaint.id.in_(existing_complaint_ids))
        .distinct()
    )

    # Get complaints from Reviews
    review_complaints = (
        session.query(Complaint.id, Complaint.complaint)
        .join(Review, and_(
            Complaint.source_id == Review.review_id,
            Complaint.source_table == 'reviews'
        ))
        .filter(Review.company_id == company.id)
        .filter(~Complaint.id.in_(existing_complaint_ids))
        .distinct()
    )

    # Combine and deduplicate by complaint text
    items_map = {}  # text -> id
    for item_id, item_text in reddit_complaints.all():
        if item_text not in items_map:
            items_map[item_text] = item_id

    for item_id, item_text in review_complaints.all():
        if item_text not in items_map:
            items_map[item_text] = item_id

    if limit:
        items = list(items_map.items())[:limit]
        items_map = dict(items)

    total = len(items_map)

    if total == 0:
        print(f"\n✅ All complaints already have embeddings!")
        return

    print(f"\n🔍 Found {total:,} unique complaints without embeddings")
    print(f"📏 Generating 1536-dimensional embeddings")
    print("=" * 60)

    # Process
    processed = 0
    errors = 0

    for item_text, item_id in items_map.items():
        processed += 1

        try:
            embedding = generate_embedding(client, item_text)

            complaint_embedding = ComplaintEmbedding(
                complaint_id=item_id,
                complaint_text=item_text,
                dimensions=1536,
                embedding=json.dumps(embedding)
            )
            session.add(complaint_embedding)
            session.commit()

            print(f"[{processed}/{total}] ✅ Generated embedding (ID: {item_id})")
            print(f"  └─ {item_text}")

        except Exception as e:
            errors += 1
            print(f"[{processed}/{total}] ❌ Error: {e}")
            print(f"  └─ {item_text}")
            session.rollback()
            continue

    print("\n" + "=" * 60)
    print("✅ COMPLAINT EMBEDDING GENERATION COMPLETE")
    print("=" * 60)
    print(f"Processed: {processed:,}")
    print(f"Generated: {processed - errors:,}")
    print(f"Errors: {errors}")
    print("=" * 60)


def generate_use_case_embeddings(session, client: OpenAI, company, limit: int = None) -> None:
    """Generate embeddings for use cases"""
    # Get use case IDs that don't have embeddings yet
    existing_use_case_ids = set(
        session.query(UseCaseEmbedding.use_case_id)
        .filter(UseCaseEmbedding.dimensions == 1536)
        .distinct()
        .all()
    )
    existing_use_case_ids = {uid[0] for uid in existing_use_case_ids}

    # Get use cases from Reddit
    reddit_use_cases = (
        session.query(UseCase.id, UseCase.use_case)
        .join(RedditContent, and_(
            UseCase.source_id == RedditContent.id,
            UseCase.source_table == 'reddit_content'
        ))
        .filter(RedditContent.company_id == company.id)
        .filter(~UseCase.id.in_(existing_use_case_ids))
        .distinct()
    )

    # Get use cases from Reviews
    review_use_cases = (
        session.query(UseCase.id, UseCase.use_case)
        .join(Review, and_(
            UseCase.source_id == Review.review_id,
            UseCase.source_table == 'reviews'
        ))
        .filter(Review.company_id == company.id)
        .filter(~UseCase.id.in_(existing_use_case_ids))
        .distinct()
    )

    # Combine and deduplicate by use case text
    items_map = {}  # text -> id
    for item_id, item_text in reddit_use_cases.all():
        if item_text not in items_map:
            items_map[item_text] = item_id

    for item_id, item_text in review_use_cases.all():
        if item_text not in items_map:
            items_map[item_text] = item_id

    if limit:
        items = list(items_map.items())[:limit]
        items_map = dict(items)

    total = len(items_map)

    if total == 0:
        print(f"\n✅ All use cases already have embeddings!")
        return

    print(f"\n🔍 Found {total:,} unique use cases without embeddings")
    print(f"📏 Generating 1536-dimensional embeddings")
    print("=" * 60)

    # Process
    processed = 0
    errors = 0

    for item_text, item_id in items_map.items():
        processed += 1

        try:
            embedding = generate_embedding(client, item_text)

            use_case_embedding = UseCaseEmbedding(
                use_case_id=item_id,
                use_case_text=item_text,
                dimensions=1536,
                embedding=json.dumps(embedding)
            )
            session.add(use_case_embedding)
            session.commit()

            print(f"[{processed}/{total}] ✅ Generated embedding (ID: {item_id})")
            print(f"  └─ {item_text}")

        except Exception as e:
            errors += 1
            print(f"[{processed}/{total}] ❌ Error: {e}")
            print(f"  └─ {item_text}")
            session.rollback()
            continue

    print("\n" + "=" * 60)
    print("✅ USE CASE EMBEDDING GENERATION COMPLETE")
    print("=" * 60)
    print(f"Processed: {processed:,}")
    print(f"Generated: {processed - errors:,}")
    print(f"Errors: {errors}")
    print("=" * 60)


def generate_embeddings(
    company_name: str,
    embedding_type: Literal["complaints", "use_cases"] = "complaints",
    limit: int = None
) -> None:
    """
    Generate full embeddings (1536D) for complaints or use cases and save to database

    Args:
        company_name: Company name to filter items
        embedding_type: Type of embeddings to generate ("complaints" or "use_cases")
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
    print(f"🏢 Company: {company_name}")
    print(f"📋 Type: {embedding_type}")

    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"❌ Company '{company_name}' not found in database")
        session.close()
        return

    print(f"✓ Found company (ID: {company.id})")

    if embedding_type == "complaints":
        generate_complaint_embeddings(session, client, company, limit)
    else:
        generate_use_case_embeddings(session, client, company, limit)

    session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings for complaints or use cases")
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'wispr')"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["complaints", "use_cases"],
        default="complaints",
        help="Type of embeddings to generate (default: complaints)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of items to process"
    )

    args = parser.parse_args()

    generate_embeddings(
        company_name=args.company,
        embedding_type=args.type,
        limit=args.limit
    )
