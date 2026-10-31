"""Domain and extraction schemas for Week 4 claim extraction and graph ontology.

Strict Pydantic v2 models sit at the boundary between the LLM extractor, the
deterministic quote-span guardrail, and the Postgres/Memgraph writers.
"""

from __future__ import annotations

from typing import Literal, get_args

from pydantic import BaseModel, Field

# Epistemic category of a claim. Must match the claim types named in
# `agents/prompts.py` and stored in `claims.claim_type`.
ClaimType = Literal["opinion", "measurement", "prediction"]
VALID_CLAIM_TYPES: frozenset[str] = frozenset(get_args(ClaimType))


class ExtractedTopic(BaseModel):
    """A canonical topic: `slug` is the graph key, `name` is for display."""

    slug: str = Field(description="Normalized lowercase hyphenated topic slug")
    name: str = Field(description="Canonical human-readable topic or entity name")


class RawExtractedClaim(BaseModel):
    claim_text: str = Field(
        min_length=5,
        description="Concise, self-contained assertion attributed to the author",
    )
    quote_span: str = Field(
        description="Exact verbatim substring from the article supporting the claim"
    )
    claim_type: ClaimType
    entities: list[str] = Field(
        min_length=1,
        max_length=5,
        description="1 to 5 key technical entities/topics",
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)


class ClaimExtractionBatch(BaseModel):
    claims: list[RawExtractedClaim] = Field(default_factory=list)


class ValidatedClaim(BaseModel):
    """A claim that has passed the verbatim quote_span guardrail and topic canonicalization."""

    claim_id: str
    article_id: str
    text: str
    quote_span: str
    claim_type: ClaimType
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)
    topics: list[ExtractedTopic] = Field(min_length=1)
