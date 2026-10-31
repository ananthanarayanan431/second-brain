"""Topic and author canonicalization: equivalent spellings must map to one graph node."""

from __future__ import annotations

import pytest

from second_brain.graph.ontology import normalize_author, normalize_topic, normalize_topics


@pytest.mark.parametrize(
    ("raw", "slug"),
    [
        # Plurals collapse onto the singular slug.
        ("databases", "database"),
        ("vector databases", "vector-database"),
        ("responses", "response"),
        ("processes", "process"),
        ("indexes", "index"),
        ("patches", "patch"),
        ("sizes", "size"),
        ("batch sizes", "batch-size"),
        ("caches", "cache"),
        ("embeddings", "embedding"),
        ("AI agents", "ai-agent"),
        ("repos", "repo"),
        ("APIs", "api"),
        # Singular-looking words are left alone.
        ("Kubernetes", "kubernetes"),
        ("metrics", "metrics"),
        ("pandas", "pandas"),
        ("status", "status"),
        # Aliases win over the generic rules.
        ("Retrieval-Augmented Generation", "rag"),
        ("LLMs", "llm"),
        ("re-ranking", "reranker"),
    ],
)
def test_normalize_topic_slug(raw: str, slug: str) -> None:
    topic = normalize_topic(raw)
    assert topic is not None
    assert topic.slug == slug


def test_singular_and_plural_share_a_slug() -> None:
    singular = normalize_topic("database")
    plural = normalize_topic("Databases")
    assert singular is not None and plural is not None
    assert singular.slug == plural.slug


@pytest.mark.parametrize("raw", ["", "   ", "AI", "models", "system", "!!"])
def test_generic_or_empty_topics_are_rejected(raw: str) -> None:
    assert normalize_topic(raw) is None


def test_normalize_topics_dedupes_in_order() -> None:
    topics = normalize_topics(["RAG", "databases", "retrieval augmented generation", "database"])
    assert [t.slug for t in topics] == ["rag", "database"]


def test_display_name_uppercases_acronyms() -> None:
    topic = normalize_topic("llm routing")
    assert topic is not None
    assert topic.name == "LLM Routing"


def test_normalize_author() -> None:
    assert normalize_author("  Paul   Iusztin ").slug == "paul-iusztin"
    assert normalize_author(None).slug == "unknown-author"
    assert normalize_author("   ").slug == "unknown-author"
