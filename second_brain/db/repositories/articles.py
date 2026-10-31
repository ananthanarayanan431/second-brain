"""Articles: upserts, lookups, and counts."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    Article,
    Publication,
)


async def upsert_article(
    session: AsyncSession,
    *,
    canonical_id: str,
    publication_id: uuid.UUID,
    url: str,
    title: str,
    author: str | None,
    published_at: datetime,
    content_hash: str,
    text: str,
) -> uuid.UUID:
    """Upsert by `canonical_id` — the dedupe key across every ingestion path."""
    stmt = (
        insert(Article)
        .values(
            id=uuid.uuid4(),
            canonical_id=canonical_id,
            publication_id=publication_id,
            url=url,
            title=title,
            author=author,
            published_at=published_at,
            content_hash=content_hash,
            text=text,
        )
        .on_conflict_do_update(
            index_elements=[Article.canonical_id],
            set_={
                "title": title,
                "author": author,
                "published_at": published_at,
                "content_hash": content_hash,
                "text": text,
                "updated_at": func.now(),
            },
        )
        .returning(Article.id)
    )
    return (await session.execute(stmt)).scalar_one()


async def get_existing_canonical_ids(session: AsyncSession, canonical_ids: list[str]) -> set[str]:
    """Which of these articles are already stored?"""
    stmt = select(Article.canonical_id).where(Article.canonical_id.in_(canonical_ids))
    return set((await session.execute(stmt)).scalars())


async def get_article_by_canonical_id(session: AsyncSession, canonical_id: str) -> Article | None:
    stmt = select(Article).where(Article.canonical_id == canonical_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_article_with_publication(
    session: AsyncSession, article_id: uuid.UUID
) -> tuple[Article, Publication] | None:
    """Fetch an Article alongside its parent Publication."""
    stmt = (
        select(Article, Publication)
        .join(Publication, Publication.id == Article.publication_id)
        .where(Article.id == article_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return row[0], row[1]


async def count_articles(session: AsyncSession) -> int:
    return (await session.execute(select(func.count()).select_from(Article))).scalar_one()


async def count_articles_for_publication(session: AsyncSession, publication_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Article).where(Article.publication_id == publication_id)
    return (await session.execute(stmt)).scalar_one()


async def count_articles_for_publication_since(
    session: AsyncSession, publication_id: uuid.UUID, since: datetime
) -> int:
    """Articles of a publication created or updated at or after `since`."""
    stmt = (
        select(func.count())
        .select_from(Article)
        .where(Article.publication_id == publication_id, Article.updated_at >= since)
    )
    return (await session.execute(stmt)).scalar_one()
