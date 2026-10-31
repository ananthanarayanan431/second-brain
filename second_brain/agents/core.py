"""Hand-written agent execution layer built directly on Inngest step primitives.

No agent frameworks (LangChain, LangGraph, CrewAI) are used. Every LLM call is
wrapped in `step.run(step_id, ...)` so outputs are durably memoized by Inngest
and validated with Pydantic v2.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import overload
from uuid import UUID

import inngest
from pydantic import BaseModel

from second_brain.agents.providers import call_llm


@dataclass(frozen=True, kw_only=True)
class AgentBase:
    """Fields shared by every agent role."""

    name: str
    role: str
    system_prompt: str
    model: str
    max_tokens: int = 2048


@dataclass(frozen=True, kw_only=True)
class TextAgent(AgentBase):
    """Agent whose output is free text."""


@dataclass(frozen=True, kw_only=True)
class StructuredAgent[T: BaseModel](AgentBase):
    """Agent whose output is validated into the Pydantic model `output_schema`."""

    output_schema: type[T]


@overload
async def run_agent[T: BaseModel](
    step: inngest.Step,
    agent: StructuredAgent[T],
    user_input: str,
    step_id: str,
    article_id: UUID | None = None,
) -> T: ...


@overload
async def run_agent(
    step: inngest.Step,
    agent: TextAgent,
    user_input: str,
    step_id: str,
    article_id: UUID | None = None,
) -> str: ...


async def run_agent[T: BaseModel](
    step: inngest.Step,
    agent: StructuredAgent[T] | TextAgent,
    user_input: str,
    step_id: str,
    article_id: UUID | None = None,
) -> T | str:
    """Execute one LLM call for `agent` inside `step.run(step_id, ...)` so its
    output is durably memoized by Inngest and its token cost is captured by
    `CostCaptureMiddleware`.

    A `StructuredAgent[T]` returns a validated `T`; a `TextAgent` returns `str`.
    """
    schema = agent.output_schema if isinstance(agent, StructuredAgent) else None

    async def _call() -> object:
        return await call_llm(
            system_prompt=agent.system_prompt,
            user_input=user_input,
            model=agent.model,
            max_tokens=agent.max_tokens,
            output_schema=schema,
            article_id=article_id,
        )

    step_result: object = await step.run(step_id, _call)

    if isinstance(step_result, dict) and "output" in step_result:
        raw_output: object = step_result["output"]
    else:
        raw_output = step_result

    if schema is None:
        return str(raw_output)
    if isinstance(raw_output, schema):
        return raw_output
    if isinstance(raw_output, str):
        return schema.model_validate_json(raw_output)
    return schema.model_validate(raw_output)


async def bounded_loop[T: BaseModel](
    step: inngest.Step,
    agent: StructuredAgent[T] | TextAgent,
    initial_input: str,
    *,
    step_prefix: str,
    should_stop: Callable[[T | str, int], Awaitable[bool] | bool],
    next_input: Callable[[T | str, int], Awaitable[str] | str],
    max_iterations: int = 3,
    max_usd: float = 0.50,
    article_id: UUID | None = None,
) -> list[T | str]:
    """Execute a bounded multi-step agent loop with hard iteration and USD cost caps."""
    outputs: list[T | str] = []
    current_input = initial_input
    accumulated_usd = 0.0

    for iteration in range(1, max_iterations + 1):
        if accumulated_usd >= max_usd:
            break

        step_id = f"{step_prefix}-{iteration}"
        result = await run_agent(
            step=step,
            agent=agent,
            user_input=current_input,
            step_id=step_id,
            article_id=article_id,
        )
        outputs.append(result)

        stop_decision = should_stop(result, iteration)
        if isinstance(stop_decision, Awaitable):
            stop_decision = await stop_decision
        if stop_decision or iteration >= max_iterations:
            break

        next_prompt = next_input(result, iteration)
        if isinstance(next_prompt, Awaitable):
            next_prompt = await next_prompt
        current_input = next_prompt

    return outputs