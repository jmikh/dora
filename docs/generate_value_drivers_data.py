"""
Generate value drivers data JSON for the demo site dashboard.
Exports data from SQLite and generates AI summaries for each category.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from parent directory
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Database path
DB_FILE = Path(__file__).parent.parent / "dora.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Output path
OUTPUT_FILE = Path(__file__).parent / "data" / "value_drivers.json"


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
    return "reddit.png"  # fallback


def generate_ai_summary(category: str, value_drivers: list[dict]) -> str:
    """
    Generate AI summary for a category.
    Uses OpenAI API if available, otherwise returns placeholder.
    """
    try:
        from openai import OpenAI

        client = OpenAI()

        # Build context from value drivers
        driver_texts = [f"- \"{vd['quote']}\"" for vd in value_drivers[:15]]
        context = "\n".join(driver_texts)

        prompt = f"""Summarize these user quotes about why they value Wispr Flow in the "{category}" category in 2-3 sentences. Focus on what users appreciate and the benefits they experience. Be concise and professional.

Quotes:
{context}

Summary:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  Warning: Could not generate AI summary for {category}: {e}")
        # Return a reasonable fallback
        count = len(value_drivers)
        return f"This category contains {count} quotes from users who value Wispr Flow for its {category.lower().replace('_', ' ')}."


def main():
    """Main function to generate value drivers JSON."""
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL, echo=False)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        # Query all value drivers with source info
        print("Fetching value drivers with source data...")

        query = text("""
            SELECT
                v.id,
                v.value_driver as category,
                v.quote,
                v.source_id,
                v.source_table,
                v.extracted_at,
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
            FROM value_drivers v
            LEFT JOIN reddit_content rc ON v.source_table = 'reddit_content' AND v.source_id = rc.id
            LEFT JOIN reviews r ON v.source_table = 'reviews' AND v.source_id = r.review_id
            ORDER BY v.value_driver, v.extracted_at DESC
        """)

        results = session.execute(query).fetchall()
        print(f"  Found {len(results)} value driver entries")

        # Group by category
        categories_data: dict[str, dict] = {}
        other_entries: list = []  # Collect "other:" entries separately
        time_series_data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for row in results:
            raw_category = row.category or "other"

            # Skip value drivers that start with "other:"
            if raw_category.startswith("other:"):
                continue

            # Normalize category: replace underscores with spaces and title case
            category = raw_category.replace("_", " ").title()

            # Initialize category if needed
            if category not in categories_data:
                categories_data[category] = {
                    "name": category,
                    "count": 0,
                    "valueDrivers": [],
                    "sources": defaultdict(int)
                }

            cat_data = categories_data[category]
            cat_data["count"] += 1

            # Source breakdown
            source_type = row.source_table
            cat_data["sources"][source_type] += 1

            # Determine date for time series
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

            month_key = date.strftime("%Y-%m") if date else "unknown"
            time_series_data[category][month_key] += 1

            # Build value driver entry
            driver_entry = {
                "id": row.id,
                "valueDriver": raw_category,
                "quote": row.quote,
                "sourceType": source_type,
                "sourceId": row.source_id,
                "date": date.isoformat() if date else None,
            }

            # Add source-specific data
            if source_type == "reddit_content":
                source_name = "reddit"
                driver_entry["source"] = {
                    "type": row.reddit_content_type or "post",
                    "title": row.reddit_title,
                    "body": row.reddit_body or "",
                    "community": row.reddit_community,
                    "url": row.reddit_url,
                    "upvotes": row.reddit_upvotes or 0
                }
            else:
                source_name = row.review_source
                driver_entry["source"] = {
                    "type": "review",
                    "platform": row.review_source,
                    "userName": row.review_user,
                    "rating": row.review_rating,
                    "body": row.review_text or "",
                    "url": None
                }

            driver_entry["icon"] = get_source_icon(source_type, source_name)
            cat_data["valueDrivers"].append(driver_entry)

        # Convert sources defaultdict to regular dict
        for cat_data in categories_data.values():
            cat_data["sources"] = dict(cat_data["sources"])

        # Sort categories by count
        sorted_categories = sorted(
            categories_data.values(),
            key=lambda x: x["count"],
            reverse=True
        )

        # Generate AI summaries for each category
        print("Generating AI summaries...")
        for cat_data in sorted_categories:
            print(f"  Processing: {cat_data['name']} ({cat_data['count']} value drivers)")
            cat_data["aiSummary"] = generate_ai_summary(
                cat_data["name"],
                cat_data["valueDrivers"]
            )

        # Build time series structure
        all_months = set()
        for cat_months in time_series_data.values():
            all_months.update(cat_months.keys())

        sorted_months = sorted([m for m in all_months if m != "unknown"])

        # Format month labels nicely
        month_labels = []
        for m in sorted_months:
            try:
                dt = datetime.strptime(m, "%Y-%m")
                month_labels.append(dt.strftime("%b %Y"))
            except:
                month_labels.append(m)

        # Build datasets for time series
        time_series_datasets = {}
        for category, months in time_series_data.items():
            time_series_datasets[category] = [
                months.get(m, 0) for m in sorted_months
            ]

        # Calculate date range
        date_range = {
            "start": sorted_months[0] if sorted_months else None,
            "end": sorted_months[-1] if sorted_months else None
        }

        # Count total (excluding "other:" entries)
        total_count = sum(cat["count"] for cat in sorted_categories)

        # Final output structure
        output = {
            "categories": sorted_categories,
            "timeSeries": {
                "labels": month_labels,
                "rawLabels": sorted_months,
                "datasets": time_series_datasets
            },
            "meta": {
                "totalValueDrivers": total_count,
                "totalCategories": len(sorted_categories),
                "dateRange": date_range,
                "generatedAt": datetime.now().isoformat()
            }
        }

        # Write to file
        print(f"Writing to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Done! Generated data for {len(sorted_categories)} categories.")
        print(f"Total value drivers: {total_count}")
        print(f"Top 5 categories:")
        for cat in sorted_categories[:5]:
            print(f"  - {cat['name']}: {cat['count']} value drivers")


if __name__ == "__main__":
    main()
