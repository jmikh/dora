#!/usr/bin/env python3
"""
View complaint categorization results grouped by category
"""

import sqlite3
from pathlib import Path
from typing import Optional

# Database path
DB_FILE = Path(__file__).parent / "dora.db"


def view_complaint_categories(
    category: Optional[str] = None,
    min_confidence: float = 0.0,
    output_file: Optional[str] = None
) -> None:
    """
    Display complaints grouped by category

    Args:
        category: Filter by specific category (optional)
        min_confidence: Minimum confidence threshold
        output_file: Save output to file (optional)
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get all categories with counts
    if category:
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM complaint_categories
            WHERE category = ? AND confidence >= ?
            GROUP BY category
            ORDER BY count DESC
        """, (category, min_confidence))
    else:
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM complaint_categories
            WHERE confidence >= ?
            GROUP BY category
            ORDER BY count DESC
        """, (min_confidence,))

    categories = cursor.fetchall()

    if not categories:
        print("No complaints found matching criteria")
        conn.close()
        return

    # Prepare output
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("COMPLAINT CATEGORIES REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Get total count
    cursor.execute("""
        SELECT COUNT(*)
        FROM complaint_categories
        WHERE confidence >= ?
    """, (min_confidence,))
    total_count = cursor.fetchone()[0]

    lines.append(f"Total complaints: {total_count:,}")
    lines.append(f"Categories: {len(categories)}")
    lines.append(f"Min confidence filter: {min_confidence:.2f}")
    lines.append("")

    # For each category, show all complaints
    for cat, count in categories:
        lines.append("=" * 80)
        lines.append(f"CATEGORY: \"{cat}\" - {count} complaints")
        lines.append("=" * 80)
        lines.append("")

        # Get complaints for this category
        cursor.execute("""
            SELECT
                c.id,
                c.complaint,
                c.quote,
                cc.confidence,
                cc.reasoning
            FROM complaints c
            JOIN complaint_categories cc ON c.id = cc.complaint_id
            WHERE cc.category = ? AND cc.confidence >= ?
            ORDER BY cc.confidence DESC
        """, (cat, min_confidence))

        complaints = cursor.fetchall()

        for i, (c_id, complaint_text, quote, conf, reasoning) in enumerate(complaints, 1):
            lines.append(f"{i}. [ID: {c_id}] {complaint_text}")
            lines.append(f"   Quote: \"{quote[:100]}{'...' if len(quote) > 100 else ''}\"")
            lines.append(f"   Confidence: {conf:.2f} | Reasoning: {reasoning}")
            lines.append("")

    # Summary
    lines.append("=" * 80)
    lines.append("CATEGORY SUMMARY")
    lines.append("=" * 80)

    for cat, count in categories:
        percentage = (count / total_count) * 100
        lines.append(f"{cat}: {count} ({percentage:.1f}%)")

    lines.append("=" * 80)

    # Output
    output = "\n".join(lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"✅ Report saved to {output_file}")
    else:
        print(output)

    conn.close()


def show_low_confidence_classifications(threshold: float = 0.95) -> None:
    """
    Show classifications with confidence below threshold

    Args:
        threshold: Confidence threshold (default 0.95)
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.complaint,
            cc.category,
            cc.confidence,
            cc.reasoning
        FROM complaints c
        JOIN complaint_categories cc ON c.id = cc.complaint_id
        WHERE cc.confidence < ?
        ORDER BY cc.confidence ASC
    """, (threshold,))

    results = cursor.fetchall()

    if not results:
        print(f"✅ No classifications below {threshold:.2f} confidence")
        conn.close()
        return

    print("=" * 80)
    print(f"LOW CONFIDENCE CLASSIFICATIONS (< {threshold:.2f})")
    print("=" * 80)
    print(f"\nTotal: {len(results)}")
    print()

    for c_id, complaint, category, conf, reasoning in results:
        print(f"[ID: {c_id}] Confidence: {conf:.2f}")
        print(f"  Complaint: {complaint}")
        print(f"  Category: {category}")
        print(f"  Reasoning: {reasoning}")
        print()

    conn.close()


def export_to_csv(output_file: str = "complaint_categories.csv") -> None:
    """
    Export all categorizations to CSV

    Args:
        output_file: Output CSV file path
    """
    import csv

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.complaint,
            c.quote,
            c.source_table,
            c.source_id,
            cc.category,
            cc.confidence,
            cc.reasoning,
            cc.classified_at
        FROM complaints c
        JOIN complaint_categories cc ON c.id = cc.complaint_id
        ORDER BY cc.category, cc.confidence DESC
    """)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'complaint_id', 'complaint', 'quote', 'source_table', 'source_id',
            'category', 'confidence', 'reasoning', 'classified_at'
        ])
        writer.writerows(cursor.fetchall())

    conn.close()
    print(f"✅ Exported to {output_file}")


def export_custom_csv(output_file: str = "complaints_by_category.csv") -> None:
    """
    Export complaints with category, source, quote, and date

    Args:
        output_file: Output CSV file path
    """
    import csv

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Union query to combine Reddit and Reviews data
    cursor.execute("""
        SELECT
            cc.category as complaint_category,
            'reddit' as source,
            c.quote,
            rc.created_at as date
        FROM complaints c
        JOIN complaint_categories cc ON c.id = cc.complaint_id
        JOIN reddit_content rc ON c.source_id = rc.id AND c.source_table = 'reddit_content'

        UNION ALL

        SELECT
            cc.category as complaint_category,
            r.source,
            c.quote,
            r.date
        FROM complaints c
        JOIN complaint_categories cc ON c.id = cc.complaint_id
        JOIN reviews r ON c.source_id = r.review_id AND c.source_table = 'reviews'

        ORDER BY date DESC
    """)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['complaint_category', 'source', 'quote', 'date'])
        writer.writerows(cursor.fetchall())

    conn.close()
    print(f"✅ Exported to {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="View complaint categorization results")
    parser.add_argument(
        "--category",
        type=str,
        help="Filter by specific category"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence threshold (default: 0.0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save output to file"
    )
    parser.add_argument(
        "--low-confidence",
        action="store_true",
        help="Show only low confidence classifications"
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        help="Export to CSV file (full details)"
    )
    parser.add_argument(
        "--export-custom",
        type=str,
        help="Export custom CSV with: category, source, quote, date"
    )

    args = parser.parse_args()

    if args.export_csv:
        export_to_csv(args.export_csv)
    elif args.export_custom:
        export_custom_csv(args.export_custom)
    elif args.low_confidence:
        show_low_confidence_classifications()
    else:
        view_complaint_categories(
            category=args.category,
            min_confidence=args.min_confidence,
            output_file=args.output
        )
