#!/usr/bin/env python3
"""
Test script for review insight extraction
This demonstrates how to use the review extraction prompt
"""

from models import Review, get_session
from pathlib import Path

def load_prompt():
    """Load the review extraction prompt"""
    prompt_file = Path(__file__).parent / "review_insight_extraction_prompt.md"
    with open(prompt_file, 'r') as f:
        return f.read()

def format_review_for_extraction(review: Review) -> str:
    """
    Format a review for the extraction prompt
    NOTE: We intentionally do NOT include the rating in the prompt
    """
    return f"""**REVIEW:**

```
Title: {review.review_text.split('.')[0] if review.review_text else 'No title'}
Author: {review.user_name or 'Anonymous'}
Source: {review.source}
Date: {review.date.strftime('%Y-%m-%d')}

{review.review_text}
```
"""

def main():
    """Test the review extraction prompt with a real review"""

    print("="*80)
    print("REVIEW EXTRACTION TEST")
    print("="*80)

    # Load the prompt
    prompt = load_prompt()
    print("\n1. Loaded extraction prompt")
    print(f"   Prompt length: {len(prompt)} characters")

    # Get a review with a complaint (rating <= 3)
    session = get_session()

    print("\n2. Finding a low-rated review for testing...")
    low_rated_review = session.query(Review).filter(
        Review.rating <= 2,
        Review.review_text.isnot(None)
    ).first()

    if low_rated_review:
        print(f"   ✓ Found review: {low_rated_review.review_id[:20]}...")
        print(f"     Rating: {low_rated_review.rating} stars")
        print(f"     Source: {low_rated_review.source}")
        print(f"     Author: {low_rated_review.user_name}")
        print(f"     Text length: {len(low_rated_review.review_text)} chars")

        # Format for extraction
        formatted_review = format_review_for_extraction(low_rated_review)

        print("\n3. Formatted review for extraction:")
        print("   " + "-"*76)
        print("   " + formatted_review.replace("\n", "\n   "))
        print("   " + "-"*76)

        # Create full prompt
        full_prompt = prompt.replace("[REVIEW WILL BE PROVIDED HERE]", formatted_review)

        print(f"\n4. Full prompt ready for LLM")
        print(f"   Total length: {len(full_prompt)} characters")
        print(f"\n   NOTE: The rating ({low_rated_review.rating} stars) is NOT included in the prompt")
        print(f"         The LLM must infer sentiment from text alone")

        print("\n" + "="*80)
        print("TO USE THIS PROMPT:")
        print("="*80)
        print("1. Send 'full_prompt' to your LLM (Claude, GPT, etc.)")
        print("2. LLM will return JSON with competitors, sentiment_score, complaints")
        print("3. Use save_extraction_results() to save to database")
        print("4. Compare ai_response['sentiment_score'] to actual rating")
        print("\nExample code:")
        print("""
    from example_ai_extraction import save_extraction_results

    # Get AI response (pseudo-code)
    ai_response = llm.complete(full_prompt)

    # Save results
    save_extraction_results(
        source_id=low_rated_review.review_id,
        source_table="reviews",
        ai_response=ai_response
    )

    # This will show comparison:
    # "actual rating: 1, AI sentiment: 2"
        """)

    # Also get a high-rated review
    print("\n" + "="*80)
    print("BONUS: High-rated review example")
    print("="*80)

    high_rated_review = session.query(Review).filter(
        Review.rating == 5,
        Review.review_text.isnot(None)
    ).first()

    if high_rated_review:
        print(f"\nFound 5-star review: {high_rated_review.review_id[:20]}...")
        print(f"Text preview: {high_rated_review.review_text[:150]}...")
        print(f"\nNOTE: Even 5-star reviews may have complaints!")
        print(f"      The LLM should extract any complaints mentioned,")
        print(f"      even if overall sentiment is positive.")

    session.close()

if __name__ == "__main__":
    main()
