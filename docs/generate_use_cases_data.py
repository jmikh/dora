"""
Generate use cases data JSON for the demo site dashboard.
Exports data from SQLite and generates AI summaries for each category.
"""

import json
import os
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
OUTPUT_FILE = Path(__file__).parent / "data" / "use_cases.json"


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


def generate_ai_summary(category: str, use_cases: list[dict]) -> str:
    """
    Generate AI summary for a category.
    Uses OpenAI API if available, otherwise returns placeholder.
    """
    try:
        from openai import OpenAI

        client = OpenAI()

        # Build context from use cases
        use_case_texts = [f"- {uc['useCase']}: \"{uc['quote']}\"" for uc in use_cases[:15]]
        context = "\n".join(use_case_texts)

        prompt = f"""Summarize these user use cases for Wispr Flow in the "{category}" category in 2-3 sentences. Focus on how users are using the product and common patterns. Be concise and professional.

Use Cases:
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
        count = len(use_cases)
        return f"This category contains {count} use cases from users utilizing Wispr Flow for {category.lower().replace('_', ' ')}."


def main():
    """Main function to generate use cases JSON."""
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL, echo=False)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        # Query all use cases with categories and source info
        print("Fetching use cases with source data...")

        # use_case column contains the category directly
        query = text("""
            SELECT
                u.id,
                u.use_case as category,
                u.quote,
                u.source_id,
                u.source_table,
                u.extracted_at,
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
            FROM use_cases u
            LEFT JOIN reddit_content rc ON u.source_table = 'reddit_content' AND u.source_id = rc.id
            LEFT JOIN reviews r ON u.source_table = 'reviews' AND u.source_id = r.review_id
            ORDER BY u.use_case, u.extracted_at DESC
        """)

        results = session.execute(query).fetchall()
        print(f"  Found {len(results)} use case entries")

        # Group by category
        categories_data: dict[str, dict] = {}
        time_series_data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for row in results:
            raw_category = row.category or "other"
            # Skip use cases that start with "other:"
            if raw_category.startswith("other:"):
                continue
            # Normalize category: replace underscores with spaces
            category = raw_category.replace("_", " ").title()
            # Fix specific category names
            category = category.replace("Llm", "LLMs")

            # Initialize category if needed
            if category not in categories_data:
                categories_data[category] = {
                    "name": category,
                    "count": 0,
                    "useCases": [],
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

            # Build use case entry
            use_case_entry = {
                "id": row.id,
                "useCase": raw_category,  # Original use case description
                "quote": row.quote,
                "sourceType": source_type,
                "sourceId": row.source_id,
                "date": date.isoformat() if date else None,
            }

            # Add source-specific data
            if source_type == "reddit_content":
                source_name = "reddit"
                use_case_entry["source"] = {
                    "type": row.reddit_content_type or "post",
                    "title": row.reddit_title,
                    "body": row.reddit_body or "",
                    "community": row.reddit_community,
                    "url": row.reddit_url,
                    "upvotes": row.reddit_upvotes or 0
                }
            else:
                source_name = row.review_source
                use_case_entry["source"] = {
                    "type": "review",
                    "platform": row.review_source,
                    "userName": row.review_user,
                    "rating": row.review_rating,
                    "body": row.review_text or "",
                    "url": None
                }

            use_case_entry["icon"] = get_source_icon(source_type, source_name)
            cat_data["useCases"].append(use_case_entry)

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
            print(f"  Processing: {cat_data['name']} ({cat_data['count']} use cases)")
            cat_data["aiSummary"] = generate_ai_summary(
                cat_data["name"],
                cat_data["useCases"]
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

        # Final output structure
        output = {
            "categories": sorted_categories,
            "timeSeries": {
                "labels": month_labels,
                "rawLabels": sorted_months,
                "datasets": time_series_datasets
            },
            "meta": {
                "totalUseCases": len(results),
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
        print(f"Top 5 categories:")
        for cat in sorted_categories[:5]:
            print(f"  - {cat['name']}: {cat['count']} use cases")


if __name__ == "__main__":
    main()
