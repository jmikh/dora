#!/usr/bin/env python3
"""
Cluster insights using HDBSCAN based on embeddings
"""

import json
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy import select, delete, update, and_
from sqlalchemy.orm import Session
import hdbscan

from models import Insight, Cluster, get_session
from datetime import datetime


def clear_existing_clusters(
    session: Session,
    company_name: str,
    insight_type: str,
    embedding_type: str,
    n_components: int
) -> None:
    """
    Clear existing clusters and cluster assignments for the given parameters

    Args:
        session: SQLAlchemy session
        company_name: Company name
        insight_type: Type of insight
        embedding_type: Embedding type
        n_components: Number of components for reduced embeddings
    """
    from models import ClusterGroupAssignment

    # Build the WHERE clause based on embedding type
    conditions = [
        Cluster.company_name == company_name,
        Cluster.insight_type == insight_type,
        Cluster.embedding_type == embedding_type
    ]

    # For reduced embeddings, match n_components; for original, match NULL n_components
    if embedding_type == "reduced":
        conditions.append(Cluster.n_components == n_components)
    else:
        conditions.append(Cluster.n_components.is_(None))

    # Find clusters to delete
    clusters_to_delete = session.execute(
        select(Cluster.id).where(and_(*conditions))
    ).scalars().all()

    if clusters_to_delete:
        # 1. Delete cluster group assignments (foreign key dependency)
        session.execute(
            delete(ClusterGroupAssignment).where(
                ClusterGroupAssignment.cluster_id.in_(clusters_to_delete)
            )
        )

        # 2. Clear cluster_id from insights
        session.execute(
            update(Insight).where(
                Insight.cluster_id.in_(clusters_to_delete)
            ).values(cluster_id=None)
        )

        # 3. Delete clusters
        session.execute(
            delete(Cluster).where(Cluster.id.in_(clusters_to_delete))
        )
        session.commit()
        print(f"🗑️  Cleared {len(clusters_to_delete)} existing clusters")


def save_clusters_to_db(
    session: Session,
    company_name: str,
    insights: List[Insight],
    cluster_labels: np.ndarray,
    embeddings: np.ndarray,
    insight_type: str,
    embedding_type: str,
    n_components: int
) -> Dict[int, int]:
    """
    Save clusters to database and update insight cluster_ids

    Args:
        session: SQLAlchemy session
        company_name: Company name
        insights: List of insights
        cluster_labels: Cluster labels from HDBSCAN (-1 for noise)
        embeddings: Embedding matrix
        insight_type: Type of insight
        embedding_type: Embedding type
        n_components: Number of components

    Returns:
        Dict mapping cluster label to database cluster ID
    """
    # Organize insights by cluster
    clusters_map: Dict[int, List[Insight]] = {}
    for insight, label in zip(insights, cluster_labels):
        if label not in clusters_map:
            clusters_map[label] = []
        clusters_map[label].append(insight)

    # Create database entries for each cluster (excluding noise -1)
    label_to_db_id = {}

    for cluster_label in sorted(clusters_map.keys()):
        if cluster_label == -1:
            # Noise points don't get a cluster entry
            continue

        cluster_insights = clusters_map[cluster_label]

        # Create cluster record
        cluster = Cluster(
            company_name=company_name,
            insight_type=insight_type,
            embedding_type=embedding_type,
            n_components=n_components if embedding_type == "reduced" else None,
            size=len(cluster_insights),
            created_at=datetime.now()
        )
        session.add(cluster)
        session.flush()  # Get the ID

        label_to_db_id[cluster_label] = cluster.id

        # Update insights with cluster_id
        for insight in cluster_insights:
            session.execute(
                update(Insight).where(Insight.id == insight.id).values(cluster_id=cluster.id)
            )

    # Set noise points to NULL cluster_id
    if -1 in clusters_map:
        for insight in clusters_map[-1]:
            session.execute(
                update(Insight).where(Insight.id == insight.id).values(cluster_id=None)
            )

    session.commit()

    num_clusters = len([c for c in clusters_map.keys() if c != -1])
    print(f"💾 Saved {num_clusters} clusters to database")

    return label_to_db_id


def load_insights_with_embeddings(
    session: Session,
    company_name: str,
    insight_type: str = "pain_point",
    embedding_type: str = "original",
    n_components: int = 5
) -> Tuple[List[Insight], np.ndarray]:
    """
    Load insights that have embeddings

    Args:
        session: SQLAlchemy session
        company_name: Company name to filter insights
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
        WHERE company_name = :company
        AND insight_type = :type
        AND {embedding_column} IS NOT NULL
        ORDER BY review_date DESC
    """

    params = {"company": company_name, "type": insight_type}
    result = session.execute(text(query_text), params)
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
    company_name: str,
    insight_type: str = "pain_point",
    min_cluster_size: int = 3,
    min_samples: int = 2,
    embedding_type: str = "original",
    n_components: int = 5
) -> None:
    """
    Cluster insights using HDBSCAN

    Args:
        company_name: Company name to filter insights
        insight_type: Type of insight to cluster
        min_cluster_size: Minimum size of clusters
        min_samples: Minimum samples in a neighborhood for core points
        embedding_type: 'original' or 'reduced'
        n_components: Number of dimensions for reduced embeddings
    """
    # Create database session
    session = get_session()
    print(f"📊 Connected to database")
    print(f"🏢 Company: {company_name}")

    # Clear existing clusters for these parameters
    print(f"\n🗑️  Clearing existing clusters...")
    clear_existing_clusters(session, company_name, insight_type, embedding_type, n_components)

    # Load insights with embeddings
    emb_desc = f"{n_components}-dim reduced" if embedding_type == "reduced" else "original 1536-dim"
    print(f"\n🔍 Loading {insight_type}s with {emb_desc} embeddings...")
    insights, embeddings = load_insights_with_embeddings(
        session, company_name, insight_type, embedding_type, n_components
    )

    if len(insights) == 0:
        print(f"\n❌ No {insight_type}s with embeddings found!")
        print("Run generate_embeddings.py first.")
        session.close()
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

    # Save clusters to database
    print(f"\n💾 Saving clusters to database...")
    label_to_db_id = save_clusters_to_db(
        session, company_name, insights, cluster_labels, embeddings,
        insight_type, embedding_type, n_components
    )

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
            db_id = label_to_db_id.get(cluster_id, "N/A")
            print("="*80)
            print(f"CLUSTER {cluster_id} (DB ID: {db_id}) - {len(cluster_insights)} insights")
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
        db_id = label_to_db_id.get(cluster_id, "N/A")
        print(f"Cluster {cluster_id} (DB ID: {db_id}): {size} insights")

    if -1 in clusters:
        print(f"Noise: {len(clusters[-1])} insights")

    print("="*80)

    # Close session
    session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cluster insights using HDBSCAN")
    parser.add_argument(
        "--type",
        type=str,
        default="pain_point",
        help="Type of insight to cluster (e.g., pain_point, feature_request, praise, use_case)"
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
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'myfitnesspal')"
    )

    args = parser.parse_args()

    cluster_insights(
        company_name=args.company,
        insight_type=args.type,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        embedding_type=args.embedding_type,
        n_components=args.dimensions
    )
