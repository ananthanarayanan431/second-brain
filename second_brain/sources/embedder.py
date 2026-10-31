"""OpenAI embeddings, batched into as few provider calls as possible.

Calls OpenAI directly when OPENAI_API_KEY is set; otherwise falls back to the
same model through OpenRouter's OpenAI-compatible embeddings endpoint using
OPENROUTER_API_KEY (OpenRouter namespaces the model ID as `openai/...`).

Returns a JSON-serializable dict carrying a top-level `"usage"` key — the
convention `CostCaptureMiddleware` (`second_brain/inngest_client.py`) recognizes to
record cost into the `costs` table, without every embedding/LLM call site
having to write to the database itself.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from second_brain.config import settings

_client: AsyncOpenAI | None = None


def _uses_openrouter() -> bool:
    return not settings.openai_api_key and bool(settings.openrouter_api_key)


def _provider_model() -> str:
    """Model ID to send to the provider; OpenRouter wants the `openai/` prefix."""
    model = settings.embedding_model
    if _uses_openrouter() and "/" not in model:
        return f"openai/{model}"
    return model


def _get_client() -> AsyncOpenAI:
    # Created on first use, not at import time, so modules that import this one
    # (and the tests) load fine without an API key.
    global _client
    if _client is None:
        if _uses_openrouter():
            _client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
            )
        else:
            _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_texts(texts: list[str]) -> dict:
    if not texts:
        return {
            "embeddings": [],
            "usage": {
                "model": settings.embedding_model,
                "input_tokens": 0,
                "output_tokens": 0,
                "est_usd": 0.0,
            },
        }

    embeddings: list[list[float]] = []
    total_tokens = 0
    for start in range(0, len(texts), settings.embedding_batch_size):
        batch = texts[start : start + settings.embedding_batch_size]
        response = await _get_client().embeddings.create(
            input=batch,
            model=_provider_model(),
            dimensions=settings.embedding_dimensions,
        )
        # The API does not guarantee response order matches input order.
        ordered = sorted(response.data, key=lambda item: item.index)
        embeddings.extend(item.embedding for item in ordered)
        total_tokens += response.usage.total_tokens

    est_usd = (total_tokens / 1_000_000) * settings.embedding_price_per_million_tokens
    return {
        "embeddings": embeddings,
        "usage": {
            "model": settings.embedding_model,
            "input_tokens": total_tokens,
            "output_tokens": 0,
            "est_usd": round(est_usd, 6),
        },
    }
