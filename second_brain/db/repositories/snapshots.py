"""Answer snapshots saved by POST /ask."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    Snapshot,
)


async def save_snapshot(
    session: AsyncSession,
    *,
    snapshot_id: str,
    question: str,
    answer_text: str,
    citations: list[dict[str, object]],
    retrieved: list[dict[str, object]],
    retriever_variant: str,
    as_of: datetime | None,
    latency_ms: int,
) -> None:
    session.add(
        Snapshot(
            snapshot_id=snapshot_id,
            question=question,
            answer_text=answer_text,
            citations=citations,
            retrieved=retrieved,
            retriever_variant=retriever_variant,
            as_of=as_of,
            latency_ms=latency_ms,
        )
    )


async def get_snapshot(session: AsyncSession, snapshot_id: str) -> Snapshot | None:
    stmt = select(Snapshot).where(Snapshot.snapshot_id == snapshot_id)
    return (await session.execute(stmt)).scalar_one_or_none()
