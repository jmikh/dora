#!/usr/bin/env python3
"""
Generate dashboard data for Wispr Flow insights visualization
"""

import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from models import Review, Insight, Cluster, YouTubeVideo, ClusterGroup, ClusterGroupAssignment, get_session

def get_pain_points_by_month_and_cluster(
    session: Session,
    company_name: str = "wispr") -> Dict[str, Any]:
    """
    Get pain points organized by month and cluster (only clustered pain points)

    Returns:
        Dictionary with timeline data and cluster details
    """
    # Query to get all pain points with their cluster info (ONLY CLUSTERED)
    # Uses LEFT JOIN to include both review and YouTube video insights
    query = text("""
        SELECT
            i.id,
            i.insight_text,
            i.review_id,
            strftime('%Y-%m', i.review_date) as month,
            i.cluster_id,
            c.cluster_label,
            c.cluster_summary,
            c.size as cluster_size,
            r.review_text,
            r.rating,
            r.user_name,
            r.date,
            COALESCE(r.source, 'youtube') as source,
            i.source_type,
            i.source_id
        FROM insights i
        INNER JOIN clusters c ON i.cluster_id = c.id
        LEFT JOIN reviews r ON i.review_id = r.review_id
        WHERE i.company_name = :company
        AND i.insight_type = 'pain_point'
        AND i.cluster_id IS NOT NULL
        ORDER BY i.review_date DESC
    """)

    result = session.execute(query, {"company": company_name})
    rows = result.fetchall()

    # Organize data by cluster first, then by month
    cluster_all_insights = defaultdict(list)  # All insights per cluster across all time
    timeline_data = defaultdict(lambda: defaultdict(list))  # Month -> Cluster -> Insights
    cluster_details = {}
    source_stats = defaultdict(int)  # Track insights by source

    for row in rows:
        insight_id, insight_text, review_id, month, cluster_id, cluster_label, cluster_summary, cluster_size, review_text, rating, user_name, review_date, source, source_type, source_id = row

        insight_data = {
            "insight_id": insight_id,
            "insight_text": insight_text,
            "review_id": review_id,
            "review_text": review_text,
            "rating": rating,
            "user_name": user_name,
            "review_date": str(review_date),
            "month": month,
            "source": source,
            "source_type": source_type,
            "source_id": source_id
        }

        # Track actual source statistics (appstore, youtube, trustpilot, etc.)
        source_stats[source] += 1

        # Add to timeline (for monthly breakdown)
        timeline_data[month][cluster_id].append(insight_data)

        # Add to cluster's all-time insights
        cluster_all_insights[cluster_id].append(insight_data)

        # Store cluster details
        if cluster_id not in cluster_details:
            cluster_details[cluster_id] = {
                "cluster_id": cluster_id,
                "label": cluster_label,
                "summary": cluster_summary,
                "size": cluster_size if cluster_size else 0,
                "total_insights": 0,
                "all_insights": []  # Will be populated later
            }

        cluster_details[cluster_id]["total_insights"] += 1

    # Add all insights to cluster details
    for cluster_id, insights in cluster_all_insights.items():
        if cluster_id in cluster_details:
            cluster_details[cluster_id]["all_insights"] = insights

    # Convert timeline to list format for easier visualization
    timeline = []
    for month in sorted(timeline_data.keys()):
        month_data = {
            "month": month,
            "clusters": []
        }

        for cluster_id, insights in timeline_data[month].items():
            month_data["clusters"].append({
                "cluster_id": cluster_id,
                "cluster_label": cluster_details[cluster_id]["label"],
                "count": len(insights)
            })

        # Sort clusters by total size (not monthly count)
        month_data["clusters"].sort(key=lambda x: cluster_details[x["cluster_id"]]["total_insights"], reverse=True)
        timeline.append(month_data)

    return {
        "timeline": timeline,
        "cluster_details": list(cluster_details.values()),
        "total_pain_points": len(rows),
        "total_clusters": len(cluster_details),
        "source_breakdown": dict(source_stats)
    }

def get_use_cases_summary(
    session: Session,
    company_name: str = "wispr") -> Dict[str, Any]:
    """
    Get use cases organized by cluster with review context
    """
    query = text("""
        SELECT
            i.id,
            i.insight_text,
            i.review_id,
            i.cluster_id,
            c.cluster_label,
            c.cluster_summary,
            c.size as cluster_size,
            r.review_text,
            r.rating,
            r.user_name,
            r.date,
            COALESCE(r.source, 'youtube') as source,
            i.source_type,
            i.source_id
        FROM insights i
        LEFT JOIN clusters c ON i.cluster_id = c.id
        LEFT JOIN reviews r ON i.review_id = r.review_id
        WHERE i.company_name = :company
        AND i.insight_type = 'use_case'
        ORDER BY c.size DESC NULLS LAST, r.date DESC
    """)

    result = session.execute(query, {"company": company_name})
    rows = result.fetchall()

    clusters = defaultdict(list)
    source_stats = defaultdict(int)

    for row in rows:
        insight_id, insight_text, review_id, cluster_id, cluster_label, cluster_summary, cluster_size, review_text, rating, user_name, review_date, source, source_type, source_id = row

        if cluster_id is None:
            cluster_id = -1
            cluster_label = "Unclustered"

        clusters[cluster_id].append({
            "insight_id": insight_id,
            "insight_text": insight_text,
            "review_id": review_id,
            "review_text": review_text,
            "rating": rating,
            "user_name": user_name,
            "review_date": str(review_date),
            "source": source,
            "source_type": source_type,
            "source_id": source_id
        })

        # Track actual source statistics (appstore, youtube, trustpilot, etc.)
        source_stats[source] += 1

    # Format for output
    use_case_clusters = []
    for cluster_id, insights in clusters.items():
        # Get cluster info from first insight's cluster
        cluster_info = next((r for r in rows if r[3] == cluster_id), None)

        use_case_clusters.append({
            "cluster_id": cluster_id,
            "label": cluster_info[4] if cluster_info and cluster_info[4] else "Unclustered",
            "summary": cluster_info[5] if cluster_info and cluster_info[5] else "",
            "count": len(insights),
            "insights": insights
        })

    use_case_clusters.sort(key=lambda x: x["count"], reverse=True)

    return {
        "use_case_clusters": use_case_clusters,
        "total_use_cases": len(rows),
        "source_breakdown": dict(source_stats)
    }

def get_review_source_stats(
    session: Session,
    company_name: str = "wispr"
) -> Dict[str, Any]:
    """
    Get review statistics by source
    """
    query = text("""
        SELECT
            source,
            COUNT(*) as review_count,
            COUNT(CASE WHEN generated_insights = 1 THEN 1 END) as processed_count
        FROM reviews
        WHERE company_name = :company
        GROUP BY source
        ORDER BY review_count DESC
    """)

    result = session.execute(query, {"company": company_name})
    rows = result.fetchall()

    sources = []
    for source, review_count, processed_count in rows:
        sources.append({
            "source": source or "unknown",
            "review_count": review_count,
            "processed_count": processed_count,
            "processing_rate": f"{(processed_count/review_count*100):.1f}%" if review_count > 0 else "0%"
        })

    return {
        "sources": sources,
        "total_reviews": sum(s["review_count"] for s in sources),
        "total_processed": sum(s["processed_count"] for s in sources)
    }


def get_semantic_groups(
    session: Session,
    company_name: str = "wispr",
    insight_type: str = "pain_point",
    embedding_type: str = "reduced",
    n_components: int = 20
) -> List[Dict[str, Any]]:
    """
    Get semantic groups with their clusters and insights

    Args:
        session: SQLAlchemy session
        company_name: Company name
        insight_type: Type of insight
        embedding_type: Embedding type
        n_components: Dimension count for reduced embeddings

    Returns:
        List of semantic groups with cluster details
    """
    # Query groups with their cluster assignments
    query = text("""
        SELECT
            g.id as group_id,
            g.group_name,
            g.group_description,
            g.created_at,
            c.id as cluster_id,
            c.cluster_label,
            c.size as cluster_size
        FROM cluster_groups g
        LEFT JOIN cluster_group_assignments a ON g.id = a.group_id
        LEFT JOIN clusters c ON a.cluster_id = c.id
        WHERE g.company_name = :company
        AND g.insight_type = :insight_type
        AND g.embedding_type = :embedding_type
        AND g.n_components = :n_components
        ORDER BY g.id, c.size DESC
    """)

    result = session.execute(query, {
        "company": company_name,
        "insight_type": insight_type,
        "embedding_type": embedding_type,
        "n_components": n_components
    })
    rows = result.fetchall()

    if not rows:
        return []

    # Organize groups
    groups_dict = {}
    for row in rows:
        group_id, group_name, group_desc, created_at, cluster_id, cluster_label, cluster_size = row

        if group_id not in groups_dict:
            groups_dict[group_id] = {
                "group_id": group_id,
                "group_name": group_name,
                "group_description": group_desc,
                "clusters": [],
                "total_insights": 0
            }

        if cluster_id:
            groups_dict[group_id]["clusters"].append({
                "cluster_id": cluster_id,
                "label": cluster_label,
                "count": cluster_size
            })
            groups_dict[group_id]["total_insights"] += cluster_size

    return list(groups_dict.values())


def get_youtube_videos(session: Session) -> Dict[str, Any]:
    """
    Get YouTube videos sorted by view count
    """
    try:
        # Query all videos, sorted by view count descending
        videos = session.query(YouTubeVideo).order_by(
            YouTubeVideo.view_count.desc()
        ).all()

        video_list = []
        for video in videos:
            video_list.append({
                "id": video.id,
                "title": video.title,
                "url": video.url,
                "thumbnail_url": video.thumbnail_url,
                "view_count": video.view_count,
                "likes": video.likes,
                "comments_count": video.comments_count,
                "date": video.date.isoformat() if video.date else None,
                "channel_name": video.channel_name,
                "duration": video.duration
            })

        return {
            "videos": video_list,
            "total_videos": len(video_list),
            "total_views": sum(v["view_count"] for v in video_list),
            "total_likes": sum(v["likes"] for v in video_list)
        }
    except Exception as e:
        print(f"⚠️  Warning: Could not load YouTube videos: {e}")
        return {
            "videos": [],
            "total_videos": 0,
            "total_views": 0,
            "total_likes": 0
        }


def generate_dashboard_data(
    company_name: str = "wispr",
    output_file: str = "dashboard_data.json"
) -> None:
    """
    Generate complete dashboard data and save to JSON
    """
    session = get_session()

    print(f"📊 Generating dashboard data for {company_name}")
    # Get review source statistics
    print("\n🔍 Fetching review statistics...")
    source_stats = get_review_source_stats(session, company_name)
    print(f"   ✅ Found {source_stats['total_reviews']} reviews from {len(source_stats['sources'])} sources")
    for source_info in source_stats['sources']:
        print(f"      - {source_info['source']}: {source_info['review_count']} reviews ({source_info['processing_rate']} processed)")

    # Get pain points timeline
    print("\n🔍 Fetching pain points...")
    pain_points_data = get_pain_points_by_month_and_cluster(session, company_name)
    print(f"   ✅ Found {pain_points_data['total_pain_points']} pain points across {pain_points_data['total_clusters']} clusters")
    print(f"      Source breakdown: {pain_points_data['source_breakdown']}")

    # Get semantic groups for pain points
    print("\n🔍 Fetching semantic groups...")
    semantic_groups = get_semantic_groups(session, company_name, "pain_point", "reduced", 20)
    pain_points_data['semantic_groups'] = semantic_groups
    print(f"   ✅ Found {len(semantic_groups)} semantic groups")

    # Get use cases
    print("\n🔍 Fetching use cases...")
    use_cases_data = get_use_cases_summary(session, company_name)
    print(f"   ✅ Found {use_cases_data['total_use_cases']} use cases")
    print(f"      Source breakdown: {use_cases_data['source_breakdown']}")

    # Get YouTube videos
    print("\n🔍 Fetching YouTube videos...")
    youtube_data = get_youtube_videos(session)
    print(f"   ✅ Found {youtube_data['total_videos']} YouTube videos")
    print(f"      Total views: {youtube_data['total_views']:,}")
    print(f"      Total likes: {youtube_data['total_likes']:,}")

    # Get company metadata
    total_reviews = session.execute(
        select(Review).where(Review.company_name == company_name)
    ).scalars().all()

    # Combine all data
    dashboard_data = {
        "company_name": company_name,
        "generated_at": datetime.now().isoformat(),
        "total_reviews": len(total_reviews),
        "review_sources": source_stats,
        "pain_points": pain_points_data,
        "use_cases": use_cases_data,
        "youtube_videos": youtube_data
    }

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"\n💾 Dashboard data saved to: {output_file}")
    print(f"   Total reviews: {len(total_reviews)}")
    print(f"   Pain points: {pain_points_data['total_pain_points']}")
    print(f"   Use cases: {use_cases_data['total_use_cases']}")

    session.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate dashboard data for visualization")
    parser.add_argument(
        "--company",
        type=str,
        default="wispr",
        help="Company name"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dashboard_data.json",
        help="Output JSON file"
    )

    args = parser.parse_args()

    generate_dashboard_data(
        company_name=args.company,
        output_file=args.output
    )
