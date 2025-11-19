#!/usr/bin/env python3
"""
Generate reduced-dimension embeddings using UMAP
"""

import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Tuple
from umap import UMAP
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from models import Insight, get_session, DB_FILE

def ensure_column_exists(conn: sqlite3.Connection, column_name: str) -> None:
    """
    Add reduced embedding column if it doesn't exist

    Args:
        conn: SQLite connection
        column_name: Name of column to create
    """
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(insights);")
    existing_columns = [col[1] for col in cursor.fetchall()]

    if column_name not in existing_columns:
        print(f"📝 Creating column '{column_name}'...")
        cursor.execute(f"""
            ALTER TABLE insights
            ADD COLUMN {column_name} TEXT;
        """)
        conn.commit()
        print(f"✅ Column '{column_name}' created")
    else:
        print(f"✓ Column '{column_name}' already exists")

def load_insights_with_embeddings(
    session: Session,
    company_name: str,
    insight_type: str) -> Tuple[List[Insight], np.ndarray]:
    """
    Load all insights with embeddings for a given type

    Args:
        session: SQLAlchemy session
        company_name: Company name to filter insights
        insight_type: Type of insight to load
    Returns:
        Tuple of (insights list, embeddings matrix)
    """
    query = (
        select(Insight)
        .where(Insight.company_name == company_name)
        .where(Insight.insight_type == insight_type)
        .where(Insight.embedding.isnot(None))
        .order_by(Insight.id)  # Important: maintain consistent order
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

def generate_reduced_embeddings(
    company_name: str,
    insight_type: str = "pain_point",
    n_components: int = 5,
    force: bool = False) -> None:
    """
    Generate reduced-dimension embeddings using UMAP

    Args:
        company_name: Company name to filter insights
        insight_type: Type of insight to process
        n_components: Number of dimensions for reduced embedding
        force: Regenerate even if column already has data
    """
    column_name = f"reduced_embedding_{n_components}"
    print(f"🏢 Company: {company_name}")
    print("="*60)

    # Create SQLAlchemy session
    session = get_session()

    # Create raw SQLite connection for schema changes
    raw_conn = sqlite3.connect(DB_FILE)

    # Ensure column exists
    ensure_column_exists(raw_conn, column_name)
    raw_conn.close()

    # Load insights with embeddings
    print(f"\n🔍 Loading {insight_type}s with embeddings...")
    insights, embeddings = load_insights_with_embeddings(session, company_name, insight_type)

    if len(insights) == 0:
        print("Run generate_embeddings.py first.")
        session.close()
        return

    print(f"✅ Loaded {len(insights):} {insight_type}s")
    print(f"   Original dimension: {embeddings.shape[1]}")
    # Check if we need to regenerate
    if not force:
        # Check how many already have reduced embeddings
        query = text(f"""
            SELECT COUNT(*)
            FROM insights
            WHERE insight_type = :type
            AND embedding IS NOT NULL
            AND {column_name} IS NOT NULL
        """)
        result = session.execute(query, {"type": insight_type})
        existing_count = result.scalar()

        if existing_count == len(insights):
            print(f"\n✅ All {insight_type}s (prompt v{prompt_version}) already have {n_components}-dim embeddings")
            print("Use --force to regenerate")
            session.close()
            return

    # Apply UMAP
    print(f"\n🔬 Applying UMAP to reduce {embeddings.shape[1]} → {n_components} dimensions...")
    print(f"   This may take a minute for {len(insights)} insights...")

    umap_model = UMAP(
        n_components=n_components,
        metric='cosine',
        n_neighbors=15,
        min_dist=0.1,
        random_state=42  # For reproducibility
    )

    reduced_embeddings = umap_model.fit_transform(embeddings)

    print(f"✅ UMAP complete. New shape: {reduced_embeddings.shape}")

    # Save reduced embeddings back to database
    print(f"\n💾 Saving {n_components}-dimensional embeddings to database...")

    raw_conn = sqlite3.connect(DB_FILE)
    cursor = raw_conn.cursor()

    for insight, reduced_emb in zip(insights, reduced_embeddings):
        # Convert numpy array to JSON
        reduced_emb_json = json.dumps(reduced_emb.tolist())

        cursor.execute(f"""
            UPDATE insights
            SET {column_name} = ?
            WHERE id = ?
        """, (reduced_emb_json, insight.id))

    raw_conn.commit()
    raw_conn.close()
    session.close()

    print(f"✅ Saved reduced embeddings to '{column_name}' column")

    # Summary
    print("\n" + "="*60)
    print("✅ REDUCED EMBEDDING GENERATION COMPLETE")
    print("="*60)
    print(f"Insight type: {insight_type}")
    print(f"Total processed: {len(insights):}")
    print(f"Dimensions: {embeddings.shape[1]} → {n_components}")
    print(f"Column: {column_name}")
    print("="*60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate reduced-dimension embeddings using UMAP")
    parser.add_argument(
        "--type",
        type=str,
        default="pain_point",
        help="Type of insight to process (e.g., pain_point, feature_request, praise, use_case)"
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=5,
        help="Number of dimensions for reduced embedding (default: 5)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if reduced embeddings already exist"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company name (e.g., 'noom', 'myfitnesspal')"
    )

    args = parser.parse_args()

    generate_reduced_embeddings(
        company_name=args.company,
        insight_type=args.type,
        n_components=args.dimensions,
        force=args.force)
