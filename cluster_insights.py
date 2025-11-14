#!/usr/bin/env python3
"""
Cluster insights using HDBSCAN based on embeddings
"""

import json
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
import hdbscan

from models import Insight, get_session


def load_insights_with_embeddings(
    session: Session,
    insight_type: str = "pain_point"
) -> Tuple[List[Insight], np.ndarray]:
    """
    Load insights that have embeddings

    Args:
        session: SQLAlchemy session
        insight_type: Type of insight to load

    Returns:
        Tuple of (insights list, embeddings matrix)
    """
    query = (
        select(Insight)
        .where(Insight.insight_type == insight_type)
        .where(Insight.embedding.isnot(None))
        .order_by(Insight.review_date.desc())
    )

    insights = list(session.execute(query).scalars().all())

    if not insights:
        return [], np.array([])

    # Convert JSON embeddings to numpy array
    embeddings = []
    for insight in insights:
        embedding_vector = json.loads(insight.embedding)
        embeddings.append(embedding_vector)

    embeddings_matrix = np.array(embeddings)

    return insights, embeddings_matrix


def cluster_insights(
    insight_type: str = "pain_point",
    min_cluster_size: int = 3,
    min_samples: int = 2
) -> None:
    """
    Cluster insights using HDBSCAN

    Args:
        insight_type: Type of insight to cluster
        min_cluster_size: Minimum size of clusters
        min_samples: Minimum samples in a neighborhood for core points
    """
    # Create database session
    session = get_session()
    print(f"📊 Connected to database")

    # Load insights with embeddings
    print(f"\n🔍 Loading {insight_type}s with embeddings...")
    insights, embeddings = load_insights_with_embeddings(session, insight_type)
    session.close()

    if len(insights) == 0:
        print(f"\n❌ No {insight_type}s with embeddings found!")
        print("Run generate_embeddings.py first.")
        return

    print(f"✅ Loaded {len(insights):,} {insight_type}s with embeddings")
    print(f"   Embedding dimension: {embeddings.shape[1]}")

    # Cluster using HDBSCAN
    print(f"\n🔬 Clustering with HDBSCAN...")
    print(f"   min_cluster_size: {min_cluster_size}")
    print(f"   min_samples: {min_samples}")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method='eom'  # Excess of Mass
    )

    cluster_labels = clusterer.fit_predict(embeddings)

    # Organize insights by cluster
    clusters: Dict[int, List[Insight]] = {}
    for insight, label in zip(insights, cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(insight)

    # Print results
    print("\n" + "="*80)
    print("CLUSTERING RESULTS")
    print("="*80)

    # Count clusters (excluding noise which is -1)
    num_clusters = len([c for c in clusters.keys() if c != -1])
    num_noise = len(clusters.get(-1, []))

    print(f"\nTotal insights: {len(insights):,}")
    print(f"Number of clusters: {num_clusters}")
    print(f"Noise points (unclustered): {num_noise}")
    print()

    # Print each cluster
    for cluster_id in sorted(clusters.keys()):
        cluster_insights = clusters[cluster_id]

        if cluster_id == -1:
            print("="*80)
            print(f"NOISE (Unclustered) - {len(cluster_insights)} insights")
            print("="*80)
        else:
            print("="*80)
            print(f"CLUSTER {cluster_id} - {len(cluster_insights)} insights")
            print("="*80)

        for i, insight in enumerate(cluster_insights, 1):
            print(f"\n{i}. [{insight.id}] (Date: {insight.review_date.date()})")
            print(f"   {insight.insight_text}")

        print()

    # Summary statistics
    print("="*80)
    print("CLUSTER SUMMARY")
    print("="*80)
    for cluster_id in sorted([c for c in clusters.keys() if c != -1]):
        size = len(clusters[cluster_id])
        print(f"Cluster {cluster_id}: {size} insights")

    if -1 in clusters:
        print(f"Noise: {len(clusters[-1])} insights")

    print("="*80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cluster insights using HDBSCAN")
    parser.add_argument(
        "--type",
        type=str,
        default="pain_point",
        choices=["pain_point", "feature_request", "praise"],
        help="Type of insight to cluster"
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=3,
        help="Minimum size of clusters (default: 5)"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=2,
        help="Minimum samples in neighborhood (default: 3)"
    )

    args = parser.parse_args()

    cluster_insights(
        insight_type=args.type,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples
    )
