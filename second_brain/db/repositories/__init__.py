"""Every SQL statement in the project lives in this package, grouped by topic.
Functions and FastAPI endpoints call these helpers; they never build SQL themselves.
"""

from second_brain.db.repositories.articles import (
    count_articles,
    count_articles_for_publication,
    count_articles_for_publication_since,
    get_article_by_canonical_id,
    get_article_with_publication,
    get_existing_canonical_ids,
    upsert_article,
)
from second_brain.db.repositories.claims import (
    count_active_claims,
    find_matching_passage_for_quote,
    get_active_claims_for_article,
    get_source_provenance,
    persist_article_claims,
)
from second_brain.db.repositories.evals import (
    get_latest_eval_report,
    upsert_eval_result,
    upsert_eval_run,
)
from second_brain.db.repositories.jobs import (
    create_job,
    get_job,
    get_job_status,
    insert_cost,
    list_recent_failures,
    record_failure,
)
from second_brain.db.repositories.passages import (
    count_passages,
    insert_passages_fresh,
    replace_passages,
    search_passages_bm25,
    search_passages_dense,
    supersede_passages,
)
from second_brain.db.repositories.publications import (
    get_cursor,
    get_publication_by_slug,
    list_publications,
    list_publications_with_stats,
    update_cursor,
    upsert_publication,
)
from second_brain.db.repositories.snapshots import (
    get_snapshot,
    save_snapshot,
)

__all__ = [
    "count_active_claims",
    "count_articles",
    "count_articles_for_publication",
    "count_articles_for_publication_since",
    "count_passages",
    "create_job",
    "find_matching_passage_for_quote",
    "get_active_claims_for_article",
    "get_article_by_canonical_id",
    "get_article_with_publication",
    "get_cursor",
    "get_existing_canonical_ids",
    "get_job",
    "get_job_status",
    "get_latest_eval_report",
    "get_publication_by_slug",
    "get_snapshot",
    "get_source_provenance",
    "insert_cost",
    "insert_passages_fresh",
    "list_publications",
    "list_publications_with_stats",
    "list_recent_failures",
    "persist_article_claims",
    "record_failure",
    "replace_passages",
    "save_snapshot",
    "search_passages_bm25",
    "search_passages_dense",
    "supersede_passages",
    "update_cursor",
    "upsert_article",
    "upsert_eval_result",
    "upsert_eval_run",
    "upsert_publication",
]
