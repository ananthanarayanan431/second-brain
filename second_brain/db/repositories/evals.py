"""Eval results, suite runs, and the latest eval report."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from second_brain.db.models import (
    EvalResult,
    EvalRun,
    Snapshot,
)


async def upsert_eval_result(
    session: AsyncSession,
    *,
    snapshot_id: str,
    deterministic_passed: bool,
    checks: dict[str, bool],
    faithfulness_verdict: str,
    faithfulness_critique: str,
    disagreement_verdict: str,
    disagreement_critique: str,
    failure_codes: list[str],
    composite_score: float,
) -> uuid.UUID:
    """Upsert an `EvalResult` row for `snapshot_id` and update `snapshots.confidence`."""
    stmt = (
        insert(EvalResult)
        .values(
            id=uuid.uuid4(),
            snapshot_id=snapshot_id,
            deterministic_passed=deterministic_passed,
            checks=checks,
            faithfulness_verdict=faithfulness_verdict,
            faithfulness_critique=faithfulness_critique,
            disagreement_verdict=disagreement_verdict,
            disagreement_critique=disagreement_critique,
            failure_codes=failure_codes,
            composite_score=composite_score,
        )
        .on_conflict_do_update(
            index_elements=[EvalResult.snapshot_id],
            set_={
                "deterministic_passed": deterministic_passed,
                "checks": checks,
                "faithfulness_verdict": faithfulness_verdict,
                "faithfulness_critique": faithfulness_critique,
                "disagreement_verdict": disagreement_verdict,
                "disagreement_critique": disagreement_critique,
                "failure_codes": failure_codes,
                "composite_score": composite_score,
            },
        )
        .returning(EvalResult.id)
    )
    eval_id = (await session.execute(stmt)).scalar_one()

    await session.execute(
        update(Snapshot)
        .where(Snapshot.snapshot_id == snapshot_id)
        .values(confidence=composite_score)
    )
    return eval_id


async def upsert_eval_run(
    session: AsyncSession,
    *,
    run_id: str,
    suite_name: str,
    variants_summary: dict[str, object],
    case_results: list[dict[str, object]],
) -> str:
    """Upsert a benchmark or failure-replay suite execution in `eval_runs`."""
    stmt = (
        insert(EvalRun)
        .values(
            run_id=run_id,
            suite_name=suite_name,
            variants_summary=variants_summary,
            case_results=case_results,
        )
        .on_conflict_do_update(
            index_elements=[EvalRun.run_id],
            set_={
                "suite_name": suite_name,
                "variants_summary": variants_summary,
                "case_results": case_results,
            },
        )
        .returning(EvalRun.run_id)
    )
    return (await session.execute(stmt)).scalar_one()


async def get_latest_eval_report(session: AsyncSession, limit: int = 10) -> dict[str, object]:
    """Assemble the fast-read evaluation report for `GET /evals/latest` and
    `second_brain_eval_report`.
    """
    latest_run = (
        await session.execute(select(EvalRun).order_by(EvalRun.created_at.desc()).limit(1))
    ).scalar_one_or_none()

    eval_rows = list(
        (
            await session.execute(
                select(EvalResult).order_by(EvalResult.created_at.desc()).limit(limit)
            )
        ).scalars()
    )

    total_evaluated = (
        await session.execute(select(func.count()).select_from(EvalResult))
    ).scalar_one()

    taxonomy_counts: dict[str, int] = {}
    det_passes = 0
    faith_passes = 0
    recent_evaluations: list[dict[str, object]] = []

    for row in eval_rows:
        if row.deterministic_passed:
            det_passes += 1
        if row.faithfulness_verdict == "PASS":
            faith_passes += 1
        for code in row.failure_codes or []:
            taxonomy_counts[str(code)] = taxonomy_counts.get(str(code), 0) + 1
        recent_evaluations.append(
            {
                "snapshot_id": row.snapshot_id,
                "composite_score": float(row.composite_score),
                "deterministic_passed": row.deterministic_passed,
                "faithfulness_verdict": row.faithfulness_verdict,
                "faithfulness_critique": row.faithfulness_critique,
                "disagreement_verdict": row.disagreement_verdict,
                "failure_codes": list(row.failure_codes or []),
                "created_at": row.created_at.isoformat(),
            }
        )

    denom = max(len(eval_rows), 1)
    return {
        "total_evaluated_snapshots": total_evaluated,
        "recent_deterministic_pass_rate": round(det_passes / denom, 4) if eval_rows else None,
        "recent_faithfulness_pass_rate": round(faith_passes / denom, 4) if eval_rows else None,
        "failure_taxonomy_counts": taxonomy_counts,
        "recent_evaluations": recent_evaluations,
        "latest_suite_run": (
            {
                "run_id": latest_run.run_id,
                "suite_name": latest_run.suite_name,
                "variants_summary": latest_run.variants_summary,
                "created_at": latest_run.created_at.isoformat(),
            }
            if latest_run is not None
            else None
        ),
    }
