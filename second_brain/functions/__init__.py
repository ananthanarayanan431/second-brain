"""Inngest functions served by `second_brain/main.py`.

`add_publication` (`discovery.py`) is intentionally not registered: from week 2
on, `backfill_publication` handles the same `second-brain/publication.added` event.
"""

from __future__ import annotations

from typing import Any

import inngest

from second_brain.functions.backfill import backfill_publication
from second_brain.functions.enrich import extract_claims
from second_brain.functions.evals import evaluate_answer, run_eval_suite
from second_brain.functions.freshness import poll_feeds
from second_brain.functions.ingest import ingest_article
from second_brain.functions.ops import handle_function_failed

FUNCTIONS: list[inngest.Function[Any]] = [
    backfill_publication,
    ingest_article,
    poll_feeds,
    extract_claims,
    evaluate_answer,
    run_eval_suite,
    handle_function_failed,
]
