"""Claims: persistence, supersession, and source provenance."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    Article,
    Claim,
    Passage,
    Publication,
)


async def count_active_claims(session: AsyncSession) -> int:
    """Count active claims (`valid_to IS NULL`) in Postgres."""
    stmt = select(func.count()).select_from(Claim).where(Claim.valid_to.is_(None))
    return (await session.execute(stmt)).scalar_one()


async def get_active_claims_for_article(
    session: AsyncSession, article_id: uuid.UUID
) -> list[Claim]:
    """Return all currently active claims for an article."""
    stmt = select(Claim).where(Claim.article_id == article_id, Claim.valid_to.is_(None))
    return list((await session.execute(stmt)).scalars())


async def persist_article_claims(
    session: AsyncSession,
    *,
    article_id: uuid.UUID,
    claims: list[dict[str, object]],
    now: datetime,
) -> list[dict[str, str]]:
    """Supersede stale active claims for `article_id` and upsert the newly validated
    claims. Returns `supersedes_pairs` (`[{new_claim_id, old_claim_id, at}]`) so
    Memgraph can merge `[:SUPERSEDES]` edges for topic-overlapping revisions.
    """
    existing_active = await get_active_claims_for_article(session, article_id)
    incoming_ids = {uuid.UUID(str(c["claim_id"])) for c in claims}

    # Any active claim not in the new batch belongs to a prior revision and is superseded
    stale_claims = [old for old in existing_active if old.id not in incoming_ids]
    if stale_claims:
        stale_ids = [old.id for old in stale_claims]
        await session.execute(update(Claim).where(Claim.id.in_(stale_ids)).values(valid_to=now))

    # Map topic slug -> most recent superseded claim id so new claims on the same
    # topic can link via supersedes_id / [:SUPERSEDES]
    topic_to_old_claim_id: dict[str, uuid.UUID] = {}
    for old in stale_claims:
        for ent in old.entities or []:
            if isinstance(ent, dict) and ent.get("slug"):
                topic_to_old_claim_id[str(ent["slug"])] = old.id

    supersedes_pairs: list[dict[str, str]] = []
    now_iso = now.isoformat()

    for c in claims:
        cid = uuid.UUID(str(c["claim_id"]))
        topics_list = c.get("topics", [])
        entities_json: list[dict[str, str]] = (
            [
                {"slug": str(t["slug"]), "name": str(t["name"])}
                for t in topics_list
                if isinstance(t, dict) and "slug" in t and "name" in t
            ]
            if isinstance(topics_list, list)
            else []
        )

        supersedes_uuid: uuid.UUID | None = None
        for ent in entities_json:
            old_id = topic_to_old_claim_id.get(ent["slug"])
            if old_id is not None and old_id != cid:
                supersedes_uuid = old_id
                supersedes_pairs.append(
                    {
                        "new_claim_id": str(cid),
                        "old_claim_id": str(old_id),
                        "at": now_iso,
                    }
                )
                break

        stmt = (
            insert(Claim)
            .values(
                id=cid,
                article_id=article_id,
                text=str(c["text"]),
                quote_span=str(c["quote_span"]),
                claim_type=str(c["claim_type"]),
                entities=entities_json,
                confidence=float(str(c.get("confidence", 0.9))),
                valid_from=now,
                valid_to=None,
                supersedes_id=supersedes_uuid,
            )
            .on_conflict_do_update(
                index_elements=[Claim.id],
                set_={
                    "text": str(c["text"]),
                    "quote_span": str(c["quote_span"]),
                    "claim_type": str(c["claim_type"]),
                    "entities": entities_json,
                    "confidence": float(str(c.get("confidence", 0.9))),
                    "valid_to": None,
                    "supersedes_id": supersedes_uuid,
                },
            )
        )
        await session.execute(stmt)

    return supersedes_pairs


async def find_matching_passage_for_quote(
    session: AsyncSession,
    *,
    article_id: uuid.UUID,
    quote_span: str,
) -> dict[str, object] | None:
    """Resolve an active Postgres passage from `article_id` containing `quote_span`
    (falling back to the first active passage of the article if the quote spans a
    chunk boundary).
    """
    stmt = (
        select(
            Passage.id,
            Passage.text,
            Passage.chunk_index,
            Article.title,
            Article.author,
            Article.url,
            Article.published_at,
        )
        .join(Article, Article.id == Passage.article_id)
        .where(Passage.article_id == article_id, Passage.valid_to.is_(None))
        .order_by(Passage.chunk_index.asc())
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return None

    norm_quote = " ".join(quote_span.split()).strip().lower()
    probe = norm_quote[:60] if len(norm_quote) > 60 else norm_quote

    chosen = rows[0]
    for row in rows:
        norm_passage = " ".join(str(row.text).split()).strip().lower()
        if norm_quote in norm_passage or (probe and probe in norm_passage):
            chosen = row
            break

    return {
        "passage_id": str(chosen.id),
        "text": chosen.text,
        "title": chosen.title,
        "author": chosen.author,
        "url": chosen.url,
        "published_at": chosen.published_at.isoformat(),
    }


async def get_source_provenance(
    session: AsyncSession, target_id: uuid.UUID
) -> dict[str, object] | None:
    """Look up full lineage for a `claim_id` or `passage_id` for `second_brain_sources`."""
    claim_stmt = (
        select(Claim, Article, Publication)
        .join(Article, Article.id == Claim.article_id)
        .join(Publication, Publication.id == Article.publication_id)
        .where(Claim.id == target_id)
    )
    claim_row = (await session.execute(claim_stmt)).first()
    if claim_row is not None:
        claim, article, pub = claim_row
        return {
            "kind": "claim",
            "id": str(claim.id),
            "article": {
                "article_id": str(article.id),
                "canonical_id": article.canonical_id,
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "content_hash": article.content_hash,
            },
            "publication": {
                "slug": pub.slug,
                "name": pub.name,
                "homepage": pub.homepage,
            },
            "author": article.author or "Unknown Author",
            "verbatim_quote": claim.quote_span,
            "claim_text": claim.text,
            "claim_type": claim.claim_type,
            "confidence": float(claim.confidence),
            "topics": list(claim.entities or []),
            "validity": {
                "valid_from": claim.valid_from.isoformat(),
                "valid_to": claim.valid_to.isoformat() if claim.valid_to else None,
                "is_active": claim.valid_to is None,
                "supersedes_id": str(claim.supersedes_id) if claim.supersedes_id else None,
            },
        }

    passage_stmt = (
        select(Passage, Article, Publication)
        .join(Article, Article.id == Passage.article_id)
        .join(Publication, Publication.id == Article.publication_id)
        .where(Passage.id == target_id)
    )
    passage_row = (await session.execute(passage_stmt)).first()
    if passage_row is not None:
        passage, article, pub = passage_row
        return {
            "kind": "passage",
            "id": str(passage.id),
            "chunk_index": passage.chunk_index,
            "article": {
                "article_id": str(article.id),
                "canonical_id": article.canonical_id,
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "content_hash": article.content_hash,
            },
            "publication": {
                "slug": pub.slug,
                "name": pub.name,
                "homepage": pub.homepage,
            },
            "author": article.author or "Unknown Author",
            "verbatim_quote": passage.text,
            "validity": {
                "valid_from": passage.valid_from.isoformat(),
                "valid_to": passage.valid_to.isoformat() if passage.valid_to else None,
                "is_active": passage.valid_to is None,
                "supersedes_id": None,
            },
        }

    return None
