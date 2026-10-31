"""Reachability checks for `GET /health` (second_brain/main.py) and `second_brain_health`
(second_brain/mcp/tools.py)."""

from __future__ import annotations

import httpx
from sqlalchemy import text

from second_brain.config import settings
from second_brain.db.repositories import count_active_claims, count_articles, count_passages
from second_brain.db.session import get_session
from second_brain.graph.client import check_memgraph_health, count_graph_entities


async def check_health() -> dict[str, object]:
    checks: dict[str, str] = {}

    # Each subsystem check is isolated and broad-caught on purpose: a health
    # check must report *which* dependency is down, not raise itself.
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    try:
        async with httpx.AsyncClient(timeout=3.0) as http_client:
            response = await http_client.get(settings.inngest_base_url)
            response.raise_for_status()
        checks["inngest"] = "ok"
    except httpx.HTTPError as exc:
        checks["inngest"] = f"error: {exc}"

    try:
        checks["memgraph"] = await check_memgraph_health()
    except Exception as exc:  # noqa: BLE001
        checks["memgraph"] = f"error: {exc}"

    # Counts are only published once every query for that store succeeds, so a
    # failure partway through leaves them at 0 instead of a partial mix.
    articles = passages = claims = topics = 0
    if checks["database"] == "ok":
        try:
            async with get_session() as session:
                db_counts = (
                    await count_articles(session),
                    await count_passages(session),
                    await count_active_claims(session),
                )
            articles, passages, claims = db_counts
        except Exception as exc:  # noqa: BLE001
            checks["database"] = f"error: {exc}"

    if checks["memgraph"] == "ok":
        try:
            graph_claims, graph_topics = await count_graph_entities()
            claims, topics = max(claims, graph_claims), graph_topics
        except Exception as exc:  # noqa: BLE001
            checks["memgraph"] = f"error: {exc}"

    overall_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ok" if overall_ok else "degraded",
        **checks,
        "articles": articles,
        "passages": passages,
        "claims": claims,
        "topics": topics,
    }
