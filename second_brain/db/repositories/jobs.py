"""Job progress, recorded failures, and LLM cost rows."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    Cost,
    Failure,
    Job,
)
from second_brain.db.repositories.articles import count_articles_for_publication_since


async def create_job(
    session: AsyncSession,
    *,
    event_id: str,
    kind: str,
    total: int,
    publication_id: uuid.UUID | None = None,
) -> None:
    stmt = (
        insert(Job)
        .values(
            event_id=event_id,
            kind=kind,
            status="running",
            total=total,
            done=0,
            publication_id=publication_id,
        )
        .on_conflict_do_nothing(index_elements=[Job.event_id])
    )
    await session.execute(stmt)


async def get_job(session: AsyncSession, event_id: str) -> Job | None:
    return (await session.execute(select(Job).where(Job.event_id == event_id))).scalar_one_or_none()


async def get_job_status(session: AsyncSession, event_id: str) -> dict[str, object] | None:
    """`done` is resolved from real article rows, not incremented by ingest-article
    (which never learns which discovery job triggered it — see the Job model's
    `publication_id` comment). Read-repairs `jobs.done` in the same query.

    Only articles written since the job started count towards it: a backfill of a
    publication that already has articles must not look finished before it starts.
    """
    job = await get_job(session, event_id)
    if job is None:
        return None
    done = (
        job.total
        if job.publication_id is None
        else min(
            await count_articles_for_publication_since(session, job.publication_id, job.created_at),
            job.total,
        )
    )
    done = max(done, job.done)
    if done != job.done:
        job.done = done
    if done >= job.total and job.status != "completed":
        job.status = "completed"
    return {
        "event_id": job.event_id,
        "kind": job.kind,
        "status": job.status,
        "total": job.total,
        "done": job.done,
    }


async def record_failure(
    session: AsyncSession,
    *,
    function_id: str,
    run_id: str,
    error: str,
    event_data: dict[str, object] | None = None,
) -> uuid.UUID:
    failure = Failure(
        id=uuid.uuid4(),
        function_id=function_id,
        run_id=run_id,
        error=error,
        event_data=event_data,
    )
    session.add(failure)
    await session.flush()
    return failure.id


async def list_recent_failures(session: AsyncSession, limit: int = 20) -> list[dict[str, object]]:
    """Return the most recent rows from the `failures` table for eval replay."""
    stmt = select(Failure).order_by(Failure.created_at.desc()).limit(limit)
    rows = list((await session.execute(stmt)).scalars())
    return [
        {
            "id": str(f.id),
            "function_id": f.function_id,
            "run_id": f.run_id,
            "error": f.error,
            "event_data": f.event_data,
            "created_at": f.created_at.isoformat(),
        }
        for f in rows
    ]


async def insert_cost(
    session: AsyncSession,
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    est_usd: float,
    article_id: uuid.UUID | None = None,
) -> None:
    session.add(
        Cost(
            id=uuid.uuid4(),
            article_id=article_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            est_usd=est_usd,
        )
    )
