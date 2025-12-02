#!/usr/bin/env python3
"""
Extract Value Drivers from Reddit and Reviews

Extract value drivers (WHY users love Wispr) from content with 4+ star ratings or sentiment.

Usage:
    # Extract from reviews with 4+ stars
    python extract_value_drivers.py --source reviews --limit 10

    # Extract from Reddit with 4+ sentiment
    python extract_value_drivers.py --source reddit --limit 10

    # Extract from all sources
    python extract_value_drivers.py --source all --limit 10
"""

import argparse
import json
import os
from typing import Optional, Literal

from dotenv import load_dotenv
from openai import OpenAI

from models import RedditContent, Review, get_session, Company
from extraction_core import (
    load_prompt,
    call_llm,
    save_value_drivers,
    format_post_for_prompt,
    format_comment_for_prompt,
    format_review_for_prompt
)

# Load environment variables
load_dotenv()


def extract_from_reddit(
    company_name: str,
    limit: Optional[int] = None,
    verbose: bool = False
):
    """
    Extract value drivers from Reddit content with 4+ sentiment

    Args:
        company_name: Company name to filter content
        limit: Optional limit on number of records to process
        verbose: If True, print detailed output
    """
    print("\n" + "="*80)
    print("EXTRACTING VALUE DRIVERS FROM REDDIT")
    print("="*80)

    # Get company
    session = get_session()
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found")
        session.close()
        return

    # Load prompts
    post_prompt = load_prompt("prompts/value_drivers/reddit_post.md")
    comment_prompt = load_prompt("prompts/value_drivers/reddit_comment.md")
    print("Loaded value_drivers prompts")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized")

    # Query Reddit content with 4+ sentiment, not yet processed for value_drivers
    query = session.query(RedditContent).filter(
        RedditContent.company_id == company.id,
        RedditContent.sentiment_score >= 4,
        (RedditContent.value_drivers_processed == False) | (RedditContent.value_drivers_processed.is_(None))
    )

    # Exclude Wispr team members
    query = query.filter(
        ~RedditContent.username.like('%AtWispr')
    )

    total = query.count()
    if limit:
        query = query.limit(limit)
        to_process = min(limit, total)
    else:
        to_process = total

    records = query.all()

    print(f"Found {total} records with sentiment >= 4 (processing: {to_process})")

    if to_process == 0:
        print("No records to process")
        session.close()
        return

    # Process records
    for idx, record in enumerate(records, 1):
        print(f"\n{'='*80}")
        print(f"[{idx}/{to_process}] Processing {record.content_type} {record.id}")
        print(f"Sentiment: {record.sentiment_score}")
        print("="*80)

        try:
            # Format content based on type
            if record.content_type == "post":
                content = format_post_for_prompt(record)
                full_prompt = post_prompt + "\n\n" + content

                print("\nPOST CONTENT:")
                if record.title:
                    print(f"   Title: {record.title}")
                if record.body:
                    print(f"   Body: {record.body}")
            else:
                content = format_comment_for_prompt(record, session)
                full_prompt = comment_prompt + "\n\n" + content

                print("\nCOMMENT CONTENT:")
                if record.body:
                    print(f"   {record.body}")

            # Call LLM
            print("\nCalling LLM...")
            ai_response = call_llm(full_prompt, client, model="gpt-5-mini")

            value_drivers = ai_response.get("value_drivers", [])
            num_saved = save_value_drivers(record.id, "reddit_content", value_drivers, mark_processed=True)

            print(f"\nEXTRACTED VALUE DRIVERS ({num_saved}):")
            if value_drivers:
                for i, vd in enumerate(value_drivers, 1):
                    # Handle both old format (value_driver) and new format (category)
                    if "category" in vd:
                        category = vd["category"]
                        if category == "other" and "other_description" in vd:
                            print(f"   {i}. other: {vd['other_description']}")
                        else:
                            print(f"   {i}. {category}")
                    else:
                        print(f"   {i}. {vd.get('value_driver', 'unknown')}")
                    print(f"      Quote: \"{vd['quote']}\"")
            else:
                print("   (none)")

            if verbose:
                print("\nFull LLM Response:")
                print(json.dumps(ai_response, indent=2))

        except Exception as e:
            print(f"  Error: {e}")
            if verbose:
                raise

    session.close()
    print(f"\nCompleted Reddit extraction ({to_process} records)")


def extract_from_reviews(
    company_name: str,
    limit: Optional[int] = None,
    verbose: bool = False
):
    """
    Extract value drivers from reviews with 4+ stars

    Args:
        company_name: Company name to filter content
        limit: Optional limit on number of records to process
        verbose: If True, print detailed output
    """
    print("\n" + "="*80)
    print("EXTRACTING VALUE DRIVERS FROM REVIEWS")
    print("="*80)

    # Get company
    session = get_session()
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found")
        session.close()
        return

    # Load prompt
    review_prompt = load_prompt("prompts/value_drivers/review.md")
    print("Loaded value_drivers prompt")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized")

    # Query reviews with 4+ stars, not yet processed for value_drivers
    query = session.query(Review).filter(
        Review.company_id == company.id,
        Review.rating >= 4,
        (Review.value_drivers_processed == False) | (Review.value_drivers_processed.is_(None))
    )

    total = query.count()
    if limit:
        query = query.limit(limit)
        to_process = min(limit, total)
    else:
        to_process = total

    reviews = query.all()

    print(f"Found {total} reviews with rating >= 4 (processing: {to_process})")

    if to_process == 0:
        print("No reviews to process")
        session.close()
        return

    # Process reviews
    for idx, review in enumerate(reviews, 1):
        print(f"\n{'='*80}")
        print(f"[{idx}/{to_process}] Processing review {review.review_id[:20]}... ({review.rating} stars)")
        print("="*80)

        try:
            # Format review for prompt
            content = format_review_for_prompt(review)
            full_prompt = review_prompt + "\n\n" + content

            print("\nREVIEW CONTENT:")
            print(f"   Rating: {review.rating} stars")
            print(f"   Source: {review.source}")
            if review.review_text:
                print(f"   Text: {review.review_text}")

            # Call LLM
            print("\nCalling LLM...")
            ai_response = call_llm(full_prompt, client, model="gpt-5-mini")

            value_drivers = ai_response.get("value_drivers", [])
            num_saved = save_value_drivers(review.review_id, "reviews", value_drivers, mark_processed=True)

            print(f"\nEXTRACTED VALUE DRIVERS ({num_saved}):")
            if value_drivers:
                for i, vd in enumerate(value_drivers, 1):
                    # Handle both old format (value_driver) and new format (category)
                    if "category" in vd:
                        category = vd["category"]
                        if category == "other" and "other_description" in vd:
                            print(f"   {i}. other: {vd['other_description']}")
                        else:
                            print(f"   {i}. {category}")
                    else:
                        print(f"   {i}. {vd.get('value_driver', 'unknown')}")
                    print(f"      Quote: \"{vd['quote']}\"")
            else:
                print("   (none)")

            if verbose:
                print("\nFull LLM Response:")
                print(json.dumps(ai_response, indent=2))

        except Exception as e:
            print(f"  Error: {e}")
            if verbose:
                raise

    session.close()
    print(f"\nCompleted review extraction ({to_process} records)")


def main():
    parser = argparse.ArgumentParser(
        description="Extract value drivers from Reddit and Reviews (4+ rating/sentiment)"
    )

    parser.add_argument(
        "--company",
        type=str,
        default="wispr",
        help="Company name (default: wispr)"
    )

    parser.add_argument(
        "--source",
        type=str,
        default="all",
        choices=["reddit", "reviews", "all"],
        help="Source to extract from (default: all)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of records to process"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    print("="*80)
    print("VALUE DRIVER EXTRACTION")
    print("="*80)
    print(f"Company: {args.company}")
    print(f"Source: {args.source}")
    print("Filter: 4+ stars (reviews) or 4+ sentiment (reddit)")
    if args.limit:
        print(f"Limit: {args.limit}")

    # Extract from requested sources
    if args.source in ["reddit", "all"]:
        extract_from_reddit(args.company, args.limit, args.verbose)

    if args.source in ["reviews", "all"]:
        extract_from_reviews(args.company, args.limit, args.verbose)

    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
