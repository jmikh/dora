#!/usr/bin/env python3
"""
Unified Content Extraction CLI

Extract complaints and/or use cases from Reddit and Reviews using OpenAI LLM.

Usage:
    # Extract complaints from all sources
    python extract_content.py --company wispr --type complaints --limit 10

    # Extract use cases from Reddit only
    python extract_content.py --company wispr --type use_cases --source reddit --limit 5

    # Extract both complaints and use cases
    python extract_content.py --company wispr --type both --limit 10
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
    save_complaints,
    save_use_cases,
    save_sentiment,
    save_competitor_mentions,
    format_post_for_prompt,
    format_comment_for_prompt,
    format_review_for_prompt
)

# Load environment variables
load_dotenv()


def extract_from_reddit(
    company_name: str,
    extraction_type: Literal["complaints", "use_cases", "both"],
    limit: Optional[int] = None,
    verbose: bool = False
):
    """
    Extract insights from Reddit content

    Args:
        company_name: Company name to filter content
        extraction_type: What to extract (complaints, use_cases, or both)
        limit: Optional limit on number of records to process
        verbose: If True, print detailed output
    """
    print("\n" + "="*80)
    print(f"EXTRACTING {extraction_type.upper()} FROM REDDIT")
    print("="*80)

    # Get company
    session = get_session()
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"❌ Company '{company_name}' not found")
        session.close()
        return

    # Load prompts based on extraction type
    prompt_dir = "prompts/complaints" if extraction_type != "use_cases" else "prompts/use_cases"

    post_prompt = load_prompt(f"{prompt_dir}/reddit_post.md")
    comment_prompt = load_prompt(f"{prompt_dir}/reddit_comment.md")

    print(f"✓ Loaded prompts from {prompt_dir}/")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized")

    # Query unprocessed Reddit content based on extraction type
    query = session.query(RedditContent).filter(
        RedditContent.company_id == company.id
    )

    # Filter by appropriate processed flag
    if extraction_type == "complaints":
        query = query.filter(RedditContent.complaints_processed == False)
    elif extraction_type == "use_cases":
        query = query.filter(RedditContent.use_cases_processed == False)
    else:  # both
        query = query.filter(
            (RedditContent.complaints_processed == False) |
            (RedditContent.use_cases_processed == False)
        )

    total = query.count()
    if limit:
        query = query.limit(limit)
        to_process = min(limit, total)
    else:
        to_process = total

    records = query.all()

    print(f"✓ Found {total} unprocessed records (processing: {to_process})")

    if to_process == 0:
        print("✓ No records to process")
        session.close()
        return

    # Process records
    for idx, record in enumerate(records, 1):
        print(f"\n{'='*80}")
        print(f"[{idx}/{to_process}] Processing {record.content_type} {record.id[:15]}...")
        print(f"{'='*80}")

        try:
            # Format content for prompt
            if record.content_type == "post":
                content = format_post_for_prompt(record)
                full_prompt = post_prompt + "\n\n" + content

                # Print post content
                print("\n📝 POST CONTENT:")
                if record.title:
                    print(f"   Title: {record.title}")
                if record.body:
                    print(f"   Body: {record.body[:200]}{'...' if len(record.body) > 200 else ''}")
            else:
                content = format_comment_for_prompt(record, session)
                full_prompt = comment_prompt + "\n\n" + content

                # Print comment content
                print("\n💬 COMMENT CONTENT:")
                if record.body:
                    print(f"   {record.body[:200]}{'...' if len(record.body) > 200 else ''}")

            # Call LLM
            print("\n⏳ Calling LLM...")
            ai_response = call_llm(full_prompt, client, model="gpt-5-mini")

            # Save results based on extraction type
            if extraction_type in ["complaints", "both"]:
                # Save sentiment and competitors only for complaints extraction
                save_sentiment(record.id, "reddit_content", ai_response.get("sentiment_score"), mark_processed=False)
                save_competitor_mentions(record.id, "reddit_content", ai_response.get("competitors_mentioned", []))

                complaints = ai_response.get("complaints", [])
                num_complaints = save_complaints(record.id, "reddit_content", complaints, mark_processed=True)

                print(f"\n📋 EXTRACTED COMPLAINTS ({num_complaints}):")
                if complaints:
                    for i, c in enumerate(complaints, 1):
                        print(f"   {i}. {c['complaint']}")
                        print(f"      Quote: \"{c['quote'][:100]}{'...' if len(c['quote']) > 100 else ''}\"")
                else:
                    print("   (none)")

                # Print sentiment and competitors for complaints
                sentiment = ai_response.get("sentiment_score")
                competitors = ai_response.get("competitors_mentioned", [])
                print(f"\n📊 SENTIMENT: {sentiment if sentiment else 'N/A'}")
                if competitors:
                    print(f"🏢 COMPETITORS: {', '.join(competitors)}")

            if extraction_type in ["use_cases", "both"]:
                use_cases = ai_response.get("use_cases", [])
                num_use_cases = save_use_cases(record.id, "reddit_content", use_cases, mark_processed=True)

                print(f"\n🎯 EXTRACTED USE CASES ({num_use_cases}):")
                if use_cases:
                    for i, uc in enumerate(use_cases, 1):
                        print(f"   {i}. {uc['use_case']}")
                        print(f"      Quote: \"{uc['quote'][:100]}{'...' if len(uc['quote']) > 100 else ''}\"")
                else:
                    print("   (none)")

            if verbose:
                print("\n🔍 FULL LLM RESPONSE:")
                print(json.dumps(ai_response, indent=2))

        except Exception as e:
            print(f"  ❌ Error: {e}")
            if verbose:
                raise

    session.close()
    print(f"\n✓ Completed Reddit extraction ({to_process} records)")


def extract_from_reviews(
    company_name: str,
    extraction_type: Literal["complaints", "use_cases", "both"],
    limit: Optional[int] = None,
    verbose: bool = False
):
    """
    Extract insights from reviews

    Args:
        company_name: Company name to filter content
        extraction_type: What to extract (complaints, use_cases, or both)
        limit: Optional limit on number of records to process
        verbose: If True, print detailed output
    """
    print("\n" + "="*80)
    print(f"EXTRACTING {extraction_type.upper()} FROM REVIEWS")
    print("="*80)

    # Get company
    session = get_session()
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"❌ Company '{company_name}' not found")
        session.close()
        return

    # Load prompt based on extraction type
    prompt_dir = "prompts/complaints" if extraction_type != "use_cases" else "prompts/use_cases"
    review_prompt = load_prompt(f"{prompt_dir}/review.md")

    print(f"✓ Loaded prompt from {prompt_dir}/review.md")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized")

    # Query unprocessed reviews based on extraction type
    query = session.query(Review).filter(
        Review.company_id == company.id
    )

    # Filter by appropriate processed flag
    if extraction_type == "complaints":
        query = query.filter(Review.complaints_processed == False)
    elif extraction_type == "use_cases":
        query = query.filter(Review.use_cases_processed == False)
    else:  # both
        query = query.filter(
            (Review.complaints_processed == False) |
            (Review.use_cases_processed == False)
        )

    total = query.count()
    if limit:
        query = query.limit(limit)
        to_process = min(limit, total)
    else:
        to_process = total

    reviews = query.all()

    print(f"✓ Found {total} unprocessed reviews (processing: {to_process})")

    if to_process == 0:
        print("✓ No reviews to process")
        session.close()
        return

    # Process reviews
    for idx, review in enumerate(reviews, 1):
        print(f"\n{'='*80}")
        print(f"[{idx}/{to_process}] Processing review {review.review_id[:20]}... ({review.rating}★)")
        print(f"{'='*80}")

        try:
            # Format review for prompt
            content = format_review_for_prompt(review)
            full_prompt = review_prompt + "\n\n" + content

            # Print review content
            print("\n⭐ REVIEW CONTENT:")
            print(f"   Rating: {review.rating}★")
            print(f"   Source: {review.source}")
            if review.user_name:
                print(f"   Author: {review.user_name}")
            if review.review_text:
                print(f"   Text: {review.review_text[:200]}{'...' if len(review.review_text) > 200 else ''}")

            # Call LLM
            print("\n⏳ Calling LLM...")
            ai_response = call_llm(full_prompt, client, model="gpt-4o-mini")

            # Save results based on extraction type
            if extraction_type in ["complaints", "both"]:
                # Save sentiment and competitors only for complaints extraction
                save_sentiment(review.review_id, "reviews", ai_response.get("sentiment_score"), mark_processed=False)
                save_competitor_mentions(review.review_id, "reviews", ai_response.get("competitors_mentioned", []))

                complaints = ai_response.get("complaints", [])
                num_complaints = save_complaints(review.review_id, "reviews", complaints, mark_processed=True)

                print(f"\n📋 EXTRACTED COMPLAINTS ({num_complaints}):")
                if complaints:
                    for i, c in enumerate(complaints, 1):
                        print(f"   {i}. {c['complaint']}")
                        print(f"      Quote: \"{c['quote'][:100]}{'...' if len(c['quote']) > 100 else ''}\"")
                else:
                    print("   (none)")

                # Print sentiment and competitors for complaints
                sentiment = ai_response.get("sentiment_score")
                competitors = ai_response.get("competitors_mentioned", [])
                print(f"\n📊 SENTIMENT: {sentiment if sentiment else 'N/A'}")
                if competitors:
                    print(f"🏢 COMPETITORS: {', '.join(competitors)}")

            if extraction_type in ["use_cases", "both"]:
                use_cases = ai_response.get("use_cases", [])
                num_use_cases = save_use_cases(review.review_id, "reviews", use_cases, mark_processed=True)

                print(f"\n🎯 EXTRACTED USE CASES ({num_use_cases}):")
                if use_cases:
                    for i, uc in enumerate(use_cases, 1):
                        print(f"   {i}. {uc['use_case']}")
                        print(f"      Quote: \"{uc['quote'][:100]}{'...' if len(uc['quote']) > 100 else ''}\"")
                else:
                    print("   (none)")

            if verbose:
                print("\n🔍 FULL LLM RESPONSE:")
                print(json.dumps(ai_response, indent=2))

        except Exception as e:
            print(f"  ❌ Error: {e}")
            if verbose:
                raise

    session.close()
    print(f"\n✓ Completed review extraction ({to_process} records)")


def main():
    parser = argparse.ArgumentParser(
        description="Extract complaints and/or use cases from Reddit and Reviews"
    )

    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'wispr')"
    )

    parser.add_argument(
        "--type",
        type=str,
        required=True,
        choices=["complaints", "use_cases", "both"],
        help="What to extract: complaints, use_cases, or both"
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
        help="Limit number of items to process"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    print("="*80)
    print("UNIFIED CONTENT EXTRACTION")
    print("="*80)
    print(f"Company: {args.company}")
    print(f"Type: {args.type}")
    print(f"Source: {args.source}")
    if args.limit:
        print(f"Limit: {args.limit}")

    # Extract from requested sources
    if args.source in ["reddit", "all"]:
        extract_from_reddit(args.company, args.type, args.limit, args.verbose)

    if args.source in ["reviews", "all"]:
        extract_from_reviews(args.company, args.type, args.limit, args.verbose)

    print("\n" + "="*80)
    print("✓ EXTRACTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
