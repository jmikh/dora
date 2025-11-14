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
    insight_type: str = "pain_point",
    embedding_type: str = "original",
    n_components: int = 5
) -> Tuple[List[Insight], np.ndarray]:
    """
    Load insights that have embeddings

    Args:
        session: SQLAlchemy session
        insight_type: Type of insight to load
        embedding_type: 'original' or 'reduced'
        n_components: Number of dimensions (only for reduced)

    Returns:
        Tuple of (insights list, embeddings matrix)
    """
    from sqlalchemy import text

    # Determine which embedding column to use
    if embedding_type == "original":
        embedding_column = "embedding"
    else:
        embedding_column = f"reduced_embedding_{n_components}"

    # Build query dynamically since we need to check different columns
    query_text = f"""
        SELECT id, review_id, insight_text, insight_type, review_date,
               extracted_at, embedding, {embedding_column}
        FROM insights
        WHERE insight_type = :type
        AND {embedding_column} IS NOT NULL
        ORDER BY review_date DESC
    """

    result = session.execute(text(query_text), {"type": insight_type})
    rows = result.fetchall()

    if not rows:
        return [], np.array([])

    # Reconstruct Insight objects and extract embeddings
    insights = []
    embeddings = []

    for row in rows:
        from datetime import datetime as dt

        # Create Insight object from row data
        insight = Insight(
            id=row[0],
            review_id=row[1],
            insight_text=row[2],
            insight_type=row[3],
            review_date=dt.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
            extracted_at=dt.fromisoformat(row[5]) if isinstance(row[5], str) else row[5]
        )
        insights.append(insight)

        # Get the appropriate embedding
        if embedding_type == "original":
            embedding_vector = json.loads(row[6])  # embedding column
        else:
            embedding_vector = json.loads(row[7])  # reduced_embedding_N column

        embeddings.append(embedding_vector)

    embeddings_matrix = np.array(embeddings)

    return insights, embeddings_matrix


def cluster_insights(
    insight_type: str = "pain_point",
    min_cluster_size: int = 3,
    min_samples: int = 2,
    embedding_type: str = "original",
    n_components: int = 5
) -> None:
    """
    Cluster insights using HDBSCAN

    Args:
        insight_type: Type of insight to cluster
        min_cluster_size: Minimum size of clusters
        min_samples: Minimum samples in a neighborhood for core points
        embedding_type: 'original' or 'reduced'
        n_components: Number of dimensions for reduced embeddings
    """
    # Create database session
    session = get_session()
    print(f"📊 Connected to database")

    # Load insights with embeddings
    emb_desc = f"{n_components}-dim reduced" if embedding_type == "reduced" else "original 1536-dim"
    print(f"\n🔍 Loading {insight_type}s with {emb_desc} embeddings...")
    insights, embeddings = load_insights_with_embeddings(
        session, insight_type, embedding_type, n_components
    )
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
        default=5,
        help="Minimum size of clusters (default: 5)"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=3,
        help="Minimum samples in neighborhood (default: 3)"
    )
    parser.add_argument(
        "--embedding-type",
        type=str,
        default="original",
        choices=["original", "reduced"],
        help="Type of embedding to use: 'original' (1536-dim) or 'reduced' (UMAP)"
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=5,
        help="Number of dimensions for reduced embeddings (default: 5)"
    )

    args = parser.parse_args()

    cluster_insights(
        insight_type=args.type,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        embedding_type=args.embedding_type,
        n_components=args.dimensions
    )
