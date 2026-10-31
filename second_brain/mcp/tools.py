"""The ten MCP tools (weeks 3–4).

Fast reads (`second_brain_health`, `second_brain_search`, `second_brain_ask`,
`second_brain_list_publications`, `second_brain_job_status`, `second_brain_sources`)
hit Postgres, Memgraph, and retrieval engines directly and return in under a
second — no Inngest run is created for them. Slow work (`second_brain_add_publication`,
`second_brain_backfill`, `second_brain_sync`) sends an event to Inngest and returns a
handle immediately; progress is polled with `second_brain_job_status`.
"""

from __future__ import annotations

import typing
import uuid

import httpx
import inngest
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from second_brain.config import settings
from second_brain.db.repositories import (
    get_job_status,
    get_latest_eval_report,
    get_source_provenance,
    list_publications_with_stats,
)
from second_brain.db.session import get_session
from second_brain.functions.ask import ask_question
from second_brain.health import check_health
from second_brain.inngest_client import client
from second_brain.retrieval import hybrid
from second_brain.schemas.events import PUBLICATION_ADDED, PublicationAdded
from second_brain.sources.allowlist import load_publications


async def second_brain_health() -> dict[str, object]:
    """Check whether Postgres, the Inngest Dev Server, and Memgraph are reachable.

    Returns article, passage, active claim, and topic counts alongside per-subsystem
    status (`"ok"` or `"error: <detail>"`). Call this first if any other tool call
    fails unexpectedly — it tells you which dependency is actually down.
    """
    return await check_health()


async def second_brain_add_publication(
    feed_url: typing.Annotated[
        str,
        Field(description="The publication's RSS feed URL, e.g. https://example.substack.com/feed"),
    ],
) -> dict[str, object]:
    """Add a publication by its RSS feed URL and start ingesting its articles.

    The feed's host must already be listed in this repo's `publications.yaml`
    allowlist — this tool refuses (via a fast, deterministic Inngest rejection)
    anything outside it rather than silently ingesting an unapproved source.

    Returns immediately with `{event_id, trace_url, status}`; it does not wait
    for ingestion to finish. Poll `second_brain_job_status(event_id)` with the returned
    `event_id` to see progress, and use `trace_url` to inspect the run in the
    Inngest Dev Server UI.
    """
    payload = PublicationAdded(feed_url=feed_url)
    event = inngest.Event(name=PUBLICATION_ADDED, data=payload.model_dump(mode="json"))
    event_ids = await client.send(event)
    event_id = event_ids[0]
    return {
        "event_id": event_id,
        "trace_url": f"{settings.inngest_base_url}/event/{event_id}",
        "status": "queued",
    }


async def second_brain_search(
    query: typing.Annotated[
        str, Field(description="Free-text search query, e.g. 'agentic RAG evals'")
    ],
    limit: typing.Annotated[
        int, Field(default=5, ge=1, le=25, description="Max passages to return (1-25)")
    ] = 5,
) -> dict[str, object]:
    """Three-way hybrid (BM25 + pgvector + Memgraph claim graph, RRF-fused) search.

    Combines full-text BM25 search, pgvector semantic similarity, and Memgraph
    topic-to-claim traversal using Reciprocal Rank Fusion. Returns real, attributed
    passages with title, author, URL, date, text snippet, and any matched claim metadata.
    Returns `{"results": []}` when nothing matches.
    """
    async with get_session() as session:
        results = await hybrid.search(session, query, limit)
    formatted = [
        {
            **r,
            "snippet": r["text"][:300] if len(r["text"]) > 300 else r["text"],
        }
        for r in results
    ]
    return {"results": formatted}


async def second_brain_ask(
    question: typing.Annotated[
        str, Field(description="Technical question to answer from the second brain")
    ],
) -> dict[str, object]:
    """Answer a technical question using 3-way hybrid retrieval and inline citations.

    Fast read path: performs 3-way Reciprocal Rank Fusion (BM25 lexical search +
    pgvector dense similarity + Memgraph claim graph traversal) and synthesizes an
    answer with inline citations (`[1]`, `[2]`) and an `as_of` freshness timestamp.
    Automatically surfaces cross-publication disagreements when authors conflict on a
    shared topic. Never creates an Inngest run. Records a retrieval snapshot for evaluation.
    """
    async with get_session() as session:
        return await ask_question(session, question=question)


async def second_brain_backfill(
    publication: typing.Annotated[
        str,
        Field(
            default="all",
            description=("Publication slug, feed URL, or 'all' to backfill all publications"),
        ),
    ] = "all",
) -> dict[str, object]:
    """Trigger a backfill ingestion run for one publication or all allowlisted publications.

    Discovers all available posts from the RSS feed, skipping already ingested
    articles, and queues ingestion jobs. Returns immediately with the primary
    event_id and trace_url.
    """
    pubs = load_publications()
    if publication != "all":
        matched = [p for p in pubs if p.slug == publication or p.feed_url == publication]
        if not matched:
            raise ToolError(
                f"Publication {publication!r} not found in publications.yaml allowlist."
            )
        target_pubs = matched
    else:
        target_pubs = pubs

    events = [
        inngest.Event(
            name=PUBLICATION_ADDED,
            data=PublicationAdded(feed_url=p.feed_url).model_dump(mode="json"),
        )
        for p in target_pubs
    ]
    event_ids = await client.send(events)
    first_id = event_ids[0]
    return {
        "event_id": first_id,
        "trace_url": f"{settings.inngest_base_url}/event/{first_id}",
        "expected_articles": len(target_pubs) * 20,
        "publications": [p.slug for p in target_pubs],
    }


async def second_brain_job_status(
    event_id: typing.Annotated[
        str,
        Field(
            description=(
                "The event_id returned by second_brain_add_publication or second_brain_backfill"
            )
        ),
    ],
) -> dict[str, object]:
    """Check progress of a publication ingestion or backfill job.

    Combines this repo's own `jobs` row (article counts) with the Inngest Dev
    Server's real run status and step execution details for that event.
    """
    trace_url = f"{settings.inngest_base_url}/event/{event_id}"

    run_status: str | None = None
    run_output: object = None
    steps_completed: int = 0
    response: httpx.Response | None = None
    inngest_error: httpx.HTTPError | None = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            runs_url = f"{settings.inngest_base_url}/v1/events/{event_id}/runs"
            response = await http_client.get(runs_url)
    except httpx.HTTPError as exc:
        # Deferred: the local `jobs` row can still answer without Inngest.
        inngest_error = exc

    if response is not None and response.status_code == 200:
        runs = response.json().get("data", [])
        if runs:
            run_status = runs[0]["status"]
            run_output = runs[0].get("output")
            steps = runs[0].get("steps") or {}
            steps_completed = len(steps)

    async with get_session() as session:
        job = await get_job_status(session, event_id)
        await session.commit()

    if job is None and inngest_error is not None:
        raise ToolError(
            f"Could not reach the Inngest Dev Server at {settings.inngest_base_url}: "
            f"{inngest_error}"
        ) from inngest_error

    if job is None and run_status is None:
        raise ToolError(
            f"No job or Inngest run found for event_id={event_id!r}. "
            "Check that it's the id returned by second_brain_add_publication "
            "or second_brain_backfill."
        )

    return {
        "status": job["status"] if job is not None else run_status,
        "steps_completed": steps_completed,
        "articles_ingested": job["done"] if job is not None else 0,
        "articles_done": job["done"] if job is not None else None,
        "articles_total": job["total"] if job is not None else None,
        "run_status": run_status,
        "failures": [run_output] if run_status == "Failed" else [],
        "trace_url": trace_url,
    }


async def second_brain_list_publications() -> dict[str, object]:
    """List all publications in the second brain alongside article counts and sync metadata."""
    async with get_session() as session:
        pubs = await list_publications_with_stats(session)
    return {"publications": pubs}


async def second_brain_sync(
    publication: typing.Annotated[
        str | None,
        Field(
            default=None,
            description="Optional publication slug to sync, or None to poll all feeds",
        ),
    ] = None,
) -> dict[str, object]:
    """Force an immediate freshness poll instead of waiting for the 5-minute cron.

    Dispatches `second-brain/feed.poll` to Inngest to check HTTP conditional headers
    (ETag / Last-Modified) against origins and discover new articles immediately.
    """
    event = inngest.Event(
        name="second-brain/feed.poll",
        data={"publication": publication} if publication else {},
    )
    event_ids = await client.send(event)
    event_id = event_ids[0]
    return {
        "event_id": event_id,
        "trace_url": f"{settings.inngest_base_url}/event/{event_id}",
        "status": "poll_triggered",
    }


async def second_brain_sources(
    claim_or_passage_id: typing.Annotated[
        str,
        Field(
            description=(
                "UUID of a cited claim (`claim_id`) or passage (`passage_id`) "
                "returned by second_brain_ask or second_brain_search"
            )
        ),
    ],
) -> dict[str, object]:
    """Inspect full provenance, verbatim quote, and temporal validity for a cited claim or passage.

    When to use `second_brain_sources` vs `second_brain_search`:
    - Use `second_brain_search` to discover relevant passages by free-text query.
    - Use `second_brain_sources` when you already have a specific `claim_id` or `passage_id`
      from a citation and want to verify its exact verbatim quote (`quote_span` or
      passage text), author, publication, epistemic `claim_type` (`opinion`,
      `measurement`, `prediction`), canonical topics, and temporal validity
      (`valid_from`, `valid_to`, `is_active`, `supersedes_id`).
    """
    try:
        target_uuid = uuid.UUID(claim_or_passage_id.strip())
    except ValueError as exc:
        raise ToolError(f"Invalid UUID for claim_or_passage_id={claim_or_passage_id!r}.") from exc

    async with get_session() as session:
        provenance = await get_source_provenance(session, target_uuid)

    if provenance is None:
        raise ToolError(
            f"No claim or passage found for claim_or_passage_id={claim_or_passage_id!r}."
        )
    return provenance


async def second_brain_eval_report(
    limit: typing.Annotated[
        int,
        Field(
            default=10,
            ge=1,
            le=50,
            description="Max recent evaluated snapshots to include (1-50)",
        ),
    ] = 10,
) -> dict[str, object]:
    """Return the Week 5 evaluation report: failure taxonomy counts (`FM-1`..`FM-6`),
    deterministic and binary LLM judge pass rates, recent snapshot critiques, and
    the latest multi-variant retrieval benchmark (`sparse`, `dense`, `2-way RRF`,
    `3-way RRF`).
    """
    async with get_session() as session:
        return await get_latest_eval_report(session, limit=limit)
