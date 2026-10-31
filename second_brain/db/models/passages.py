"""Versioned, embedded article chunks used for retrieval."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from second_brain.config import settings
from second_brain.db.models.base import Base

if TYPE_CHECKING:
    from second_brain.db.models.articles import Article


class Passage(Base):
    __tablename__ = "passages"
    __table_args__ = (
        Index(
            "uq_passages_article_chunk",
            "article_id",
            "chunk_index",
            unique=True,
            postgresql_where=text("valid_to IS NULL"),
        ),
        Index("ix_passages_tsv", "tsv", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimensions), nullable=True
    )
    # Generated column (STORED) — written by hand in the migration, not autogenerate.
    tsv: Mapped[str] = mapped_column(TSVECTOR, nullable=True)
    # Temporal validity: a passage with `valid_to` set is no longer current.
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    article: Mapped[Article] = relationship(back_populates="passages")
