"""Publications and their feed-polling cursors."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    Cursor,
    Publication,
)
from second_brain.db.repositories.articles import count_articles_for_publication


async def upsert_publication(
    session: AsyncSession, *, slug: str, name: str, feed_url: str, homepage: str
) -> uuid.UUID:
    stmt = (
        insert(Publication)
        .values(id=uuid.uuid4(), slug=slug, name=name, feed_url=feed_url, homepage=homepage)
        .on_conflict_do_update(
            index_elements=[Publication.slug],
            set_={"name": name, "feed_url": feed_url, "homepage": homepage},
        )
        .returning(Publication.id)
    )
    return (await session.execute(stmt)).scalar_one()


async def get_publication_by_slug(session: AsyncSession, slug: str) -> Publication | None:
    return (
        await session.execute(select(Publication).where(Publication.slug == slug))
    ).scalar_one_or_none()


async def list_publications(session: AsyncSession) -> list[Publication]:
    return list((await session.execute(select(Publication))).scalars())


async def list_publications_with_stats(session: AsyncSession) -> list[dict[str, object]]:
    """List publications alongside article counts and cursor sync info."""
    pubs = await list_publications(session)
    results = []
    for pub in pubs:
        art_count = await count_articles_for_publication(session, pub.id)
        cursor = await get_cursor(session, pub.id)
        last_checked = (
            cursor.last_checked_at.isoformat() if cursor and cursor.last_checked_at else None
        )
        results.append(
            {
                "id": str(pub.id),
                "slug": pub.slug,
                "name": pub.name,
                "feed_url": pub.feed_url,
                "homepage": pub.homepage,
                "active": pub.active,
                "article_count": art_count,
                "last_checked_at": last_checked,
                "poll_count": cursor.poll_count if cursor else 0,
                "not_modified_count": cursor.not_modified_count if cursor else 0,
            }
        )
    return results


async def get_cursor(session: AsyncSession, publication_id: uuid.UUID) -> Cursor | None:
    stmt = select(Cursor).where(Cursor.publication_id == publication_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def update_cursor(
    session: AsyncSession,
    *,
    publication_id: uuid.UUID,
    etag: str | None,
    last_modified: str | None,
    not_modified: bool = False,
) -> None:
    """Update or insert publication polling cursor with conditional response metadata."""
    existing = await get_cursor(session, publication_id)
    if existing is None:
        cursor = Cursor(
            publication_id=publication_id,
            etag=etag,
            last_modified=last_modified,
            last_checked_at=datetime.now(),
            poll_count=1,
            not_modified_count=1 if not_modified else 0,
        )
        session.add(cursor)
    else:
        existing.poll_count += 1
        if not_modified:
            existing.not_modified_count += 1
        else:
            if etag:
                existing.etag = etag
            if last_modified:
                existing.last_modified = last_modified
        existing.last_checked_at = datetime.now()
