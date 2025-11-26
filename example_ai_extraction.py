#!/usr/bin/env python3
"""
Example: How to store AI-extracted insights (competitors, complaints, and use cases)

DEPRECATED: Use extraction_core.py functions instead (save_complaints, save_use_cases, save_sentiment, save_competitor_mentions)
This file is kept for backward compatibility only.
"""

from models import CompetitorMention, Complaint, UseCase, RedditContent, Review, get_session
from datetime import datetime

def save_extraction_results(source_id: str, source_table: str, ai_response: dict):
    """
    Save all AI-extracted insights from a single content item

    DEPRECATED: Use extraction_core.py functions instead

    Args:
        source_id: ID of the source content (e.g., "t3_xyz" for Reddit, review_id for reviews)
        source_table: Source table name (e.g., "reddit_content", "reviews", "youtube_videos")
        ai_response: AI extraction response with structure:
            {
                "competitors_mentioned": ["Spokenly", "Superwhisper"],
                "sentiment_score": 4,
                "complaints": [
                    {"complaint": "No local model support", "quote": "..."},
                    {"complaint": "Too expensive", "quote": "..."}
                ],
                "use_cases": [
                    {"use_case": "Writing emails", "quote": "..."},
                    {"use_case": "Taking notes", "quote": "..."}
                ]
            }
    """
    session = get_session()

    try:
        # 1. Save sentiment score to source table
        if source_table == "reddit_content":
            content = session.query(RedditContent).filter(RedditContent.id == source_id).first()
            if content:
                content.sentiment_score = ai_response.get("sentiment_score")
                content.ai_processed = True  # Mark as processed
                print(f"✓ Updated sentiment_score for {source_id}")
        elif source_table == "reviews":
            review = session.query(Review).filter(Review.review_id == source_id).first()
            if review:
                review.sentiment_score = ai_response.get("sentiment_score")
                review.ai_processed = True  # Mark as processed
                print(f"✓ Updated sentiment_score for {source_id} (actual rating: {review.rating}, AI sentiment: {review.sentiment_score})")

        # 2. Save competitor mentions
        # Remove existing mentions first
        session.query(CompetitorMention).filter(
            CompetitorMention.source_id == source_id,
            CompetitorMention.source_table == source_table
        ).delete()

        competitors = ai_response.get("competitors_mentioned", [])
        for competitor_name in competitors:
            mention = CompetitorMention(
                competitor_name=competitor_name,
                source_id=source_id,
                source_table=source_table
            )
            session.add(mention)

        if competitors:
            print(f"✓ Saved {len(competitors)} competitor mentions")

        # 3. Save complaints
        # Remove existing complaints first
        session.query(Complaint).filter(
            Complaint.source_id == source_id,
            Complaint.source_table == source_table
        ).delete()

        complaints = ai_response.get("complaints", [])
        for complaint_data in complaints:
            complaint = Complaint(
                complaint=complaint_data["complaint"],
                quote=complaint_data["quote"],
                source_id=source_id,
                source_table=source_table
            )
            session.add(complaint)

        if complaints:
            print(f"✓ Saved {len(complaints)} complaints")

        # 4. Save use cases
        # Remove existing use cases first
        session.query(UseCase).filter(
            UseCase.source_id == source_id,
            UseCase.source_table == source_table
        ).delete()

        use_cases = ai_response.get("use_cases", [])
        for use_case_data in use_cases:
            use_case = UseCase(
                use_case=use_case_data["use_case"],
                quote=use_case_data["quote"],
                source_id=source_id,
                source_table=source_table
            )
            session.add(use_case)

        if use_cases:
            print(f"✓ Saved {len(use_cases)} use cases")

        session.commit()
        print(f"✓ Successfully saved all insights for {source_id}")

    except Exception as e:
        session.rollback()
        print(f"✗ Error saving extraction results: {e}")

    finally:
        session.close()


def example_usage():
    """Example of how to use the AI extraction storage"""

    print("="*80)
    print("EXAMPLE: Storing AI Extraction Results")
    print("="*80)

    # Example 1: Reddit post with multiple competitors and complaints
    print("\n1. Reddit Post Example:")
    reddit_ai_response = {
        "competitors_mentioned": ["Spokenly", "Superwhisper", "VoiceInk"],
        "sentiment_score": 2,
        "complaints": [
            {
                "complaint": "Poor Bluetooth support",
                "quote": "it doesn't work well with my AirPods at all"
            },
            {
                "complaint": "No local model support",
                "quote": "I wish it could run locally without cloud"
            },
            {
                "complaint": "Too expensive",
                "quote": "the subscription is just too pricey for what it offers"
            }
        ]
    }

    reddit_id = "t3_example123"
    save_extraction_results(
        source_id=reddit_id,
        source_table="reddit_content",
        ai_response=reddit_ai_response
    )

    # Example 2: App Store Review
    print("\n2. App Store Review Example:")
    review_ai_response = {
        "competitors_mentioned": ["Dragon NaturallySpeaking"],
        "sentiment_score": 4,
        "complaints": [
            {
                "complaint": "Occasional lag",
                "quote": "sometimes there's a slight delay in transcription"
            }
        ]
    }

    review_id = "review_456"
    save_extraction_results(
        source_id=review_id,
        source_table="reviews",
        ai_response=review_ai_response
    )

    # Query and analyze the data
    print("\n" + "="*80)
    print("ANALYTICS: Query Stored Insights")
    print("="*80)

    session = get_session()

    # 1. Top competitors
    print("\n1. Top Competitors Mentioned:")
    from sqlalchemy import func

    top_competitors = session.query(
        CompetitorMention.competitor_name,
        func.count(CompetitorMention.id).label('count')
    ).group_by(
        CompetitorMention.competitor_name
    ).order_by(
        func.count(CompetitorMention.id).desc()
    ).all()

    for competitor, count in top_competitors:
        print(f"   - {competitor:20} ({count} mentions)")

    # 2. Top complaints
    print("\n2. Top Complaints:")

    top_complaints = session.query(
        Complaint.complaint,
        func.count(Complaint.id).label('count')
    ).group_by(
        Complaint.complaint
    ).order_by(
        func.count(Complaint.id).desc()
    ).all()

    for complaint, count in top_complaints:
        print(f"   - {complaint:40} ({count} times)")

    # 3. Complaints by source
    print("\n3. Complaints by Source:")

    complaints_by_source = session.query(
        Complaint.source_table,
        func.count(Complaint.id).label('count')
    ).group_by(
        Complaint.source_table
    ).all()

    for source, count in complaints_by_source:
        print(f"   - {source:20} ({count} complaints)")

    # 4. Content with negative sentiment (Reddit only)
    print("\n4. Reddit Content with Negative Sentiment (1-2):")

    negative_content = session.query(RedditContent).filter(
        RedditContent.sentiment_score.in_([1, 2])
    ).limit(5).all()

    for content in negative_content:
        print(f"   - {content.id}: sentiment={content.sentiment_score}")

    # Clean up example data
    print("\n" + "="*80)
    print("Cleaning up example data...")
    print("="*80)

    session.query(CompetitorMention).filter(
        CompetitorMention.source_id.in_([reddit_id, review_id])
    ).delete(synchronize_session=False)

    session.query(Complaint).filter(
        Complaint.source_id.in_([reddit_id, review_id])
    ).delete(synchronize_session=False)

    # Reset sentiment scores
    content = session.query(RedditContent).filter(RedditContent.id == reddit_id).first()
    if content:
        content.sentiment_score = None

    session.commit()
    print("✓ Example data cleaned up")

    session.close()


if __name__ == "__main__":
    example_usage()
