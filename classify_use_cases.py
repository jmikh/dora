#!/usr/bin/env python3
"""
Classify use cases into predefined categories using OpenAI LLM
"""

import os
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy import and_
from dotenv import load_dotenv
from datetime import datetime

from models import UseCase, Company, RedditContent, Review, get_session
from extraction_core import load_prompt

# Load environment variables
load_dotenv()

# Load system prompt from file
SYSTEM_PROMPT = load_prompt("prompts/use_cases/classify.md")

# User prompt template (includes both use case and quote for context)
USER_PROMPT_TEMPLATE = """Categorize this use case:

**Use Case:** {use_case}

**Quote from user:** "{quote}"

Return the category name exactly as listed (including lowercase) and your confidence level (0.0 to 1.0)."""


class UseCaseCategory(BaseModel):
    """Structured output for use case categorization"""
    category: Literal[
        # Communication
        "writing emails",
        "sending messages",
        "social media",
        # Productivity & Work
        "taking notes",
        "writing documentation",
        "writing reports",
        "task management",
        "braindump and creative thinking",
        "journaling",
        # Coding & Development
        "vibe coding",
        # Content Creation
        "writing articles",
        "creative writing",
        "academic writing",
        # Context-Based
        "dictating while driving",
        "dictating while walking",
        "dictating in meetings",
        "working hands-free",
        # AI & Assistants
        "prompting AI assistants",
        "voice search",
        # Other
        "other"
    ] = Field(
        description="The specific category this use case belongs to"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0. Use >0.90 only for clear single-category matches"
    )
    reasoning: str = Field(
        description="Brief 1-sentence explanation of why this category was chosen"
    )


def classify_use_case(client: OpenAI, use_case: str, quote: str) -> UseCaseCategory:
    """
    Classify a single use case using OpenAI

    Args:
        client: OpenAI client instance
        use_case: The use case text
        quote: The exact quote from the user

    Returns:
        UseCaseCategory with category, confidence, and reasoning
    """
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                use_case=use_case,
                quote=quote
            )}
        ],
        response_format=UseCaseCategory,
    )

    result = completion.choices[0].message.parsed

    # Enforce confidence threshold: <0.90 → "other"
    if result.category != "other" and result.confidence < 0.90:
        original_category = result.category
        result.category = "other"
        result.reasoning = f"Low confidence ({result.confidence:.2f}) for '{original_category}' - moved to 'other'"

    return result


def classify_use_cases(
    company_name: str,
    limit: int = None,
    force: bool = False,
    reclassify_category: str = None
) -> None:
    """
    Classify all use cases for a company

    Args:
        company_name: Company name to filter use cases
        limit: Maximum number to process
        force: Reclassify even if already classified
        reclassify_category: Re-classify only use cases currently in this category (e.g., "other")
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Create database session
    session = get_session()
    print(f"Connected to database")
    print(f"Company: {company_name}")

    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found in database")
        session.close()
        return

    print(f"Found company (ID: {company.id})")

    # Get use case IDs for this company from both Reddit and Reviews
    reddit_use_case_ids = (
        session.query(UseCase.id)
        .join(RedditContent, and_(
            UseCase.source_id == RedditContent.id,
            UseCase.source_table == 'reddit_content'
        ))
        .filter(RedditContent.company_id == company.id)
        .distinct()
    )

    review_use_case_ids = (
        session.query(UseCase.id)
        .join(Review, and_(
            UseCase.source_id == Review.review_id,
            UseCase.source_table == 'reviews'
        ))
        .filter(Review.company_id == company.id)
        .distinct()
    )

    # Combine use case IDs
    all_use_case_ids = set()
    for uid_tuple in reddit_use_case_ids.all():
        all_use_case_ids.add(uid_tuple[0])
    for uid_tuple in review_use_case_ids.all():
        all_use_case_ids.add(uid_tuple[0])

    if not all_use_case_ids:
        print(f"No use cases found for company '{company_name}'")
        session.close()
        return

    # Load use cases
    use_cases = session.query(UseCase).filter(UseCase.id.in_(all_use_case_ids)).all()

    # Filter based on reclassify_category or force flag
    import sqlite3
    conn = sqlite3.connect("dora.db")
    cursor = conn.cursor()

    if reclassify_category:
        # Re-classify only use cases in specific category
        print(f"Re-classifying use cases in category: \"{reclassify_category}\"")
        cursor.execute(
            "SELECT use_case_id FROM use_case_categories WHERE category = ?",
            (reclassify_category,)
        )
        reclassify_ids = {row[0] for row in cursor.fetchall()}
        use_cases = [uc for uc in use_cases if uc.id in reclassify_ids]
        print(f"Found {len(reclassify_ids)} use cases to re-classify")

    elif not force:
        # Filter out already classified
        cursor.execute("SELECT use_case_id FROM use_case_categories")
        classified_ids = {row[0] for row in cursor.fetchall()}
        use_cases = [uc for uc in use_cases if uc.id not in classified_ids]

    conn.close()

    if limit:
        use_cases = use_cases[:limit]

    total = len(use_cases)

    if total == 0:
        print(f"\nAll use cases already classified!")
        print("Use --force to reclassify")
        session.close()
        return

    print(f"\nFound {total:,} use cases to classify")
    print("=" * 80)

    # Process use cases
    processed = 0
    errors = 0
    category_counts = {}

    for use_case in use_cases:
        processed += 1

        try:
            # Classify use case
            result = classify_use_case(client, use_case.use_case, use_case.quote)

            # Track category counts
            category_counts[result.category] = category_counts.get(result.category, 0) + 1

            # Store in database
            import sqlite3
            conn = sqlite3.connect("dora.db")
            cursor = conn.cursor()

            if reclassify_category:
                # UPDATE existing row when reclassifying
                cursor.execute("""
                    UPDATE use_case_categories
                    SET category = ?, confidence = ?, reasoning = ?, classified_at = CURRENT_TIMESTAMP
                    WHERE use_case_id = ?
                """, (result.category, result.confidence, result.reasoning, use_case.id))
            elif force:
                # Delete existing classification and insert new one
                cursor.execute(
                    "DELETE FROM use_case_categories WHERE use_case_id = ?",
                    (use_case.id,)
                )
                cursor.execute("""
                    INSERT INTO use_case_categories (use_case_id, category, confidence, reasoning)
                    VALUES (?, ?, ?, ?)
                """, (use_case.id, result.category, result.confidence, result.reasoning))
            else:
                # INSERT new row for unclassified use cases
                cursor.execute("""
                    INSERT INTO use_case_categories (use_case_id, category, confidence, reasoning)
                    VALUES (?, ?, ?, ?)
                """, (use_case.id, result.category, result.confidence, result.reasoning))

            conn.commit()
            conn.close()

            print(f"[{processed}/{total}] {result.category} (conf: {result.confidence:.2f})")
            print(f"  {use_case.use_case}")

        except Exception as e:
            errors += 1
            print(f"[{processed}/{total}] Error: {e}")
            print(f"  {use_case.use_case}")
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "=" * 80)
    print("CLASSIFICATION COMPLETE")
    print("=" * 80)
    print(f"Use cases processed: {processed:,}")
    print(f"Successfully classified: {processed - errors:,}")
    print(f"Errors: {errors}")
    print("\nCategory distribution:")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify use cases using OpenAI LLM")
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'wispr')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of use cases to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reclassify even if already classified"
    )
    parser.add_argument(
        "--reclassify-category",
        type=str,
        help="Re-classify only use cases currently in this category (e.g., 'other')"
    )

    args = parser.parse_args()

    classify_use_cases(
        company_name=args.company,
        limit=args.limit,
        force=args.force,
        reclassify_category=args.reclassify_category
    )
