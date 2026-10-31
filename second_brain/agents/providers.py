"""LLM provider layer: one `call_llm` entry point over Anthropic or OpenRouter.

`settings.llm_provider` picks the backend:
- "anthropic": the native Anthropic SDK.
- "openrouter": OpenRouter's OpenAI-compatible API, through the `openai` SDK.

Both return `{"output": ..., "usage": {...}}`, where `usage` is shaped for
`CostCaptureMiddleware` (`second_brain/inngest_client.py`). With
`persist_cost=True` the cost row is also written straight to the `costs` table,
for calls made outside an Inngest step.

Model IDs are passed through unchanged, so they must match the chosen provider:
for example `claude-sonnet-5-5` on Anthropic, or an `anthropic/...` ID on OpenRouter.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import anthropic
import openai
from pydantic import BaseModel

from second_brain.config import settings
from second_brain.db.repositories import insert_cost
from second_brain.db.session import get_session

# USD per million tokens (input, output). Models not listed fall back to the
# `anthropic_*_price_per_million_tokens` settings. OpenRouter IDs are looked up
# without their `provider/` prefix.
MODEL_PRICING_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class LLMError(RuntimeError):
    """The provider could not produce usable output (missing key, refusal, truncation)."""


@dataclass(frozen=True)
class _Completion:
    """Provider-neutral result of one LLM call."""

    text: str
    input_tokens: int
    output_tokens: int


def llm_configured() -> bool:
    """True when the API key for the configured `LLM_PROVIDER` is set."""
    if settings.llm_provider == "openrouter":
        return bool(settings.openrouter_api_key)
    return bool(settings.anthropic_api_key)


# --- Clients (created lazily, one per process) ---

_anthropic_client: anthropic.AsyncAnthropic | None = None
_openrouter_client: openai.AsyncOpenAI | None = None


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if not settings.anthropic_api_key:
        raise LLMError("LLM_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY is not set.")
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_openrouter_client() -> openai.AsyncOpenAI:
    global _openrouter_client
    if not settings.openrouter_api_key:
        raise LLMError("LLM_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set.")
    if _openrouter_client is None:
        _openrouter_client = openai.AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _openrouter_client


# --- Providers ---


async def _complete_anthropic(
    *,
    system_prompt: str,
    user_input: str,
    model: str,
    max_tokens: int,
    output_schema: type[BaseModel] | None,
) -> _Completion:
    extra: dict[str, Any] = {}
    if output_schema is not None:
        extra["output_config"] = {
            "format": {"type": "json_schema", "schema": anthropic.transform_schema(output_schema)}
        }

    response = await _get_anthropic_client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}],
        **extra,
    )

    if response.stop_reason in ("refusal", "max_tokens"):
        raise LLMError(
            f"Anthropic model {model!r} stopped with {response.stop_reason!r}; "
            "raise max_tokens if the output was truncated."
        )

    # Skip thinking blocks; the answer is in the text blocks.
    text = "".join(block.text for block in response.content if block.type == "text")
    return _Completion(text, response.usage.input_tokens, response.usage.output_tokens)


async def _complete_openrouter(
    *,
    system_prompt: str,
    user_input: str,
    model: str,
    max_tokens: int,
    output_schema: type[BaseModel] | None,
) -> _Completion:
    client = _get_openrouter_client()
    messages: list[Any] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    # `parse` sends the Pydantic model as a strict JSON schema; the model must
    # support structured outputs on OpenRouter.
    completion = await (
        client.chat.completions.parse(
            model=model, max_tokens=max_tokens, messages=messages, response_format=output_schema
        )
        if output_schema is not None
        else client.chat.completions.create(model=model, max_tokens=max_tokens, messages=messages)
    )

    choice = completion.choices[0]
    if choice.message.refusal or choice.finish_reason in ("length", "content_filter"):
        raise LLMError(
            f"OpenRouter model {model!r} returned no usable output "
            f"(finish_reason={choice.finish_reason!r}, refusal={choice.message.refusal!r})."
        )

    usage = completion.usage
    return _Completion(
        choice.message.content or "",
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
    )


_Provider = Callable[..., Awaitable[_Completion]]
_PROVIDERS: dict[str, _Provider] = {
    "anthropic": _complete_anthropic,
    "openrouter": _complete_openrouter,
}


# --- Cost ---


def estimate_llm_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost from token counts using `MODEL_PRICING_PER_MTOK`."""
    in_price, out_price = MODEL_PRICING_PER_MTOK.get(
        model.rsplit("/", 1)[-1],
        (
            settings.anthropic_input_price_per_million_tokens,
            settings.anthropic_output_price_per_million_tokens,
        ),
    )
    usd = (input_tokens * in_price + output_tokens * out_price) / 1_000_000
    return round(usd, 6)


async def record_llm_cost(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    est_usd: float,
    article_id: uuid.UUID | None = None,
) -> None:
    """Persist one LLM invocation cost row to the `costs` table."""
    async with get_session() as session:
        await insert_cost(
            session,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            est_usd=est_usd,
            article_id=article_id,
        )
        await session.commit()


# --- Entry point ---


def _strip_code_fence(text: str) -> str:
    """Remove a markdown code fence around JSON, which some OpenRouter models add."""
    stripped = text.strip()
    match = _CODE_FENCE.match(stripped)
    return match.group(1) if match else stripped


async def call_llm(
    *,
    system_prompt: str,
    user_input: str,
    model: str,
    max_tokens: int = 2048,
    output_schema: type[BaseModel] | None = None,
    article_id: uuid.UUID | None = None,
    persist_cost: bool = False,
) -> dict[str, Any]:
    """Call the configured provider and return `{"output": ..., "usage": {...}}`.

    With `output_schema`, the output is validated against it and returned as a
    JSON-compatible dict; otherwise it is the response text.
    """
    complete = _PROVIDERS[settings.llm_provider]
    result = await complete(
        system_prompt=system_prompt,
        user_input=user_input,
        model=model,
        max_tokens=max_tokens,
        output_schema=output_schema,
    )

    est_usd = estimate_llm_cost_usd(model, result.input_tokens, result.output_tokens)
    usage: dict[str, Any] = {
        "model": model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "est_usd": est_usd,
        "article_id": str(article_id) if article_id is not None else None,
    }
    if persist_cost:
        await record_llm_cost(
            model=model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            est_usd=est_usd,
            article_id=article_id,
        )

    if output_schema is None:
        return {"output": result.text, "usage": usage}

    validated = output_schema.model_validate_json(_strip_code_fence(result.text))
    return {"output": validated.model_dump(mode="json"), "usage": usage}
