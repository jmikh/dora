#!/usr/bin/env python3
"""
Generate reduced-dimension embeddings using UMAP for complaints or use cases
"""

import json
import numpy as np
from typing import List, Tuple, Literal
from umap import UMAP
from sqlalchemy import and_

from models import (
    ComplaintEmbedding, UseCaseEmbedding,
    Complaint, UseCase,
    Company, RedditContent, Review,
    get_session
)


def load_complaint_embeddings(
    session,
    company_name: str,
    source_dimensions: int = 1536
) -> Tuple[List[ComplaintEmbedding], np.ndarray]:
    """Load all complaint embeddings for a given company"""
    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"❌ Company '{company_name}' not found")
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

    # Load embeddings
    embeddings_list = (
        session.query(ComplaintEmbedding)
        .filter(
            ComplaintEmbedding.complaint_id.in_(all_ids),
            ComplaintEmbedding.dimensions == source_dimensions
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
    source_dimensions: int = 1536
) -> Tuple[List[UseCaseEmbedding], np.ndarray]:
    """Load all use case embeddings for a given company"""
    # Get company
    company = session.query(Company).filter(Company.name == company_name).first()
    if not company:
        print(f"❌ Company '{company_name}' not found")
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
            UseCaseEmbedding.dimensions == source_dimensions
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


def generate_reduced_embeddings(
    company_name: str,
    embedding_type: Literal["complaints", "use_cases"] = "complaints",
    target_dimensions: int = 50,
    source_dimensions: int = 1536,
    force: bool = False
) -> None:
    """
    Generate reduced-dimension embeddings using UMAP

    Args:
        company_name: Company name to filter items
        embedding_type: Type of embeddings to reduce ("complaints" or "use_cases")
        target_dimensions: Number of dimensions for reduced embedding (e.g., 50, 20)
        source_dimensions: Dimension of source embeddings (default: 1536)
        force: Regenerate even if reduced embeddings already exist
    """
    print(f"🏢 Company: {company_name}")
    print(f"📋 Type: {embedding_type}")
    print("=" * 60)

    # Create SQLAlchemy session
    session = get_session()

    # Load embeddings based on type
    print(f"\n🔍 Loading {embedding_type} embeddings ({source_dimensions}D)...")

    if embedding_type == "complaints":
        embeddings_list, embeddings = load_complaint_embeddings(
            session, company_name, source_dimensions
        )
        EmbeddingModel = ComplaintEmbedding
        id_field = "complaint_id"
        text_field = "complaint_text"
    else:
        embeddings_list, embeddings = load_use_case_embeddings(
            session, company_name, source_dimensions
        )
        EmbeddingModel = UseCaseEmbedding
        id_field = "use_case_id"
        text_field = "use_case_text"

    if len(embeddings_list) == 0:
        print(f"❌ No {source_dimensions}D embeddings found for {embedding_type}")
        print("Run generate_embeddings.py first.")
        session.close()
        return

    print(f"✅ Loaded {len(embeddings_list):,} {embedding_type} embeddings")
    print(f"   Original dimension: {embeddings.shape[1]}")

    # Check if we need to regenerate
    if not force:
        # Check how many already have reduced embeddings
        item_ids = [getattr(emb, id_field) for emb in embeddings_list]
        existing_reduced = (
            session.query(EmbeddingModel)
            .filter(
                getattr(EmbeddingModel, id_field).in_(item_ids),
                EmbeddingModel.dimensions == target_dimensions
            )
            .count()
        )

        if existing_reduced == len(embeddings_list):
            print(f"\n✅ All {embedding_type} already have {target_dimensions}D embeddings")
            print("Use --force to regenerate")
            session.close()
            return

        if existing_reduced > 0:
            print(f"\n⚠️  Found {existing_reduced} existing {target_dimensions}D embeddings")
            print(f"   Will create {len(embeddings_list) - existing_reduced} new ones")

    # Apply UMAP
    print(f"\n🔬 Applying UMAP to reduce {embeddings.shape[1]} → {target_dimensions} dimensions...")
    print(f"   This may take a minute for {len(embeddings_list):,} items...")

    umap_model = UMAP(
        n_components=target_dimensions,
        metric='cosine',
        n_neighbors=min(15, len(embeddings_list) - 1),  # Handle small datasets
        min_dist=0.1,
        random_state=42  # For reproducibility
    )

    reduced_embeddings = umap_model.fit_transform(embeddings)

    print(f"✅ UMAP complete. New shape: {reduced_embeddings.shape}")

    # Save reduced embeddings back to database
    print(f"\n💾 Saving {target_dimensions}D embeddings to database...")

    processed = 0
    skipped = 0

    for emb_obj, reduced_emb in zip(embeddings_list, reduced_embeddings):
        item_id = getattr(emb_obj, id_field)
        item_text = getattr(emb_obj, text_field)

        # Check if this embedding already exists
        if not force:
            existing = session.query(EmbeddingModel).filter(
                getattr(EmbeddingModel, id_field) == item_id,
                EmbeddingModel.dimensions == target_dimensions
            ).first()

            if existing:
                skipped += 1
                continue

        # Convert numpy array to JSON
        reduced_emb_json = json.dumps(reduced_emb.tolist())

        # Create new embedding entry
        if embedding_type == "complaints":
            new_embedding = ComplaintEmbedding(
                complaint_id=item_id,
                complaint_text=item_text,
                dimensions=target_dimensions,
                embedding=reduced_emb_json
            )
        else:
            new_embedding = UseCaseEmbedding(
                use_case_id=item_id,
                use_case_text=item_text,
                dimensions=target_dimensions,
                embedding=reduced_emb_json
            )

        session.add(new_embedding)
        processed += 1

        if processed % 100 == 0:
            print(f"   [{processed}/{len(embeddings_list)}] Saved...")
            session.commit()

    session.commit()
    session.close()

    print(f"✅ Saved {processed:,} reduced embeddings")
    if skipped > 0:
        print(f"   Skipped {skipped:,} existing embeddings")

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ REDUCED EMBEDDING GENERATION COMPLETE ({embedding_type.upper()})")
    print("=" * 60)
    print(f"Company: {company_name}")
    print(f"Total items: {len(embeddings_list):,}")
    print(f"Embeddings created: {processed:,}")
    print(f"Dimensions: {source_dimensions} → {target_dimensions}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate reduced-dimension embeddings using UMAP")
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
        help="Type of embeddings to reduce (default: complaints)"
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=50,
        help="Target number of dimensions for reduced embedding (default: 50)"
    )
    parser.add_argument(
        "--source-dimensions",
        type=int,
        default=1536,
        help="Dimension of source embeddings to reduce from (default: 1536)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if reduced embeddings already exist"
    )

    args = parser.parse_args()

    generate_reduced_embeddings(
        company_name=args.company,
        embedding_type=args.type,
        target_dimensions=args.dimensions,
        source_dimensions=args.source_dimensions,
        force=args.force
    )
