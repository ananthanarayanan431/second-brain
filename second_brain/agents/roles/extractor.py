"""Claim extractor agent role configured with the locked Week 4 ontology schema."""

from __future__ import annotations

import re

from second_brain.agents.core import StructuredAgent
from second_brain.agents.prompts import CLAIM_EXTRACTOR_SYSTEM_PROMPT
from second_brain.config import settings
from second_brain.graph.ontology import TOPIC_ALIASES, normalize_topics
from second_brain.schemas.entities import ClaimExtractionBatch, ClaimType, RawExtractedClaim

claim_extractor_agent: StructuredAgent[ClaimExtractionBatch] = StructuredAgent(
    name="claim-extractor",
    role="Structured Claim & Quote-Span Extractor",
    system_prompt=CLAIM_EXTRACTOR_SYSTEM_PROMPT,
    model=settings.extraction_model,
    output_schema=ClaimExtractionBatch,
    max_tokens=settings.extraction_max_tokens,
)

# A number with a unit ("40%", "120 ms", "3x", "2.5 seconds") marks a measurement.
# `%` is not a word character, so it cannot be followed by `\b` like the word units.
_MEASUREMENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|(?:ms|x|seconds|bytes|tokens|usd)\b)")
_PREDICTION_RE = re.compile(r"\b(?:will|future|predict|next decade|eventually)\b")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_MIN_SENTENCE_CHARS = 25


def format_extractor_prompt(
    *,
    title: str,
    author: str | None,
    publication_name: str,
    article_text: str,
) -> str:
    """Format the article metadata and body for `claim_extractor_agent`.

    The body is wrapped in `<article>` tags so it stays clearly separated from
    the instructions; the system prompt treats it as untrusted data.
    """
    return (
        f"Publication: {publication_name}\n"
        f"Article Title: {title}\n"
        f"Author: {author or 'Unknown Author'}\n\n"
        f"<article>\n{article_text}\n</article>"
    )


def heuristic_extract_claims(
    article_text: str,
    *,
    max_claims: int = 5,
) -> ClaimExtractionBatch:
    """Deterministic fallback extractor used only when no LLM API key is configured.

    Splits the article into sentences, finds sentences mentioning known domain
    entities, and uses the exact sentence from `article_text` as `quote_span`
    so the downstream quote-span guardrail still validates real substrings.
    """
    sentences = [
        s.strip()
        for s in _SENTENCE_SPLIT_RE.split(article_text)
        if len(s.strip()) >= _MIN_SENTENCE_CHARS
    ]
    extracted: list[RawExtractedClaim] = []

    for sentence in sentences:
        lower = sentence.lower()
        matched_entities = [
            canonical_name
            for alias_key, (_slug, canonical_name) in TOPIC_ALIASES.items()
            if re.search(rf"\b{re.escape(alias_key)}\b", lower)
        ]

        topics = normalize_topics(matched_entities)
        if not topics:
            continue

        claim_type: ClaimType = "opinion"
        if _MEASUREMENT_RE.search(lower):
            claim_type = "measurement"
        elif _PREDICTION_RE.search(lower):
            claim_type = "prediction"

        extracted.append(
            RawExtractedClaim(
                claim_text=sentence,
                quote_span=sentence,
                claim_type=claim_type,
                entities=[t.name for t in topics[:5]],
                confidence=0.85,
            )
        )
        if len(extracted) >= max_claims:
            break

    return ClaimExtractionBatch(claims=extracted)
