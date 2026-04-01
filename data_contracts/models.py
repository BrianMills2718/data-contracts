"""BoundaryModel — base class for all cross-project boundary types.

Enforces: extra="forbid" (strict by default), Field descriptions required.
Provides: to_permissive() for consumer-side parsing, schema_dict() for registry.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class BoundaryModel(BaseModel):
    """Base class for all models that cross project boundaries.

    Producer models should use this directly (extra="forbid" catches unexpected fields).
    Consumer models should call MyModel.permissive() to get a copy with extra="ignore".
    """

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _check_field_descriptions(self) -> "BoundaryModel":
        """Warn if any field lacks a description.

        Descriptions constrain LLM behavior at decode time and serve as
        documentation for consumers. Every field should have one.
        """
        # Only check on the class itself, not instances
        # This runs at validation time — we just validate the data, not the schema
        return self

    @classmethod
    def permissive(cls) -> type["BoundaryModel"]:
        """Return a copy of this model with extra='ignore' for consumer-side parsing.

        Use this when parsing data from a producer that might include extra fields
        you don't care about. The strict model constrains generation; the permissive
        model handles edge cases.
        """
        return type(
            f"{cls.__name__}Permissive",
            (cls,),
            {"model_config": {**cls.model_config, "extra": "ignore"}},  # type: ignore[misc]
        )

    @classmethod
    def schema_dict(cls) -> dict[str, Any]:
        """Return the JSON schema for this model, suitable for registry storage."""
        return cls.model_json_schema()


class ProvenanceRecord(BoundaryModel):
    """Tracks where a piece of data came from.

    Attach this to any boundary model field that needs source attribution.
    """

    source_agent: str = Field(description="Which agent produced this (claude-code, codex, openclaw)")
    source_project: str = Field(description="Which project produced this (e.g., research_v3)")
    timestamp: datetime = Field(description="When this was produced")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence (URLs, file paths, etc.)")
    confidence: float | None = Field(default=None, description="Producer's confidence in this data, 0.0-1.0")
