#!/usr/bin/env python3
"""
Print Reddit content with full thread hierarchy
- For posts: print the post
- For comments: print the full thread from root post down to the comment
"""

from models import RedditContent, get_session
from typing import List, Optional


def get_thread_path(comment_id: str, session) -> List[RedditContent]:
    """
    Get the full path from root post to a specific comment
    Returns list ordered from root post to the target comment
    """
    path = []
    current_id = comment_id

    # Traverse up the chain to find the root
    while current_id:
        content = session.query(RedditContent).filter(
            RedditContent.id == current_id
        ).first()

        if not content:
            break

        path.insert(0, content)  # Insert at beginning to maintain order

        # Move up the chain
        if content.content_type == 'comment':
            # For comments, follow parent_id to get the parent (could be post or comment)
            current_id = content.parent_id
        else:
            # We've reached the root post
            break

    return path


def print_content_item(content: RedditContent, indent: int = 0):
    """Print a single content item (post or comment) with indentation"""
    prefix = "    " * indent  # 4 spaces per level

    if content.content_type == 'post':
        print(f"{prefix}[POST]")
        if content.title:
            print(f"{prefix}Title: {content.title}")
        if content.body:
            print(f"{prefix}Body: {content.body}")
    else:  # comment
        print(f"{prefix}[COMMENT]")
        if content.body:
            print(f"{prefix}{content.body}")


def print_reddit_threads(limit: Optional[int] = None, posts_only: bool = False):
    """
    Iterate over all reddit content and print:
    - Posts: just the post
    - Comments: full thread from root post to the comment

    Args:
        limit: Optional limit on number of items to process (for testing)
        posts_only: If True, only print posts (skip comments)
    """
    session = get_session()

    # Get all reddit content ordered by date
    query = session.query(RedditContent).order_by(
        RedditContent.created_at.desc()
    )

    # Filter for posts only if requested
    if posts_only:
        query = query.filter(RedditContent.content_type == 'post')

    if limit:
        query = query.limit(limit)

    all_content = query.all()

    for content in all_content:
        if content.content_type == 'post':
            # Just print the post
            print_content_item(content, indent=0)
            print("\n---\n")
        else:
            # For comments, get and print the full thread path
            thread_path = get_thread_path(content.id, session)

            # Print each item in the path with increasing indentation
            for i, item in enumerate(thread_path):
                print_content_item(item, indent=i)
                print()  # Blank line after each item

            print("---\n")

    session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Print Reddit content threads")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of items to process (for testing)"
    )
    parser.add_argument(
        "--posts-only",
        action="store_true",
        help="Only print posts (skip comments)"
    )

    args = parser.parse_args()
    print_reddit_threads(limit=args.limit, posts_only=args.posts_only)
