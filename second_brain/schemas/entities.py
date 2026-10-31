"""Shared value types for extracted claims and their topics."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# Epistemic category of a claim. Must match the claim types named in
# `agents/prompts.py` and stored in `claims.claim_type`.
ClaimType = Literal["measurement", "opinion", "prediction"]


class ExtractedTopic(BaseModel):
    """A canonical topic: `slug` is the graph key, `name` is for display."""

    slug: str
    name: str
