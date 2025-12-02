#!/usr/bin/env python3
"""
Extraction Core Module

Shared logic for extracting complaints and use cases from Reddit and Reviews
"""

import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

from models import Complaint, UseCase, RedditContent, Review, get_session


def load_prompt(prompt_path: str) -> str:
    """
    Load a prompt template from file

    Args:
        prompt_path: Relative path to prompt file from project root (e.g., "prompts/complaints/reddit_post.md")

    Returns:
        Prompt content as string
    """
    full_path = Path(__file__).parent / prompt_path

    with open(full_path, 'r') as f:
        content = f.read()

    # Check if prompt references {{COMMON_RULES}}
    if "{{COMMON_RULES}}" in content:
        # Load the corresponding common.md file
        prompt_dir = Path(prompt_path).parent
        common_path = full_path.parent / "common.md"

        if common_path.exists():
            with open(common_path, 'r') as cf:
                common_rules = cf.read()
            content = content.replace("{{COMMON_RULES}}", common_rules)

    return content


def call_llm(prompt: str, client: OpenAI, model: str = "gpt-4o-mini") -> Dict:
    """
    Call OpenAI API to extract insights

    Args:
        prompt: The complete prompt to send
        client: OpenAI client instance
        model: Model to use (default: gpt-4o-mini)

    Returns:
        Parsed JSON response from LLM
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}
    )

    result_text = response.choices[0].message.content
    return json.loads(result_text)


def save_complaints(source_id: str, source_table: str, complaints: List[Dict], mark_processed: bool = True) -> int:
    """
    Save complaints to database and mark as processed

    Args:
        source_id: ID of the source content
        source_table: Source table name (e.g., "reddit_content", "reviews")
        complaints: List of complaint dicts with "complaint" and "quote" keys
        mark_processed: Whether to mark complaints_processed=True (default: True)

    Returns:
        Number of complaints saved
    """
    session = get_session()

    try:
        # Remove existing complaints for this source
        session.query(Complaint).filter(
            Complaint.source_id == source_id,
            Complaint.source_table == source_table
        ).delete()

        # Add new complaints
        for complaint_data in complaints:
            complaint = Complaint(
                complaint=complaint_data["complaint"],
                quote=complaint_data["quote"],
                source_id=source_id,
                source_table=source_table
            )
            session.add(complaint)

        # Mark as processed (even if no complaints found)
        if mark_processed:
            if source_table == "reddit_content":
                content = session.query(RedditContent).filter(RedditContent.id == source_id).first()
                if content:
                    content.complaints_processed = True
            elif source_table == "reviews":
                review = session.query(Review).filter(Review.review_id == source_id).first()
                if review:
                    review.complaints_processed = True

        session.commit()
        return len(complaints) if complaints else 0

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_use_cases(source_id: str, source_table: str, use_cases: List[Dict], mark_processed: bool = True) -> int:
    """
    Save use cases to database and mark as processed

    Args:
        source_id: ID of the source content
        source_table: Source table name (e.g., "reddit_content", "reviews")
        use_cases: List of use case dicts with "use_case" and "quote" keys
        mark_processed: Whether to mark use_cases_processed=True (default: True)

    Returns:
        Number of use cases saved
    """
    session = get_session()

    try:
        # Remove existing use cases for this source
        session.query(UseCase).filter(
            UseCase.source_id == source_id,
            UseCase.source_table == source_table
        ).delete()

        # Add new use cases
        for use_case_data in use_cases:
            # Handle both old format (use_case) and new format (category)
            if "category" in use_case_data:
                category = use_case_data["category"]
                # For "other" category, include the description
                if category == "other" and "other_description" in use_case_data:
                    use_case_text = f"other: {use_case_data['other_description']}"
                else:
                    use_case_text = category
            else:
                use_case_text = use_case_data.get("use_case", "unknown")

            use_case = UseCase(
                use_case=use_case_text,
                quote=use_case_data["quote"],
                source_id=source_id,
                source_table=source_table
            )
            session.add(use_case)

        # Mark as processed (even if no use cases found)
        if mark_processed:
            if source_table == "reddit_content":
                content = session.query(RedditContent).filter(RedditContent.id == source_id).first()
                if content:
                    content.use_cases_processed = True
            elif source_table == "reviews":
                review = session.query(Review).filter(Review.review_id == source_id).first()
                if review:
                    review.use_cases_processed = True

        session.commit()
        return len(use_cases) if use_cases else 0

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_value_drivers(source_id: str, source_table: str, value_drivers: List[Dict], mark_processed: bool = True) -> int:
    """
    Save value drivers to database and mark as processed

    Args:
        source_id: ID of the source content
        source_table: Source table name (e.g., "reddit_content", "reviews")
        value_drivers: List of value driver dicts with "value_driver" and "quote" keys
        mark_processed: Whether to mark value_drivers_processed=True (default: True)

    Returns:
        Number of value drivers saved
    """
    from models import ValueDriver

    session = get_session()

    try:
        # Remove existing value drivers for this source
        session.query(ValueDriver).filter(
            ValueDriver.source_id == source_id,
            ValueDriver.source_table == source_table
        ).delete()

        # Add new value drivers
        for vd_data in value_drivers:
            # Handle both old format (value_driver) and new format (category)
            if "category" in vd_data:
                category = vd_data["category"]
                # For "other" category, include the description
                if category == "other" and "other_description" in vd_data:
                    value_driver_text = f"other: {vd_data['other_description']}"
                else:
                    value_driver_text = category
            else:
                value_driver_text = vd_data.get("value_driver", "unknown")

            value_driver = ValueDriver(
                value_driver=value_driver_text,
                quote=vd_data["quote"],
                source_id=source_id,
                source_table=source_table
            )
            session.add(value_driver)

        # Mark as processed (even if no value drivers found)
        if mark_processed:
            if source_table == "reddit_content":
                content = session.query(RedditContent).filter(RedditContent.id == source_id).first()
                if content:
                    content.value_drivers_processed = True
            elif source_table == "reviews":
                review = session.query(Review).filter(Review.review_id == source_id).first()
                if review:
                    review.value_drivers_processed = True

        session.commit()
        return len(value_drivers) if value_drivers else 0

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_sentiment(source_id: str, source_table: str, sentiment_score: int, mark_processed: bool = True):
    """
    Save sentiment score to source table

    Args:
        source_id: ID of the source content
        source_table: Source table name (e.g., "reddit_content", "reviews")
        sentiment_score: Sentiment score (1-5 or null)
        mark_processed: Whether to mark content as ai_processed
    """
    from models import RedditContent, Review

    session = get_session()

    try:
        if source_table == "reddit_content":
            content = session.query(RedditContent).filter(RedditContent.id == source_id).first()
            if content:
                content.sentiment_score = sentiment_score
                if mark_processed:
                    content.ai_processed = True

        elif source_table == "reviews":
            review = session.query(Review).filter(Review.review_id == source_id).first()
            if review:
                review.sentiment_score = sentiment_score
                if mark_processed:
                    review.ai_processed = True

        session.commit()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_competitor_mentions(source_id: str, source_table: str, competitors: List[str]) -> int:
    """
    Save competitor mentions to database

    Args:
        source_id: ID of the source content
        source_table: Source table name
        competitors: List of competitor names

    Returns:
        Number of competitors saved
    """
    if not competitors:
        return 0

    from models import CompetitorMention

    session = get_session()

    try:
        # Remove existing mentions
        session.query(CompetitorMention).filter(
            CompetitorMention.source_id == source_id,
            CompetitorMention.source_table == source_table
        ).delete()

        # Add new mentions
        for competitor_name in competitors:
            mention = CompetitorMention(
                competitor_name=competitor_name,
                source_id=source_id,
                source_table=source_table
            )
            session.add(mention)

        session.commit()
        return len(competitors)

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ============================================================================
# Content Formatting Functions
# ============================================================================

def get_thread_path(comment_id: str, session) -> List[RedditContent]:
    """
    Get the full path from root post to a specific comment

    Args:
        comment_id: The comment ID to get the path for
        session: Database session

    Returns:
        List of RedditContent objects from root post to target comment
    """
    path = []
    current_id = comment_id

    while current_id:
        content = session.query(RedditContent).filter(
            RedditContent.id == current_id
        ).first()

        if not content:
            break

        path.insert(0, content)

        if content.content_type == 'comment':
            current_id = content.parent_id
        else:
            break

    return path


def format_post_for_prompt(post: RedditContent) -> str:
    """Format a Reddit post for the extraction prompt"""
    output = "**POST:**\n\n```\n"

    if post.title:
        output += f"Title: {post.title}\n"
    if post.body:
        output += f"Body: {post.body}\n"

    output += f"\nCommunity: {post.community_name}\n"
    output += "```"

    return output


def format_comment_for_prompt(comment: RedditContent, session) -> str:
    """Format a Reddit comment with thread context for the extraction prompt"""
    thread_path = get_thread_path(comment.id, session)

    output = "**THREAD CONTEXT:**\n\n```\n"

    # Add all context items (everything except the target comment)
    for i, item in enumerate(thread_path[:-1]):
        prefix = "    " * i

        if item.content_type == 'post':
            output += f"{prefix}[POST - ROOT]\n"
            if item.title:
                output += f"{prefix}Title: {item.title}\n"
            if item.body:
                # Truncate long post bodies for context
                body = item.body[:300] + "..." if len(item.body) > 300 else item.body
                output += f"{prefix}Body: {body}\n"
        else:
            output += f"\n{prefix}[COMMENT - CONTEXT]\n"
            if item.body:
                output += f"{prefix}{item.body}\n"

    output += "```\n\n"
    output += "**TARGET COMMENT:**\n\n```\n"

    # Add target comment (last item in path)
    target = thread_path[-1]
    if target.body:
        output += target.body + "\n"

    output += "```"

    return output


def format_review_for_prompt(review: Review) -> str:
    """
    Format a review for the extraction prompt
    NOTE: We intentionally do NOT include the rating in the prompt
    """
    # Extract title from review text (first sentence or first 50 chars)
    title = "No title"
    if review.review_text:
        first_line = review.review_text.split('\n')[0]
        if '.' in first_line:
            title = first_line.split('.')[0]
        else:
            title = first_line[:50] if len(first_line) > 50 else first_line

    output = "**REVIEW:**\n\n```\n"
    output += f"Title: {title}\n"
    output += f"Author: {review.user_name or 'Anonymous'}\n"
    output += f"Source: {review.source}\n"
    output += f"Date: {review.date.strftime('%Y-%m-%d')}\n\n"

    if review.review_text:
        output += f"{review.review_text}\n"

    output += "```"

    return output
