"""Passages: versioned writes and BM25 / dense retrieval."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    Article,
    Passage,
)


async def replace_passages(
    session: AsyncSession,
    *,
    article_id: uuid.UUID,
    passages: list[dict[str, object]],
) -> int:
    """Upsert by `(article_id, chunk_index)` — re-running produces zero new rows.

    `tsv` is a generated column (see the migration) and is never written here.
    """
    if not passages:
        return 0
    stmt = insert(Passage).values(
        [
            {
                "id": uuid.uuid4(),
                "article_id": article_id,
                "chunk_index": p["chunk_index"],
                "text": p["text"],
                "embedding": p["embedding"],
            }
            for p in passages
        ]
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Passage.article_id, Passage.chunk_index],
        index_where=Passage.valid_to.is_(None),
        set_={"text": stmt.excluded.text, "embedding": stmt.excluded.embedding},
    )
    await session.execute(stmt)
    return len(passages)


async def supersede_passages(session: AsyncSession, article_id: uuid.UUID) -> int:
    """Close active passages by setting valid_to = now(). History is preserved."""
    stmt = (
        update(Passage)
        .where(Passage.article_id == article_id, Passage.valid_to.is_(None))
        .values(valid_to=func.now())
    )
    result = await session.execute(stmt)
    return getattr(result, "rowcount", 0)


async def insert_passages_fresh(
    session: AsyncSession,
    *,
    article_id: uuid.UUID,
    passages: list[dict[str, object]],
) -> int:
    """Insert new passage versions without conflicting on previously superseded rows."""
    if not passages:
        return 0
    stmt = insert(Passage).values(
        [
            {
                "id": uuid.uuid4(),
                "article_id": article_id,
                "chunk_index": p["chunk_index"],
                "text": p["text"],
                "embedding": p["embedding"],
            }
            for p in passages
        ]
    )
    await session.execute(stmt)
    return len(passages)


async def count_passages(session: AsyncSession) -> int:
    return (await session.execute(select(func.count()).select_from(Passage))).scalar_one()


async def search_passages_bm25(
    session: AsyncSession, query: str, limit: int
) -> list[dict[str, object]]:
    """BM25 (tsvector) search, no LLM. Sparse half of the week-1 retrieval preview
    (`second_brain/retrieval/sparse.py`); fused with the dense half from week 2 on.
    """
    tsquery = func.websearch_to_tsquery("english", query)
    rank = func.ts_rank(Passage.tsv, tsquery)
    stmt = (
        select(
            Passage.id,
            Passage.text,
            Article.title,
            Article.author,
            Article.url,
            Article.published_at,
            rank.label("rank"),
        )
        .join(Article, Article.id == Passage.article_id)
        .where(Passage.tsv.op("@@")(tsquery), Passage.valid_to.is_(None))
        .order_by(rank.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "passage_id": str(row.id),
            "text": row.text,
            "title": row.title,
            "author": row.author,
            "url": row.url,
            "published_at": row.published_at.isoformat(),
            "rank": float(row.rank),
        }
        for row in rows
    ]


async def search_passages_dense(
    session: AsyncSession, query_embedding: list[float], limit: int
) -> list[dict[str, object]]:
    """Cosine-similarity search over `passages.embedding` (pgvector), no LLM.
    Dense half of the week-1 retrieval preview (`second_brain/retrieval/dense.py`); fused
    with the sparse half from week 2 on.
    """
    distance = Passage.embedding.cosine_distance(query_embedding)
    stmt = (
        select(
            Passage.id,
            Passage.text,
            Article.title,
            Article.author,
            Article.url,
            Article.published_at,
            distance.label("distance"),
        )
        .join(Article, Article.id == Passage.article_id)
        .where(Passage.valid_to.is_(None), Passage.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "passage_id": str(row.id),
            "text": row.text,
            "title": row.title,
            "author": row.author,
            "url": row.url,
            "published_at": row.published_at.isoformat(),
            # Cosine similarity, not distance — higher is more relevant, consistent
            # with search_passages_bm25's `rank` so callers don't special-case sign.
            "rank": 1.0 - float(row.distance),
        }
        for row in rows
    ]
