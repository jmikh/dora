#!/usr/bin/env python3
"""
Extract Magic Moments from Reviews and Reddit

Extract extreme emotional reactions for marketing purposes.
Processes content in batches of 10 for efficiency.

Usage:
    # Extract from 5-star reviews
    python extract_magic_moments.py --source reviews --limit 50

    # Extract from Reddit posts with sentiment 5
    python extract_magic_moments.py --source reddit --limit 50

    # Extract from all sources
    python extract_magic_moments.py --source all --limit 50
"""

import argparse
import json
import os
from typing import Optional, List

from dotenv import load_dotenv
from openai import OpenAI

from models import Review, RedditContent, MagicMoment, Company, get_session
from extraction_core import load_prompt, call_llm

# Load environment variables
load_dotenv()


def format_reviews_batch(reviews: List[Review]) -> str:
    """Format a batch of reviews for the prompt"""
    formatted = []
    for review in reviews:
        formatted.append(f"""Review ID: {review.review_id}
Rating: {review.rating} stars
Text: {review.review_text or '(no text)'}
""")
    return "\n---\n".join(formatted)


def format_reddit_batch(content_list: List[RedditContent]) -> str:
    """Format a batch of Reddit content for the prompt"""
    formatted = []
    for content in content_list:
        text = content.body or ''
        if content.content_type == 'post' and content.title:
            text = f"Title: {content.title}\nBody: {text}"
        formatted.append(f"""Content ID: {content.id}
Type: {content.content_type}
{text}
""")
    return "\n---\n".join(formatted)


def save_magic_moments_reviews(magic_moments: List[dict], session) -> int:
    """Save magic moments from reviews to database"""
    saved = 0
    for mm in magic_moments:
        magic_moment = MagicMoment(
            quote=mm["quote"],
            source_id=mm["review_id"],
            source_table="reviews"
        )
        session.add(magic_moment)
        saved += 1
    return saved


def save_magic_moments_reddit(magic_moments: List[dict], session) -> int:
    """Save magic moments from Reddit to database"""
    saved = 0
    for mm in magic_moments:
        magic_moment = MagicMoment(
            quote=mm["quote"],
            source_id=mm["content_id"],
            source_table="reddit_content"
        )
        session.add(magic_moment)
        saved += 1
    return saved


def extract_from_reviews(
    company_name: str,
    limit: Optional[int] = None,
    batch_size: int = 10,
    verbose: bool = False
):
    """Extract magic moments from 5-star reviews in batches"""
    print("\n" + "="*80)
    print("EXTRACTING MAGIC MOMENTS FROM 5-STAR REVIEWS")
    print("="*80)

    session = get_session()
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found")
        session.close()
        return

    prompt_template = load_prompt("prompts/magic_moments/review.md")
    print("Loaded review prompt")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)

    # Query 5-star reviews not yet processed
    query = session.query(Review).filter(
        Review.company_id == company.id,
        Review.rating == 5,
        (Review.magic_moments_processed == False) | (Review.magic_moments_processed.is_(None))
    )

    total = query.count()
    to_process = min(limit, total) if limit else total

    print(f"Found {total} 5-star reviews (processing: {to_process})")

    if to_process == 0:
        print("No reviews to process")
        session.close()
        return

    processed = 0
    total_magic_moments = 0
    batch_num = 0

    while processed < to_process:
        batch_num += 1
        current_batch_size = min(batch_size, to_process - processed)

        reviews = session.query(Review).filter(
            Review.company_id == company.id,
            Review.rating == 5,
            (Review.magic_moments_processed == False) | (Review.magic_moments_processed.is_(None))
        ).limit(current_batch_size).all()

        if not reviews:
            break

        review_ids = [r.review_id for r in reviews]

        print(f"\n{'='*80}")
        print(f"BATCH {batch_num}: Processing {len(reviews)} reviews")
        print("="*80)

        if verbose:
            for r in reviews:
                print(f"\n  [{r.review_id[:20]}...] {r.rating} stars")
                print(f"  {r.review_text[:200] if r.review_text else '(no text)'}...")

        try:
            reviews_text = format_reviews_batch(reviews)
            full_prompt = prompt_template + "\n" + reviews_text

            print("\nCalling LLM...")
            ai_response = call_llm(full_prompt, client, model="gpt-4o-mini")

            magic_moments = ai_response.get("magic_moments", [])
            num_saved = save_magic_moments_reviews(magic_moments, session)
            total_magic_moments += num_saved

            # Mark as processed
            session.query(Review).filter(
                Review.review_id.in_(review_ids)
            ).update({Review.magic_moments_processed: True}, synchronize_session=False)
            session.commit()

            print(f"\nEXTRACTED MAGIC MOMENTS ({num_saved}):")
            if magic_moments:
                for mm in magic_moments:
                    print(f"   [{mm['review_id'][:15]}...] \"{mm['quote']}\"")
            else:
                print("   (none in this batch)")

            processed += len(reviews)

        except Exception as e:
            print(f"  Error processing batch: {e}")
            session.query(Review).filter(
                Review.review_id.in_(review_ids)
            ).update({Review.magic_moments_processed: True}, synchronize_session=False)
            session.commit()
            processed += len(reviews)
            if verbose:
                raise

    session.close()
    print(f"\nReviews processed: {processed}, Magic moments found: {total_magic_moments}")


def extract_from_reddit(
    company_name: str,
    limit: Optional[int] = None,
    batch_size: int = 10,
    verbose: bool = False
):
    """Extract magic moments from Reddit posts with sentiment 5"""
    print("\n" + "="*80)
    print("EXTRACTING MAGIC MOMENTS FROM REDDIT (SENTIMENT 5)")
    print("="*80)

    session = get_session()
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found")
        session.close()
        return

    prompt_template = load_prompt("prompts/magic_moments/reddit.md")
    print("Loaded reddit prompt")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)

    # Query Reddit content with sentiment 5, exclude Wispr team, not yet processed
    query = session.query(RedditContent).filter(
        RedditContent.company_id == company.id,
        RedditContent.sentiment_score == 5,
        ~RedditContent.username.like('%AtWispr'),
        (RedditContent.magic_moments_processed == False) | (RedditContent.magic_moments_processed.is_(None))
    )

    total = query.count()
    to_process = min(limit, total) if limit else total

    print(f"Found {total} Reddit posts/comments with sentiment 5 (processing: {to_process})")

    if to_process == 0:
        print("No Reddit content to process")
        session.close()
        return

    processed = 0
    total_magic_moments = 0
    batch_num = 0

    while processed < to_process:
        batch_num += 1
        current_batch_size = min(batch_size, to_process - processed)

        content_list = session.query(RedditContent).filter(
            RedditContent.company_id == company.id,
            RedditContent.sentiment_score == 5,
            ~RedditContent.username.like('%AtWispr'),
            (RedditContent.magic_moments_processed == False) | (RedditContent.magic_moments_processed.is_(None))
        ).limit(current_batch_size).all()

        if not content_list:
            break

        content_ids = [c.id for c in content_list]

        print(f"\n{'='*80}")
        print(f"BATCH {batch_num}: Processing {len(content_list)} Reddit posts/comments")
        print("="*80)

        if verbose:
            for c in content_list:
                print(f"\n  [{c.id}] {c.content_type}")
                text = c.body[:200] if c.body else '(no text)'
                print(f"  {text}...")

        try:
            content_text = format_reddit_batch(content_list)
            full_prompt = prompt_template + "\n" + content_text

            print("\nCalling LLM...")
            ai_response = call_llm(full_prompt, client, model="gpt-4o-mini")

            magic_moments = ai_response.get("magic_moments", [])
            num_saved = save_magic_moments_reddit(magic_moments, session)
            total_magic_moments += num_saved

            # Mark as processed
            session.query(RedditContent).filter(
                RedditContent.id.in_(content_ids)
            ).update({RedditContent.magic_moments_processed: True}, synchronize_session=False)
            session.commit()

            print(f"\nEXTRACTED MAGIC MOMENTS ({num_saved}):")
            if magic_moments:
                for mm in magic_moments:
                    print(f"   [{mm['content_id']}] \"{mm['quote']}\"")
            else:
                print("   (none in this batch)")

            processed += len(content_list)

        except Exception as e:
            print(f"  Error processing batch: {e}")
            session.query(RedditContent).filter(
                RedditContent.id.in_(content_ids)
            ).update({RedditContent.magic_moments_processed: True}, synchronize_session=False)
            session.commit()
            processed += len(content_list)
            if verbose:
                raise

    session.close()
    print(f"\nReddit processed: {processed}, Magic moments found: {total_magic_moments}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract magic moments from reviews and Reddit (batch processing)"
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
        choices=["reviews", "reddit", "all"],
        help="Source to extract from (default: all)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit total number of items to process per source"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of items per batch (default: 10)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    print("="*80)
    print("MAGIC MOMENT EXTRACTION")
    print("="*80)
    print(f"Company: {args.company}")
    print(f"Source: {args.source}")
    print(f"Filters: 5-star reviews, sentiment 5 Reddit (excl. AtWispr)")
    print(f"Batch size: {args.batch_size}")
    if args.limit:
        print(f"Limit: {args.limit}")

    if args.source in ["reviews", "all"]:
        extract_from_reviews(args.company, args.limit, args.batch_size, args.verbose)

    if args.source in ["reddit", "all"]:
        extract_from_reddit(args.company, args.limit, args.batch_size, args.verbose)

    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
