"""
Generate magic moments data JSON for the demo site dashboard.
Exports magic moments with their source content.
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
OUTPUT_FILE = Path(__file__).parent / "data" / "magic_moments.json"


def get_source_icon(source_table: str, source_name: str | None) -> str:
    """Map source to icon filename."""
    if source_table == "reddit_content":
        return "reddit.png"
    if source_name == "appstore":
        return "appstore.png"
    if source_name == "trustpilot":
        return "trustpilot.png"
    if source_name == "microsoft":
        return "windows.png"
    if source_name == "producthunt":
        return "producthunt.png"
    return "reddit.png"


def main():
    """Main function to generate magic moments JSON."""
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL, echo=False)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        print("Fetching magic moments with source data...")

        query = text("""
            SELECT
                m.id,
                m.quote,
                m.source_id,
                m.source_table,
                m.extracted_at,
                -- Reddit content fields
                rc.content_type as reddit_content_type,
                rc.title as reddit_title,
                rc.body as reddit_body,
                rc.community_name as reddit_community,
                rc.url as reddit_url,
                rc.created_at as reddit_date,
                rc.up_votes as reddit_upvotes,
                -- Review fields
                r.source as review_source,
                r.user_name as review_user,
                r.rating as review_rating,
                r.date as review_date,
                r.review_text as review_text
            FROM magic_moments m
            LEFT JOIN reddit_content rc ON m.source_table = 'reddit_content' AND m.source_id = rc.id
            LEFT JOIN reviews r ON m.source_table = 'reviews' AND m.source_id = r.review_id
            ORDER BY m.extracted_at DESC
        """)

        results = session.execute(query).fetchall()
        print(f"  Found {len(results)} magic moments")

        moments = []

        for row in results:
            source_type = row.source_table

            # Determine date
            if source_type == "reddit_content" and row.reddit_date:
                date = row.reddit_date
            elif source_type == "reviews" and row.review_date:
                date = row.review_date
            else:
                date = row.extracted_at

            # Parse date if string
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except:
                    date = datetime.now()

            # Build moment entry
            moment = {
                "id": row.id,
                "quote": row.quote,
                "sourceType": source_type,
                "sourceId": row.source_id,
                "date": date.isoformat() if date else None,
            }

            # Add source-specific data
            if source_type == "reddit_content":
                source_name = "reddit"
                moment["source"] = {
                    "type": row.reddit_content_type or "post",
                    "title": row.reddit_title,
                    "body": row.reddit_body or "",
                    "community": row.reddit_community,
                    "url": row.reddit_url,
                    "upvotes": row.reddit_upvotes or 0
                }
            else:
                source_name = row.review_source
                moment["source"] = {
                    "type": "review",
                    "platform": row.review_source,
                    "userName": row.review_user,
                    "rating": row.review_rating,
                    "body": row.review_text or "",
                    "url": None
                }

            moment["icon"] = get_source_icon(source_type, source_name)
            moments.append(moment)

        # Final output
        output = {
            "moments": moments,
            "meta": {
                "total": len(moments),
                "generatedAt": datetime.now().isoformat()
            }
        }

        # Write to file
        print(f"Writing to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Done! Generated {len(moments)} magic moments.")


if __name__ == "__main__":
    main()
