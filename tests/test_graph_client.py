"""Schema initialization must tolerate "already exists" but retry real failures."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest
from neo4j import AsyncDriver

from second_brain.graph import client


class _Result:
    async def consume(self) -> None:
        return None


class _Session:
    def __init__(self, errors: dict[str, Exception], ran: list[str]) -> None:
        self._errors = errors
        self._ran = ran

    async def __aenter__(self) -> _Session:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def run(self, query: str, parameters: Any = None) -> _Result:
        self._ran.append(query)
        if query in self._errors:
            raise self._errors[query]
        return _Result()


class _Driver:
    def __init__(self, errors: dict[str, Exception] | None = None) -> None:
        self.errors = errors or {}
        self.ran: list[str] = []

    def session(self) -> _Session:
        return _Session(self.errors, self.ran)


@pytest.fixture(autouse=True)
def _reset_driver() -> Iterator[None]:
    yield
    client.set_graph_driver(None)


def _install(driver: _Driver) -> None:
    client.set_graph_driver(cast(AsyncDriver, driver))


async def test_schema_initialized_once_when_all_statements_succeed() -> None:
    driver = _Driver()
    _install(driver)

    await client.ensure_graph_schema()
    await client.ensure_graph_schema()

    assert len(driver.ran) == len(client.SCHEMA_DDL_STATEMENTS)


async def test_already_exists_errors_count_as_success() -> None:
    stmt = client.SCHEMA_DDL_STATEMENTS[-1]
    driver = _Driver({stmt: RuntimeError("Constraint already exists.")})
    _install(driver)

    await client.ensure_graph_schema()
    await client.ensure_graph_schema()

    assert len(driver.ran) == len(client.SCHEMA_DDL_STATEMENTS)


async def test_real_failure_is_retried_on_next_call(caplog: pytest.LogCaptureFixture) -> None:
    stmt = client.SCHEMA_DDL_STATEMENTS[0]
    driver = _Driver({stmt: RuntimeError("connection reset")})
    _install(driver)

    await client.ensure_graph_schema()
    assert "connection reset" in caplog.text

    driver.errors.clear()
    await client.ensure_graph_schema()
    await client.ensure_graph_schema()

    # First call ran every statement, second retried them all, third was a no-op.
    assert len(driver.ran) == 2 * len(client.SCHEMA_DDL_STATEMENTS)
