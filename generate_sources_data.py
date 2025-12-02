"""
Generate sources data JSON for the demo site search.
Exports raw posts, comments, and reviews from SQLite.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Database path
DB_FILE = Path(__file__).parent.parent / "dora.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Output path
OUTPUT_FILE = Path(__file__).parent / "data" / "sources.json"


def main():
    """Main function to generate sources JSON."""
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL, echo=False)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sources = []

    with Session(engine) as session:
        # Query Reddit content (posts and comments)
        print("Fetching Reddit content...")
        reddit_query = text("""
            SELECT
                id,
                content_type,
                title,
                body,
                username,
                community_name,
                up_votes,
                url,
                created_at
            FROM reddit_content
            WHERE body IS NOT NULL AND body != ''
            ORDER BY created_at DESC
        """)

        reddit_results = session.execute(reddit_query).fetchall()
        print(f"  Found {len(reddit_results)} Reddit posts/comments")

        for row in reddit_results:
            # Parse date
            date = row.created_at
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except:
                    date = None

            sources.append({
                "id": f"reddit_{row.id}",
                "type": "reddit",
                "contentType": row.content_type or "post",
                "title": row.title,
                "body": row.body,
                "username": row.username,
                "community": row.community_name,
                "upvotes": row.up_votes or 0,
                "url": row.url,
                "date": date.isoformat() if date else None,
                "icon": "reddit.png"
            })

        # Query reviews
        print("Fetching reviews...")
        reviews_query = text("""
            SELECT
                review_id,
                source,
                user_name,
                rating,
                date,
                review_text
            FROM reviews
            WHERE review_text IS NOT NULL AND review_text != ''
            ORDER BY date DESC
        """)

        review_results = session.execute(reviews_query).fetchall()
        print(f"  Found {len(review_results)} reviews")

        for row in review_results:
            # Parse date
            date = row.date
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except:
                    date = None

            # Map source to icon
            source_lower = (row.source or "").lower()
            if "appstore" in source_lower or "app store" in source_lower:
                icon = "appstore.png"
                platform = "appstore"
            elif "trustpilot" in source_lower:
                icon = "trustpilot.png"
                platform = "trustpilot"
            elif "producthunt" in source_lower or "product hunt" in source_lower:
                icon = "producthunt.png"
                platform = "producthunt"
            elif "microsoft" in source_lower or "windows" in source_lower:
                icon = "windows.png"
                platform = "microsoft"
            else:
                icon = "reddit.png"
                platform = row.source or "unknown"

            sources.append({
                "id": f"review_{row.review_id}",
                "type": "review",
                "contentType": "review",
                "title": None,
                "body": row.review_text,
                "username": row.user_name,
                "platform": platform,
                "rating": row.rating,
                "url": None,
                "date": date.isoformat() if date else None,
                "icon": icon
            })

    # Sort by date descending
    sources.sort(key=lambda x: x["date"] or "", reverse=True)

    # Count by type
    reddit_count = sum(1 for s in sources if s["type"] == "reddit")
    post_count = sum(1 for s in sources if s["type"] == "reddit" and s["contentType"] == "post")
    comment_count = sum(1 for s in sources if s["type"] == "reddit" and s["contentType"] == "comment")
    review_count = sum(1 for s in sources if s["type"] == "review")

    # Count by platform for reviews
    platform_counts = {}
    for s in sources:
        if s["type"] == "review":
            p = s.get("platform", "unknown")
            platform_counts[p] = platform_counts.get(p, 0) + 1

    # Final output
    output = {
        "sources": sources,
        "meta": {
            "total": len(sources),
            "reddit": reddit_count,
            "posts": post_count,
            "comments": comment_count,
            "reviews": review_count,
            "platforms": platform_counts,
            "generatedAt": datetime.now().isoformat()
        }
    }

    # Write to file
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Done! Generated {len(sources)} sources.")
    print(f"  - Reddit posts: {post_count}")
    print(f"  - Reddit comments: {comment_count}")
    print(f"  - Reviews: {review_count}")


if __name__ == "__main__":
    main()
