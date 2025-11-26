#!/usr/bin/env python3
"""
Group clusters semantically using LLM to create thematic categories
"""

import os
from typing import List, Dict, Optional
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from models import (
    Cluster,
    ClusterGroup as ClusterGroupModel,
    ClusterGroupAssignment,
    get_session
)

# Load environment variables
load_dotenv()

class ClusterGroup(BaseModel):
    """A semantic group of related clusters"""
    group_name: str  # 3-5 word category name
    group_description: str  # One sentence description
    cluster_ids: List[int]  # List of cluster IDs in this group

class SemanticGrouping(BaseModel):
    """Structured output for semantic cluster grouping"""
    groups: List[ClusterGroup]

def generate_semantic_groups(client: OpenAI, clusters: List[Cluster]) -> SemanticGrouping:
    """
    Use LLM to group clusters into semantic categories

    Args:
        client: OpenAI client
        clusters: List of clusters with labels and summaries

    Returns:
        SemanticGrouping with groups
    """
    # Prepare cluster information
    cluster_info = []
    for cluster in clusters:
        label = cluster.cluster_label or f"Cluster {cluster.id}"
        summary = cluster.cluster_summary or "No summary available"
        cluster_info.append(f"ID {cluster.id}: {label} - {summary} ({cluster.size} insights)")

    clusters_text = "\n".join(cluster_info)

    system_prompt = """You are analyzing user feedback clusters to identify higher-level thematic categories.

Given a list of clusters (each representing a specific issue or theme), group related clusters into broader semantic categories.

Rules for grouping:
- Create 3-7 groups maximum (don't over-fragment)
- Each cluster must appear in EXACTLY ONE group (no duplicates allowed)
- Each group should contain 2+ clusters (unless a cluster is truly unique)
- Group name should be 3-5 words and describe the overarching theme
- Group description should be one sentence explaining what ties these clusters together
- Consider semantic relationships, not just keyword matching
- Look for common underlying themes (e.g., "Data Accuracy", "User Experience", "Pricing & Value")

Examples of good groups:
- "Tracking & Syncing Issues" - Problems with data recording, syncing, and accuracy
- "Premium Features & Pricing" - Concerns about cost, value, and premium feature access
- "User Interface & Navigation" - UI/UX issues, confusing design, navigation problems
"""

    user_message = f"""Group these feedback clusters into semantic categories:

{clusters_text}

Identify the main thematic groups and assign each cluster to exactly one group."""

    completion = client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=SemanticGrouping,
        temperature=0.3
    )

    return completion.choices[0].message.parsed

def save_groups_to_database(
    session: Session,
    grouping: SemanticGrouping,
    company_name: str,
    insight_type: str,
    embedding_type: str,
    n_components: Optional[int] = None
) -> None:
    """
    Save semantic groups to database

    Args:
        session: SQLAlchemy session
        grouping: SemanticGrouping result
        company_name: Company name
        insight_type: Type of insight
        embedding_type: Embedding type
        n_components: Dimension count for reduced embeddings
    """
    # Delete existing groups for this configuration
    from sqlalchemy import delete as delete_stmt

    # First, find the group IDs to delete
    group_conditions = [
        ClusterGroupModel.company_name == company_name,
        ClusterGroupModel.insight_type == insight_type,
        ClusterGroupModel.embedding_type == embedding_type
    ]

    if embedding_type == "reduced" and n_components:
        group_conditions.append(ClusterGroupModel.n_components == n_components)

    group_ids_to_delete = session.execute(
        select(ClusterGroupModel.id).where(and_(*group_conditions))
    ).scalars().all()

    if group_ids_to_delete:
        # Delete cluster group assignments first (foreign key dependency)
        session.execute(
            delete_stmt(ClusterGroupAssignment).where(
                ClusterGroupAssignment.group_id.in_(group_ids_to_delete)
            )
        )

        # Then delete the groups
        session.execute(
            delete_stmt(ClusterGroupModel).where(
                ClusterGroupModel.id.in_(group_ids_to_delete)
            )
        )

        print(f"   🗑️  Deleted {len(group_ids_to_delete)} existing groups and their assignments")
        session.commit()

    # Insert new groups
    for group_data in grouping.groups:
        group = ClusterGroupModel(
            company_name=company_name,
            insight_type=insight_type,
            embedding_type=embedding_type,
            n_components=n_components,
            group_name=group_data.group_name,
            group_description=group_data.group_description
        )
        session.add(group)
        session.flush()  # Get the group ID

        # Insert cluster assignments
        for cluster_id in group_data.cluster_ids:
            assignment = ClusterGroupAssignment(
                group_id=group.id,
                cluster_id=cluster_id
            )
            session.add(assignment)

    session.commit()
    print(f"   ✅ Saved {len(grouping.groups)} groups to database")


def generate_text_report(
    grouping: SemanticGrouping,
    clusters_dict: Dict[int, Cluster]
) -> str:
    """
    Generate text report of semantic grouping

    Args:
        grouping: SemanticGrouping result
        clusters_dict: Dict mapping cluster ID to Cluster object

    Returns:
        Text report
    """
    report = []
    report.append("=" * 80)
    report.append("SEMANTIC CLUSTER GROUPING")
    report.append("=" * 80)
    report.append(f"Number of groups: {len(grouping.groups)}")
    report.append("")

    for idx, group in enumerate(grouping.groups, 1):
        total_insights = sum(clusters_dict[cid].size for cid in group.cluster_ids if cid in clusters_dict)

        report.append("=" * 80)
        report.append(f"GROUP {idx}: {group.group_name}")
        report.append("=" * 80)
        report.append(f"Description: {group.group_description}")
        report.append(f"Clusters: {len(group.cluster_ids)} | Total insights: {total_insights}")
        report.append("")

        for cluster_id in group.cluster_ids:
            if cluster_id not in clusters_dict:
                continue

            cluster = clusters_dict[cluster_id]
            label = cluster.cluster_label or f"Cluster {cluster.id}"
            summary = cluster.cluster_summary or "No summary"

            report.append(f"  • {label} ({cluster.size} insights)")
            report.append(f"    {summary}")
            report.append("")

        report.append("")

    return "\n".join(report)

def semantic_clustering_analysis(
    company_name: str,
    insight_type: str = "pain_point",
    embedding_type: str = "reduced",
    n_components: int = 5
) -> None:
    """
    Perform semantic grouping of clusters using LLM

    Args:
        company_name: Company name to filter clusters
        insight_type: Type of insight        embedding_type: Embedding type
        n_components: Dimension count for reduced
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Create database session
    session = get_session()
    print(f"📊 Connected to database")
    print(f"🏢 Company: {company_name}")

    # Load clusters
    print(f"\n🔍 Loading clusters...")
    print(f"   Type: {insight_type}")
    print(f"   Embedding: {embedding_type}" + (f" ({n_components}D)" if embedding_type == "reduced" else ""))

    query = select(Cluster).where(
        and_(
            Cluster.company_name == company_name,
            Cluster.insight_type == insight_type,
            Cluster.embedding_type == embedding_type
        )
    )

    if embedding_type == "reduced":
        query = query.where(Cluster.n_components == n_components)

    clusters = list(session.execute(query).scalars().all())
    session.close()

    if len(clusters) == 0:
        print("\n❌ No clusters found!")
        print("Run cluster_insights.py first.")
        return

    if len(clusters) < 2:
        print(f"\n⚠️  Only {len(clusters)} cluster found. Need at least 2 for grouping.")
        return

    # Check if clusters have labels
    unlabeled = [c for c in clusters if not c.cluster_label]
    if unlabeled:
        print(f"\n⚠️  Warning: {len(unlabeled)} clusters don't have labels.")
        print("   Run label_clusters.py first for best results.")

    print(f"✅ Loaded {len(clusters)} clusters")

    # Generate semantic grouping
    print(f"\n🤖 Generating semantic groups using LLM...")

    grouping = generate_semantic_groups(client, clusters)

    print(f"✅ Generated {len(grouping.groups)} semantic groups")

    # Create cluster lookup dict
    clusters_dict = {c.id: c for c in clusters}

    # Validate grouping: check for duplicates and missing clusters
    assigned_ids = set()
    duplicate_ids = set()

    for group in grouping.groups:
        for cluster_id in group.cluster_ids:
            if cluster_id in assigned_ids:
                duplicate_ids.add(cluster_id)
            assigned_ids.add(cluster_id)

    # Handle duplicates - remove from all groups except the first occurrence
    if duplicate_ids:
        print(f"\n⚠️  Found {len(duplicate_ids)} clusters assigned to multiple groups")
        print(f"   Removing duplicates (keeping first assignment)...")

        seen_clusters = set()
        for group in grouping.groups:
            original_count = len(group.cluster_ids)
            # Keep only clusters we haven't seen yet
            group.cluster_ids = [cid for cid in group.cluster_ids if cid not in seen_clusters]
            seen_clusters.update(group.cluster_ids)

            removed = original_count - len(group.cluster_ids)
            if removed > 0:
                print(f"   - {group.group_name}: removed {removed} duplicate(s)")

        # Rebuild assigned_ids after deduplication
        assigned_ids = set()
        for group in grouping.groups:
            assigned_ids.update(group.cluster_ids)

    missing_ids = set(c.id for c in clusters) - assigned_ids
    if missing_ids:
        print(f"\n⚠️  Found {len(missing_ids)} clusters not assigned to any group")
        print(f"   Creating individual groups for unassigned clusters...")

        # Create individual groups for unassigned clusters
        for cluster_id in missing_ids:
            cluster = clusters_dict[cluster_id]
            label = cluster.cluster_label or f"Cluster {cluster_id}"
            summary = cluster.cluster_summary or "No summary available"

            # Create a group just for this cluster (using Pydantic model)
            individual_group = ClusterGroup(
                group_name=label,
                group_description=summary,
                cluster_ids=[cluster_id]
            )
            grouping.groups.append(individual_group)
            assigned_ids.add(cluster_id)

        print(f"   ✅ Created {len(missing_ids)} individual groups")
        print(f"   Total groups: {len(grouping.groups)}")

    # Save groups to database
    print(f"\n💾 Saving groups to database...")
    session = get_session()
    save_groups_to_database(
        session,
        grouping,
        company_name,
        insight_type,
        embedding_type,
        n_components if embedding_type == "reduced" else None
    )
    session.close()

    # Generate text report
    report = generate_text_report(grouping, clusters_dict)
    print(f"\n{report}")

    # Save report
    output_base = f"semantic_groups_{insight_type}_{embedding_type}"
    if embedding_type == "reduced":
        output_base += f"_{n_components}d"

    report_file = f"{output_base}_report.txt"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"📄 Report saved to: {report_file}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ SEMANTIC GROUPING COMPLETE")
    print("=" * 80)
    print(f"Clusters analyzed: {len(clusters)}")
    print(f"Groups created: {len(grouping.groups)}")
    print(f"Clusters assigned: {len(assigned_ids)} / {len(clusters)}")
    print(f"Saved to database: ✅")
    print("=" * 80)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Group clusters semantically using LLM"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="pain_point",
        help="Type of insight (e.g., pain_point, feature_request, praise, use_case)"
    )
    parser.add_argument(
        "--embedding-type",
        type=str,
        default="reduced",
        choices=["original", "reduced"],
        help="Embedding type (default: reduced)"
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=5,
        help="Number of dimensions for reduced embeddings (default: 5)"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'myfitnesspal')"
    )

    args = parser.parse_args()

    semantic_clustering_analysis(
        company_name=args.company,
        insight_type=args.type,
        embedding_type=args.embedding_type,
        n_components=args.dimensions
    )
