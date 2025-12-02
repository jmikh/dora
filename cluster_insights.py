#!/usr/bin/env python3
"""
Cluster complaints or use cases using HDBSCAN based on embeddings
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Literal
from sqlalchemy import and_
import hdbscan

from models import (
    ComplaintEmbedding, UseCaseEmbedding,
    Complaint, UseCase,
    Cluster, Company, RedditContent, Review,
    get_session
)
from datetime import datetime


def clear_existing_clusters(
    session,
    company_name: str,
    embedding_type: str,
    n_components: int,
    cluster_type: str = "complaints"
) -> None:
    """
    Clear existing clusters and cluster assignments for the given parameters

    Args:
        session: SQLAlchemy session
        company_name: Company name
        embedding_type: Embedding type ('original' or 'reduced')
        n_components: Number of components for embeddings
        cluster_type: Type of clustering ('complaints' or 'use_cases')
    """
    from models import ClusterGroupAssignment

    # Build the WHERE clause based on embedding type
    conditions = [
        Cluster.company_name == company_name,
        Cluster.embedding_type == embedding_type,
        Cluster.cluster_type == cluster_type
    ]

    # For reduced embeddings, match n_components; for original, match 1536
    if embedding_type == "reduced":
        conditions.append(Cluster.n_components == n_components)
    else:
        conditions.append(Cluster.n_components == 1536)

    # Find clusters to delete
    from sqlalchemy import select, delete
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

        # 2. Delete clusters
        session.execute(
            delete(Cluster).where(Cluster.id.in_(clusters_to_delete))
        )
        session.commit()
        print(f"  Cleared {len(clusters_to_delete)} existing clusters")


def save_clusters_to_db(
    session,
    company_name: str,
    embeddings_list: List,
    cluster_labels: np.ndarray,
    embedding_type: str,
    n_components: int,
    cluster_type: str = "complaints"
) -> Dict[int, int]:
    """
    Save clusters to database

    Args:
        session: SQLAlchemy session
        company_name: Company name
        embeddings_list: List of embedding objects
        cluster_labels: Cluster labels from HDBSCAN (-1 for noise)
        embedding_type: Embedding type ('original' or 'reduced')
        n_components: Number of dimensions
        cluster_type: Type of clustering ('complaints' or 'use_cases')

    Returns:
        Dict mapping cluster label to database cluster ID
    """
    # Organize items by cluster
    clusters_map: Dict[int, List] = {}
    for emb, label in zip(embeddings_list, cluster_labels):
        if label not in clusters_map:
            clusters_map[label] = []
        clusters_map[label].append(emb)

    # Create database entries for each cluster (excluding noise -1)
    label_to_db_id = {}

    for cluster_label in sorted(clusters_map.keys()):
        if cluster_label == -1:
            # Noise points don't get a cluster entry
            continue

        cluster_items = clusters_map[cluster_label]

        # Create cluster record
        cluster = Cluster(
            company_name=company_name,
            insight_type=None,
            embedding_type=embedding_type,
            n_components=n_components,
            cluster_type=cluster_type,
            size=len(cluster_items),
            created_at=datetime.now()
        )
        session.add(cluster)
        session.flush()  # Get the ID

        label_to_db_id[cluster_label] = cluster.id

    session.commit()

    num_clusters = len([c for c in clusters_map.keys() if c != -1])
    print(f"  Saved {num_clusters} clusters to database")

    return label_to_db_id


def load_complaint_embeddings(
    session,
    company_name: str,
    dimensions: int = 50,
    category: str = None
) -> Tuple[List[ComplaintEmbedding], np.ndarray]:
    """Load complaint embeddings for a given company"""
    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found")
        return [], np.array([])

    # Get complaint IDs for this company from both Reddit and Reviews
    reddit_complaint_ids = (
        session.query(Complaint.id)
        .join(RedditContent, and_(
            Complaint.source_id == RedditContent.id,
            Complaint.source_table == 'reddit_content'
        ))
        .filter(RedditContent.company_id == company.id)
        .distinct()
    )

    review_complaint_ids = (
        session.query(Complaint.id)
        .join(Review, and_(
            Complaint.source_id == Review.review_id,
            Complaint.source_table == 'reviews'
        ))
        .filter(Review.company_id == company.id)
        .distinct()
    )

    # Combine complaint IDs
    all_ids = set()
    for cid_tuple in reddit_complaint_ids.all():
        all_ids.add(cid_tuple[0])
    for cid_tuple in review_complaint_ids.all():
        all_ids.add(cid_tuple[0])

    if not all_ids:
        return [], np.array([])

    # Filter by category if specified
    if category:
        import sqlite3
        conn = sqlite3.connect("dora.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT complaint_id FROM complaint_categories WHERE category = ?",
            (category,)
        )
        category_complaint_ids = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Intersect with company complaints
        all_ids = all_ids.intersection(category_complaint_ids)

        if not all_ids:
            return [], np.array([])

    # Load embeddings
    embeddings_list = (
        session.query(ComplaintEmbedding)
        .filter(
            ComplaintEmbedding.complaint_id.in_(all_ids),
            ComplaintEmbedding.dimensions == dimensions
        )
        .order_by(ComplaintEmbedding.complaint_id)
        .all()
    )

    if not embeddings_list:
        return [], np.array([])

    # Convert to numpy array
    embeddings = []
    for emb in embeddings_list:
        embedding_vector = json.loads(emb.embedding)
        embeddings.append(embedding_vector)

    return embeddings_list, np.array(embeddings)


def load_use_case_embeddings(
    session,
    company_name: str,
    dimensions: int = 50
) -> Tuple[List[UseCaseEmbedding], np.ndarray]:
    """Load use case embeddings for a given company"""
    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"Company '{company_name}' not found")
        return [], np.array([])

    # Get use case IDs for this company from both Reddit and Reviews
    reddit_use_case_ids = (
        session.query(UseCase.id)
        .join(RedditContent, and_(
            UseCase.source_id == RedditContent.id,
            UseCase.source_table == 'reddit_content'
        ))
        .filter(RedditContent.company_id == company.id)
        .distinct()
    )

    review_use_case_ids = (
        session.query(UseCase.id)
        .join(Review, and_(
            UseCase.source_id == Review.review_id,
            UseCase.source_table == 'reviews'
        ))
        .filter(Review.company_id == company.id)
        .distinct()
    )

    # Combine use case IDs
    all_ids = set()
    for uid_tuple in reddit_use_case_ids.all():
        all_ids.add(uid_tuple[0])
    for uid_tuple in review_use_case_ids.all():
        all_ids.add(uid_tuple[0])

    if not all_ids:
        return [], np.array([])

    # Load embeddings
    embeddings_list = (
        session.query(UseCaseEmbedding)
        .filter(
            UseCaseEmbedding.use_case_id.in_(all_ids),
            UseCaseEmbedding.dimensions == dimensions
        )
        .order_by(UseCaseEmbedding.use_case_id)
        .all()
    )

    if not embeddings_list:
        return [], np.array([])

    # Convert to numpy array
    embeddings = []
    for emb in embeddings_list:
        embedding_vector = json.loads(emb.embedding)
        embeddings.append(embedding_vector)

    return embeddings_list, np.array(embeddings)


def cluster_items(
    company_name: str,
    cluster_type: Literal["complaints", "use_cases"] = "complaints",
    min_cluster_size: int = 5,
    min_samples: int = 3,
    dimensions: int = 50,
    category: str = None
) -> None:
    """
    Cluster complaints or use cases using HDBSCAN

    Args:
        company_name: Company name to filter items
        cluster_type: Type to cluster ('complaints' or 'use_cases')
        min_cluster_size: Minimum size of clusters
        min_samples: Minimum samples in a neighborhood for core points
        dimensions: Dimension of embeddings to use (e.g., 1536, 50, 20)
        category: Optional LLM category to filter by (only for complaints)
    """
    # Create database session
    session = get_session()
    print(f"Connected to database")
    print(f"Company: {company_name}")
    print(f"Type: {cluster_type}")
    if category and cluster_type == "complaints":
        print(f"Filtering by category: \"{category}\"")

    # Determine embedding type
    embedding_type = "original" if dimensions == 1536 else "reduced"

    # Clear existing clusters for these parameters
    print(f"\nClearing existing clusters...")
    clear_existing_clusters(session, company_name, embedding_type, dimensions, cluster_type)

    # Load embeddings based on type
    print(f"\nLoading {cluster_type} embeddings ({dimensions}D)...")

    if cluster_type == "complaints":
        embeddings_list, embeddings = load_complaint_embeddings(
            session, company_name, dimensions, category
        )
        id_field = "complaint_id"
        text_field = "complaint_text"
        item_name = "complaint"
    else:
        embeddings_list, embeddings = load_use_case_embeddings(
            session, company_name, dimensions
        )
        id_field = "use_case_id"
        text_field = "use_case_text"
        item_name = "use_case"

    if len(embeddings_list) == 0:
        print(f"\nNo {cluster_type} with {dimensions}D embeddings found!")
        print("Run generate_embeddings.py and generate_reduced_embeddings.py first.")
        session.close()
        return

    print(f"Loaded {len(embeddings_list):,} {cluster_type} embeddings")
    print(f"Embedding dimension: {embeddings.shape[1]}")

    # Cluster using HDBSCAN
    print(f"\nClustering with HDBSCAN...")
    print(f"  min_cluster_size: {min_cluster_size}")
    print(f"  min_samples: {min_samples}")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method='eom'  # Excess of Mass
    )

    cluster_labels = clusterer.fit_predict(embeddings)

    # Save clusters to database
    print(f"\nSaving clusters to database...")
    label_to_db_id = save_clusters_to_db(
        session, company_name, embeddings_list, cluster_labels,
        embedding_type, dimensions, cluster_type
    )

    # Organize items by cluster
    clusters: Dict[int, List] = {}
    for emb, label in zip(embeddings_list, cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(emb)

    # Print results
    print("\n" + "=" * 80)
    print(f"CLUSTERING RESULTS ({cluster_type.upper()})")
    print("=" * 80)

    # Count clusters (excluding noise which is -1)
    num_clusters = len([c for c in clusters.keys() if c != -1])
    num_noise = len(clusters.get(-1, []))

    print(f"\nTotal {cluster_type}: {len(embeddings_list):,}")
    print(f"Number of clusters: {num_clusters}")
    print(f"Noise points (unclustered): {num_noise}")
    print()

    # Print each cluster
    for cluster_id in sorted(clusters.keys()):
        cluster_items = clusters[cluster_id]

        if cluster_id == -1:
            print("=" * 80)
            print(f"NOISE (Unclustered) - {len(cluster_items)} {cluster_type}")
            print("=" * 80)
        else:
            db_id = label_to_db_id.get(cluster_id, "N/A")
            print("=" * 80)
            print(f"CLUSTER {cluster_id} (DB ID: {db_id}) - {len(cluster_items)} {cluster_type}")
            print("=" * 80)

        for i, emb in enumerate(cluster_items, 1):
            item_id = getattr(emb, id_field)
            item_text = getattr(emb, text_field)

            print(f"\n{i}. [ID: {item_id}]")
            print(f"   {item_name.title()}: {item_text}")

            # Get quote from related object
            if cluster_type == "complaints":
                quote = emb.complaint.quote if emb.complaint else "N/A"
                source_id = emb.complaint.source_id if emb.complaint else None
                source_table = emb.complaint.source_table if emb.complaint else None
            else:
                quote = emb.use_case.quote if emb.use_case else "N/A"
                source_id = emb.use_case.source_id if emb.use_case else None
                source_table = emb.use_case.source_table if emb.use_case else None
            print(f"   Quote: \"{quote}\"")

            # Get full review/content
            if source_id and source_table:
                if source_table == "reviews":
                    review = session.query(Review).filter(Review.review_id == source_id).first()
                    if review and review.review_text:
                        print(f"   Full Review: \"{review.review_text}\"")
                elif source_table == "reddit_content":
                    reddit = session.query(RedditContent).filter(RedditContent.id == source_id).first()
                    if reddit:
                        full_text = f"{reddit.title or ''} {reddit.body or ''}".strip()
                        if full_text:
                            print(f"   Full Post: \"{full_text}\"")

        print()

    # Summary statistics
    print("=" * 80)
    print("CLUSTER SUMMARY")
    print("=" * 80)
    for cluster_id in sorted([c for c in clusters.keys() if c != -1]):
        size = len(clusters[cluster_id])
        db_id = label_to_db_id.get(cluster_id, "N/A")
        print(f"Cluster {cluster_id} (DB ID: {db_id}): {size} {cluster_type}")

    if -1 in clusters:
        print(f"Noise: {len(clusters[-1])} {cluster_type}")

    print("=" * 80)

    # Close session
    session.close()


# Backward compatibility
def cluster_complaints(
    company_name: str,
    min_cluster_size: int = 5,
    min_samples: int = 3,
    dimensions: int = 50,
    category: str = None
) -> None:
    """Backward compatible function for clustering complaints"""
    cluster_items(
        company_name=company_name,
        cluster_type="complaints",
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        dimensions=dimensions,
        category=category
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cluster complaints or use cases using HDBSCAN")
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'wispr')"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["complaints", "use_cases"],
        default="complaints",
        help="Type of items to cluster (default: complaints)"
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=50,
        help="Dimension of embeddings to use (default: 50)"
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
        "--category",
        type=str,
        help="Filter by LLM category (only for complaints)"
    )

    args = parser.parse_args()

    cluster_items(
        company_name=args.company,
        cluster_type=args.type,
        dimensions=args.dimensions,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        category=args.category
    )
