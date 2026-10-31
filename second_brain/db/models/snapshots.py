"""Answer snapshots saved by POST /ask."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from second_brain.db.models.base import Base


class Snapshot(Base):
    """One row per answer from `POST /ask`: what was asked, what was answered, and
    EVERY candidate passage the retriever surfaced (not only the cited ones), with
    its rank in each search engine. That is what lets us tell, later, whether a bad
    answer came from ingestion, retrieval or generation.
    """

    __tablename__ = "snapshots"

    snapshot_id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    retrieved: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    retriever_variant: Mapped[str] = mapped_column(String, nullable=False)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Filled in by the evaluators in week 5; always NULL in week 2.
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
