#!/usr/bin/env python3
"""
Build hierarchical cluster dendrogram using Agglomerative Clustering
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from typing import List, Tuple, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from models import Cluster, Insight, get_session

def load_cluster_centroids(
    session: Session,
    company_name: str,
    insight_type: str,
    embedding_type: str,
    n_components: Optional[int]
) -> Tuple[List[Cluster], np.ndarray]:
    """
    Load clusters and calculate their centroids from insight embeddings

    Args:
        session: SQLAlchemy session
        company_name: Company name to filter clusters
        insight_type: Type of insight        embedding_type: Embedding type
        n_components: Dimension count for reduced embeddings

    Returns:
        Tuple of (clusters list, centroids matrix)
    """
    from sqlalchemy import text

    # Determine embedding column
    if embedding_type == "original":
        embedding_column = "embedding"
    else:
        embedding_column = f"reduced_embedding_{n_components}"

    # Find all clusters matching criteria
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

    if not clusters:
        return [], np.array([])

    # Calculate centroid for each cluster
    centroids = []

    for cluster in clusters:
        # Load all insights in this cluster with embeddings
        query_text = f"""
            SELECT {embedding_column}
            FROM insights
            WHERE cluster_id = :cluster_id
            AND {embedding_column} IS NOT NULL
        """

        result = session.execute(text(query_text), {"cluster_id": cluster.id})
        rows = result.fetchall()

        if not rows:
            # Skip clusters with no embeddings
            continue

        # Extract embeddings and calculate centroid
        embeddings = [json.loads(row[0]) for row in rows]
        embeddings_matrix = np.array(embeddings)
        centroid = np.mean(embeddings_matrix, axis=0)
        centroids.append(centroid)

    centroids_matrix = np.array(centroids)

    return clusters, centroids_matrix

def plot_dendrogram(
    linkage_matrix: np.ndarray,
    clusters: List[Cluster],
    output_file: str = "dendrogram.png",
    figsize: Tuple[int, int] = (15, 10)
) -> None:
    """
    Plot and save dendrogram

    Args:
        linkage_matrix: Linkage matrix from hierarchical clustering
        clusters: List of clusters
        output_file: Output filename
        figsize: Figure size
    """
    plt.figure(figsize=figsize)

    # Create labels with cluster info
    labels = []
    for cluster in clusters:
        label = cluster.cluster_label or f"Cluster {cluster.id}"
        labels.append(f"{label} ({cluster.size})")

    # Plot dendrogram
    dendrogram(
        linkage_matrix,
        labels=labels,
        leaf_rotation=90,
        leaf_font_size=8
    )

    plt.title("Hierarchical Clustering Dendrogram", fontsize=14, fontweight='bold')
    plt.xlabel("Cluster (Label and Size)", fontsize=12)
    plt.ylabel("Distance", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Dendrogram saved to: {output_file}")

def generate_text_hierarchy(
    linkage_matrix: np.ndarray,
    clusters: List[Cluster],
    threshold: float
) -> str:
    """
    Generate text representation of hierarchy

    Args:
        linkage_matrix: Linkage matrix
        clusters: List of clusters
        threshold: Distance threshold for grouping

    Returns:
        Text hierarchy report
    """
    from scipy.cluster.hierarchy import fcluster

    # Cut dendrogram at threshold to get groups
    groups = fcluster(linkage_matrix, threshold, criterion='distance')

    # Organize clusters by group
    cluster_groups = {}
    for idx, group_id in enumerate(groups):
        if group_id not in cluster_groups:
            cluster_groups[group_id] = []
        cluster_groups[group_id].append(clusters[idx])

    # Build text report
    report = []
    report.append("=" * 80)
    report.append("HIERARCHICAL CLUSTER GROUPS")
    report.append("=" * 80)
    report.append(f"Distance threshold: {threshold:.2f}")
    report.append(f"Number of groups: {len(cluster_groups)}")
    report.append("")

    for group_id in sorted(cluster_groups.keys()):
        group_clusters = cluster_groups[group_id]
        total_insights = sum(c.size for c in group_clusters)

        report.append("=" * 80)
        report.append(f"GROUP {group_id} - {len(group_clusters)} clusters, {total_insights} insights")
        report.append("=" * 80)

        for cluster in sorted(group_clusters, key=lambda c: c.size, reverse=True):
            label = cluster.cluster_label or f"Cluster {cluster.id}"
            summary = cluster.cluster_summary or "No summary"
            report.append(f"\n  • {label} ({cluster.size} insights)")
            report.append(f"    {summary}")

        report.append("")

    return "\n".join(report)

def hierarchical_clustering_analysis(
    company_name: str,
    insight_type: str = "pain_point",
    embedding_type: str = "reduced",
    n_components: int = 5,
    linkage_method: str = "ward",
    distance_threshold: float = None
) -> None:
    """
    Perform hierarchical clustering analysis on existing clusters

    Args:
        company_name: Company name to filter clusters
        insight_type: Type of insight        embedding_type: Embedding type
        n_components: Dimension count for reduced
        linkage_method: Linkage method (ward, average, complete, single)
        distance_threshold: Distance threshold for cutting dendrogram (auto if None)
    """
    # Create database session
    session = get_session()
    print(f"📊 Connected to database")
    print(f"🏢 Company: {company_name}")

    # Load clusters and calculate centroids
    print(f"\n🔍 Loading clusters...")
    print(f"   Type: {insight_type}")
    print(f"   Embedding: {embedding_type}" + (f" ({n_components}D)" if embedding_type == "reduced" else ""))

    clusters, centroids = load_cluster_centroids(
        session, company_name, insight_type, prompt_version, embedding_type, n_components
    )

    session.close()

    if len(clusters) == 0:
        print("\n❌ No clusters found!")
        print("Run cluster_insights.py first.")
        return

    if len(clusters) < 2:
        print(f"\n⚠️  Only {len(clusters)} cluster found. Need at least 2 for hierarchy.")
        return

    print(f"✅ Loaded {len(clusters)} clusters")
    print(f"   Centroid dimension: {centroids.shape[1]}")

    # Perform hierarchical clustering
    print(f"\n🌲 Building hierarchy using '{linkage_method}' linkage...")

    linkage_matrix = linkage(centroids, method=linkage_method)

    print(f"✅ Hierarchy built")

    # Auto-calculate threshold if not provided
    if distance_threshold is None:
        # Use 70th percentile of distances as default threshold
        distances = linkage_matrix[:, 2]
        distance_threshold = np.percentile(distances, 70)
        print(f"   Auto-calculated threshold: {distance_threshold:.2f}")

    # Generate outputs
    print(f"\n📈 Generating outputs...")

    # 1. Save dendrogram plot
    output_base = f"hierarchy_{insight_type}_{embedding_type}"
    if embedding_type == "reduced":
        output_base += f"_{n_components}d"

    plot_file = f"{output_base}_dendrogram.png"
    plot_dendrogram(linkage_matrix, clusters, plot_file)

    # 2. Generate text hierarchy
    text_report = generate_text_hierarchy(linkage_matrix, clusters, distance_threshold)
    print(f"\n{text_report}")

    # 3. Save text report
    report_file = f"{output_base}_report.txt"
    with open(report_file, "w") as f:
        f.write(text_report)
    print(f"📄 Report saved to: {report_file}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ HIERARCHICAL ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Clusters analyzed: {len(clusters)}")
    print(f"Linkage method: {linkage_method}")
    print(f"Distance threshold: {distance_threshold:.2f}")
    print("=" * 80)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build hierarchical cluster dendrogram using Agglomerative Clustering"
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
        "--linkage",
        type=str,
        default="ward",
        choices=["ward", "average", "complete", "single"],
        help="Linkage method (default: ward)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        help="Distance threshold for cutting dendrogram (auto if not specified)"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'myfitnesspal')"
    )

    args = parser.parse_args()

    hierarchical_clustering_analysis(
        company_name=args.company,
        insight_type=args.type,
        embedding_type=args.embedding_type,
        n_components=args.dimensions,
        linkage_method=args.linkage,
        distance_threshold=args.threshold
    )
