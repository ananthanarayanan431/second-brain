"""Eval results and eval suite runs."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from second_brain.db.models.base import Base


class EvalResult(Base):
    """One row per evaluated `Snapshot`, written by `evaluate-answer` (Week 5).
    Records both deterministic code assertions and narrow binary LLM judge verdicts.
    """

    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[str] = mapped_column(
        String, ForeignKey("snapshots.snapshot_id"), unique=True, nullable=False
    )
    deterministic_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checks: Mapped[dict[str, bool]] = mapped_column(JSONB, nullable=False, default=dict)
    faithfulness_verdict: Mapped[str] = mapped_column(String, nullable=False)
    faithfulness_critique: Mapped[str] = mapped_column(Text, nullable=False)
    disagreement_verdict: Mapped[str] = mapped_column(String, nullable=False)
    disagreement_critique: Mapped[str] = mapped_column(Text, nullable=False)
    failure_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    composite_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvalRun(Base):
    """One row per benchmark experiment or failure replay run (`run-eval-suite`)."""

    __tablename__ = "eval_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    suite_name: Mapped[str] = mapped_column(String, nullable=False)
    variants_summary: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    case_results: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
