"""SQLAlchemy models.

Only one function writes each table ("one writer per table"
rule): `add-publication` / `backfill-publication` write `publications` and
`jobs`, `ingest-article` writes `articles`/`passages`, the cost-capture
middleware writes `costs`, and `POST /ask` writes `snapshots`. Every pipeline
write is an upsert (snapshots are append-only); see `second_brain/db/repositories/`.

Importing this package imports every model, so `Base.metadata` is complete
for Alembic autogenerate and relationship() strings resolve.
"""

from second_brain.db.models.articles import Article
from second_brain.db.models.base import Base
from second_brain.db.models.claims import Claim
from second_brain.db.models.evals import EvalResult, EvalRun
from second_brain.db.models.jobs import Cost, Failure, Job
from second_brain.db.models.passages import Passage
from second_brain.db.models.publications import Cursor, Publication
from second_brain.db.models.snapshots import Snapshot

__all__ = [
    "Article",
    "Base",
    "Claim",
    "Cost",
    "Cursor",
    "EvalResult",
    "EvalRun",
    "Failure",
    "Job",
    "Passage",
    "Publication",
    "Snapshot",
]
