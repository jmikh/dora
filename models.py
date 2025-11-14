"""
SQLAlchemy models for Noom reviews database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, Session
from pathlib import Path

Base = declarative_base()

# Database file path
DB_FILE = Path(__file__).parent / "noom_playstore_reviews.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"


class Review(Base):
    """Review model - represents reviews table"""
    __tablename__ = "reviews"

    review_id = Column(Text, primary_key=True, nullable=False)
    user_name = Column(Text)
    rating = Column(Integer, nullable=False)
    helpful_votes = Column(Integer, default=0)
    date = Column(DateTime, nullable=False)
    review_text = Column(Text)
    reply_content = Column(Text)
    version = Column(Text)

    # Relationship to insights
    insights = relationship("Insight", back_populates="review")

    def __repr__(self):
        return f"<Review(id={self.review_id[:8]}, rating={self.rating}, date={self.date})>"


class Insight(Base):
    """Insight model - represents insights table"""
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Text, ForeignKey("reviews.review_id"), nullable=False)
    insight_text = Column(Text, nullable=False)
    insight_type = Column(Text, nullable=False)  # 'pain_point', 'feature_request', 'praise'
    review_date = Column(DateTime, nullable=False)
    extracted_at = Column(DateTime, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON string of embedding vector

    # Relationship to review
    review = relationship("Review", back_populates="insights")

    def __repr__(self):
        return f"<Insight(type={self.insight_type}, text={self.insight_text[:30]}...)>"


def get_engine():
    """Create and return SQLAlchemy engine"""
    return create_engine(DATABASE_URL, echo=False)


def get_session() -> Session:
    """Create and return a new session"""
    engine = get_engine()
    return Session(engine)
