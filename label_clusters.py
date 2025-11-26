#!/usr/bin/env python3
"""
Label clusters using LLM by analyzing centroid insights
"""

import os
import json
import numpy as np
from typing import List, Optional
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy import select, update, and_
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from models import Cluster, Insight, get_session

# Load environment variables
load_dotenv()

class ClusterLabeling(BaseModel):
    """Structured output for cluster labeling"""
    label: str  # 2-3 word label
    summary: str  # One sentence summary

def find_centroid_insights(
    session: Session,
    cluster_id: int,
    company_name: str,
    embedding_type: str,
    n_components: Optional[int],
    n_insights: int = 10
) -> List[Insight]:
    """
    Find insights closest to cluster centroid

    Args:
        session: SQLAlchemy session
        cluster_id: Database cluster ID
        company_name: Company name (for validation)
        embedding_type: 'original' or 'reduced'
        n_components: Dimension count for reduced embeddings
        n_insights: Number of centroid insights to return

    Returns:
        List of Insight objects closest to centroid
    """
    from sqlalchemy import text

    # Determine embedding column
    if embedding_type == "original":
        embedding_column = "embedding"
    else:
        embedding_column = f"reduced_embedding_{n_components}"

    # Load all insights in cluster with their embeddings
    query_text = f"""
        SELECT id, review_id, insight_text, insight_type, review_date,
               extracted_at, {embedding_column}
        FROM insights
        WHERE cluster_id = :cluster_id
        AND company_name = :company
        AND {embedding_column} IS NOT NULL
    """

    result = session.execute(text(query_text), {"cluster_id": cluster_id, "company": company_name})
    rows = result.fetchall()

    if not rows:
        return []

    # Extract embeddings and calculate centroid
    embeddings = []
    insights = []

    for row in rows:
        from datetime import datetime as dt

        insight = Insight(
            id=row[0],
            review_id=row[1],
            insight_text=row[2],
            insight_type=row[3],
            review_date=dt.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
            extracted_at=dt.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            source_type='review',  # Default for existing code
            source_id=row[1] if row[1] else ''  # Use review_id as source_id
        )
        insights.append(insight)

        embedding_vector = json.loads(row[6])  # Moved from index 7 to 6
        embeddings.append(embedding_vector)

    embeddings_matrix = np.array(embeddings)
    centroid = np.mean(embeddings_matrix, axis=0)

    # Calculate distances to centroid
    distances = np.linalg.norm(embeddings_matrix - centroid, axis=1)

    # Get indices of closest insights
    closest_indices = np.argsort(distances)[:n_insights]

    # Return insights sorted by distance to centroid
    return [insights[i] for i in closest_indices]

def generate_cluster_labeling(client: OpenAI, insights: List[Insight]) -> ClusterLabeling:
    """
    Generate label and summary for cluster using LLM

    Args:
        client: OpenAI client
        insights: List of insights from cluster

    Returns:
        ClusterLabeling with label and summary
    """
    # Prepare insights text
    insights_text = "\n".join([f"- {insight.insight_text}" for insight in insights])

    system_prompt = """You are analyzing user feedback to identify common themes.
Given a list of similar user complaints or feedback, generate:
1. A concise 2-3 word label that describes the main issue
2. A one-sentence summary (15-25 words) that describes what users are experiencing

Label rules:
- Use 2-3 words maximum
- Be specific and actionable
- Focus on the core problem or feature
- Examples: "Step Count Accuracy", "Syncing Issues", "Premium Pricing", "UI Navigation"

Summary rules:
- One sentence only (15-25 words)
- Describe the common problem users are experiencing
- Be specific about what's not working or what users want
- Examples: "Users report that the step counter is inaccurate and doesn't match their actual steps walked."
"""

    user_message = f"""Analyze these similar user feedback items:

{insights_text}"""

    completion = client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=ClusterLabeling,
    )

    return completion.choices[0].message.parsed

def label_clusters(
    company_name: str,
    insight_type: str = "pain_point",
    embedding_type: str = "reduced",
    n_components: int = 5,
    n_centroid_insights: int = 10,
    force: bool = False
) -> None:
    """
    Label all unlabeled clusters for given parameters

    Args:
        company_name: Company name to filter clusters
        insight_type: Type of insight        embedding_type: Embedding type
        n_components: Dimension count for reduced
        n_centroid_insights: Number of centroid insights to use for labeling
        force: Re-label clusters even if they already have labels
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

    # Find clusters to label
    print(f"\n🔍 Finding clusters to label...")
    print(f"   Type: {insight_type}")
    print(f"   Embedding: {embedding_type}" + (f" ({n_components}D)" if embedding_type == "reduced" else ""))
    print(f"   Force re-label: {force}")

    # Build query based on force flag
    query = select(Cluster).where(
        and_(
            Cluster.company_name == company_name,
            Cluster.insight_type == insight_type,
            Cluster.embedding_type == embedding_type
        )
    )

    # Only filter by NULL labels if not forcing
    if not force:
        query = query.where(Cluster.cluster_label.is_(None))

    if embedding_type == "reduced":
        query = query.where(Cluster.n_components == n_components)

    clusters = list(session.execute(query).scalars().all())

    if not clusters:
        if force:
            print("\n❌ No clusters found matching the criteria!")
        else:
            print("\n✅ All clusters already have labels!")
            print("   Use --force to re-label existing clusters")
        session.close()
        return

    # Count how many already have labels
    already_labeled = len([c for c in clusters if c.cluster_label is not None])
    unlabeled = len(clusters) - already_labeled

    if force and already_labeled > 0:
        print(f"✅ Found {len(clusters)} clusters ({unlabeled} unlabeled, {already_labeled} will be re-labeled)")
    else:
        print(f"✅ Found {len(clusters)} unlabeled clusters")
    print("="*60)

    # Label each cluster
    labeled = 0
    errors = 0

    for idx, cluster in enumerate(clusters, 1):
        try:
            relabel_indicator = " [RE-LABELING]" if cluster.cluster_label else ""
            print(f"\n[{idx}/{len(clusters)}] Cluster {cluster.id} ({cluster.size} insights){relabel_indicator}")

            if cluster.cluster_label:
                print(f"  📌 Current label: '{cluster.cluster_label}'")

            # Find centroid insights
            centroid_insights = find_centroid_insights(
                session, cluster.id, company_name, embedding_type, n_components, n_centroid_insights
            )

            if not centroid_insights:
                print(f"  ⚠️  No insights found (skipping)")
                continue

            # Limit to available insights
            actual_count = min(len(centroid_insights), n_centroid_insights)
            print(f"  📍 Using {actual_count} centroid insights")

            # Generate label and summary
            labeling = generate_cluster_labeling(client, centroid_insights[:actual_count])
            print(f"  🏷️  Label: '{labeling.label}'")
            print(f"  📝 Summary: {labeling.summary}")

            # Update database
            session.execute(
                update(Cluster).where(Cluster.id == cluster.id).values(
                    cluster_label=labeling.label,
                    cluster_summary=labeling.summary
                )
            )
            session.commit()

            labeled += 1

            # Show sample insight
            if centroid_insights:
                print(f"  └─ Sample: {centroid_insights[0].insight_text[:70]}...")

        except Exception as e:
            errors += 1
            print(f"  ❌ Error: {e}")
            session.rollback()
            continue

    # Close session
    session.close()

    # Summary
    print("\n" + "="*60)
    print("✅ LABELING COMPLETE")
    print("="*60)
    print(f"Clusters labeled: {labeled}")
    print(f"Errors: {errors}")
    print("="*60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Label clusters using LLM")
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
        "--n-insights",
        type=int,
        default=10,
        help="Number of centroid insights to use for labeling (default: 10)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-label clusters even if they already have labels"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'myfitnesspal')"
    )

    args = parser.parse_args()

    label_clusters(
        company_name=args.company,
        insight_type=args.type,
        embedding_type=args.embedding_type,
        n_components=args.dimensions,
        n_centroid_insights=args.n_insights,
        force=args.force
    )
