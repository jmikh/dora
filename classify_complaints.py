#!/usr/bin/env python3
"""
Classify complaints into predefined categories using OpenAI LLM
"""

import os
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy import and_
from dotenv import load_dotenv
from datetime import datetime

from models import Complaint, Company, RedditContent, Review, get_session
from extraction_core import load_prompt

# Load environment variables
load_dotenv()

# Load system prompt from file
SYSTEM_PROMPT = load_prompt("prompts/complaints/classify.md")

# User prompt template (includes both complaint and quote for context)
USER_PROMPT_TEMPLATE = """Categorize this complaint:

**Complaint:** {complaint}

**Quote from user:** "{quote}"

Return the category name exactly as listed (including lowercase) and your confidence level (0.0 to 1.0)."""


class ComplaintCategory(BaseModel):
    """Structured output for complaint categorization"""
    category: Literal[
        "lag in starting recording",
        "latency in transcription",
        "no dark mode",
        "customer support not responsive",
        "too expensive",
        "microphone runs in the background",
        "drains battery or high cpu usage",
        "freezes and crashes",
        "no offline or local model",
        "issues with command mode",
        "accuracy issues",
        "AI/Smart formatting issues",
        "privacy concerns",
        "language detection issues",
        "punctuation issues",
        "mobile keyboard issues",
        "hotkey issues",
        "reliability and performance problems",
        "subscription problems",
        "customization issues",
        "authentication and login issues",
        "onboarding issues",
        "microphone compatibility issues",
        "lack of Android version",
        "lack of public roadmap or feature requests",
        "no better than competitors",
        "issues related to updates",
        "difficult to use",
        "other"
    ] = Field(
        description="The specific category this complaint belongs to"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0. Use >0.95 only for crystal-clear single-category matches"
    )
    reasoning: str = Field(
        description="Brief 1-sentence explanation of why this category was chosen"
    )


def classify_complaint(client: OpenAI, complaint: str, quote: str) -> ComplaintCategory:
    """
    Classify a single complaint using OpenAI

    Args:
        client: OpenAI client instance
        complaint: The normalized complaint text
        quote: The exact quote from the user

    Returns:
        ComplaintCategory with category, confidence, and reasoning
    """
    completion = client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                complaint=complaint,
                quote=quote
            )}
        ],
        response_format=ComplaintCategory,
    )

    result = completion.choices[0].message.parsed

    # Enforce confidence threshold: <0.95 → "other"
    if result.category != "other" and result.confidence < 0.95:
        original_category = result.category
        result.category = "other"
        result.reasoning = f"Low confidence ({result.confidence:.2f}) for '{original_category}' - moved to 'other'"

    return result


def classify_complaints(
    company_name: str,
    limit: int = None,
    force: bool = False,
    reclassify_category: str = None
) -> None:
    """
    Classify all complaints for a company

    Args:
        company_name: Company name to filter complaints
        limit: Maximum number to process
        force: Reclassify even if already classified
        reclassify_category: Re-classify only complaints currently in this category (e.g., "other")
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

    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"❌ Company '{company_name}' not found in database")
        session.close()
        return

    print(f"✓ Found company (ID: {company.id})")

    # Get complaint IDs for this company from both Reddit and Reviews
    reddit_complaint_ids = (
        session.query(Complaint.id)
        .join(RedditContent, and_(
            Complaint.source_id == RedditContent.id,
            Complaint.source_table == 'reddit_content'
        ))
        .filter(RedditContent.company_id == company.id)
        .distinct()
    )

    review_complaint_ids = (
        session.query(Complaint.id)
        .join(Review, and_(
            Complaint.source_id == Review.review_id,
            Complaint.source_table == 'reviews'
        ))
        .filter(Review.company_id == company.id)
        .distinct()
    )

    # Combine complaint IDs
    all_complaint_ids = set()
    for cid_tuple in reddit_complaint_ids.all():
        all_complaint_ids.add(cid_tuple[0])
    for cid_tuple in review_complaint_ids.all():
        all_complaint_ids.add(cid_tuple[0])

    if not all_complaint_ids:
        print(f"❌ No complaints found for company '{company_name}'")
        session.close()
        return

    # Load complaints
    complaints = session.query(Complaint).filter(Complaint.id.in_(all_complaint_ids)).all()

    # Filter based on reclassify_category or force flag
    import sqlite3
    conn = sqlite3.connect("dora.db")
    cursor = conn.cursor()

    if reclassify_category:
        # Re-classify only complaints in specific category
        print(f"🔄 Re-classifying complaints in category: \"{reclassify_category}\"")
        cursor.execute(
            "SELECT complaint_id FROM complaint_categories WHERE category = ?",
            (reclassify_category,)
        )
        reclassify_ids = {row[0] for row in cursor.fetchall()}
        complaints = [c for c in complaints if c.id in reclassify_ids]
        print(f"   Found {len(reclassify_ids)} complaints to re-classify")

    elif not force:
        # Filter out already classified
        cursor.execute("SELECT complaint_id FROM complaint_categories")
        classified_ids = {row[0] for row in cursor.fetchall()}
        complaints = [c for c in complaints if c.id not in classified_ids]

    conn.close()

    if limit:
        complaints = complaints[:limit]

    total = len(complaints)

    if total == 0:
        print(f"\n✅ All complaints already classified!")
        print("Use --force to reclassify")
        session.close()
        return

    print(f"\n🔍 Found {total:,} complaints to classify")
    print("="*80)

    # Process complaints
    processed = 0
    errors = 0
    category_counts = {}

    for complaint in complaints:
        processed += 1

        try:
            # Classify complaint
            result = classify_complaint(client, complaint.complaint, complaint.quote)

            # Track category counts
            category_counts[result.category] = category_counts.get(result.category, 0) + 1

            # Store in database
            import sqlite3
            conn = sqlite3.connect("dora.db")
            cursor = conn.cursor()

            if reclassify_category:
                # UPDATE existing row when reclassifying
                cursor.execute("""
                    UPDATE complaint_categories
                    SET category = ?, confidence = ?, reasoning = ?, classified_at = CURRENT_TIMESTAMP
                    WHERE complaint_id = ?
                """, (result.category, result.confidence, result.reasoning, complaint.id))
            elif force:
                # Delete existing classification and insert new one
                cursor.execute(
                    "DELETE FROM complaint_categories WHERE complaint_id = ?",
                    (complaint.id,)
                )
                cursor.execute("""
                    INSERT INTO complaint_categories (complaint_id, category, confidence, reasoning)
                    VALUES (?, ?, ?, ?)
                """, (complaint.id, result.category, result.confidence, result.reasoning))
            else:
                # INSERT new row for unclassified complaints
                cursor.execute("""
                    INSERT INTO complaint_categories (complaint_id, category, confidence, reasoning)
                    VALUES (?, ?, ?, ?)
                """, (complaint.id, result.category, result.confidence, result.reasoning))

            conn.commit()
            conn.close()

            print(f"[{processed}/{total}] ✅ {result.category} (conf: {result.confidence:.2f})")
            print(f"  └─ {complaint.complaint}")

        except Exception as e:
            errors += 1
            print(f"[{processed}/{total}] ❌ Error: {e}")
            print(f"  └─ {complaint.complaint}")
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "="*80)
    print("✅ CLASSIFICATION COMPLETE")
    print("="*80)
    print(f"Complaints processed: {processed:,}")
    print(f"Successfully classified: {processed - errors:,}")
    print(f"Errors: {errors}")
    print("\nCategory distribution:")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")
    print("="*80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify complaints using OpenAI LLM")
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'wispr')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of complaints to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reclassify even if already classified"
    )
    parser.add_argument(
        "--reclassify-category",
        type=str,
        help="Re-classify only complaints currently in this category (e.g., 'other')"
    )

    args = parser.parse_args()

    classify_complaints(
        company_name=args.company,
        limit=args.limit,
        force=args.force,
        reclassify_category=args.reclassify_category
    )
