"""Data models for cross-project boundary contracts.

BoundaryModel: strict base for boundary types. ContractInfo: registry metadata.
ContractViolation: schema incompatibility. BoundaryResult: call outcome.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BoundaryModel(BaseModel):
    """Base class for models that cross project boundaries.

    Producer models use this directly (extra="forbid"). Consumer models call
    .permissive() for a copy with extra="ignore".
    """

    model_config = {"extra": "forbid"}

    @classmethod
    def permissive(cls) -> type[BoundaryModel]:
        """Return a permissive copy (extra='ignore') for consumer-side parsing."""
        return type(f"{cls.__name__}Permissive", (cls,),
                    {"model_config": {**cls.model_config, "extra": "ignore"}})

    @classmethod
    def schema_dict(cls) -> dict[str, Any]:
        """Return JSON schema suitable for registry storage."""
        return cls.model_json_schema()


class ProvenanceRecord(BoundaryModel):
    """Tracks where a piece of data came from."""

    source_agent: str = Field(description="Which agent produced this (claude-code, codex, openclaw)")
    source_project: str = Field(description="Which project produced this (e.g., research_v3)")
    timestamp: datetime = Field(description="When this was produced")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence (URLs, file paths)")
    confidence: float | None = Field(default=None, description="Producer's confidence, 0.0-1.0")


class ContractInfo(BaseModel):
    """Metadata about a registered boundary contract."""

    name: str = Field(description="Unique boundary name, e.g. 'onto-canon6.digimon_export'")
    version: str = Field(default="0.1.0", description="Semantic version")
    producer: str = Field(default="", description="Project that produces data", validation_alias="producer_project")
    consumers: list[str] = Field(default_factory=list, description="Projects that consume data", validation_alias="consumer_projects")
    input_schema: dict[str, Any] | None = Field(default=None, description="JSON schema of input")
    output_schema: dict[str, Any] | None = Field(default=None, description="JSON schema of output")
    description: str = Field(default="", description="Human-readable description")
    first_registered: str = Field(default="", description="ISO timestamp of first registration")
    call_count: int = Field(default=0, description="Total calls")
    error_count: int = Field(default=0, description="Failed calls")
    model_config = {"extra": "ignore", "populate_by_name": True}


class ContractViolation(BaseModel):
    """A specific incompatibility between a producer and consumer schema."""

    producer: str = Field(description="Producer boundary name")
    consumer: str = Field(description="Consumer boundary name")
    field: str = Field(description="The field with the issue")
    kind: str = Field(description="Violation kind: missing_field, type_mismatch, field_removed")
    detail: str = Field(default="", description="Human-readable explanation")
    severity: str = Field(default="breaking", description="breaking or warning")


class BoundaryResult(BaseModel):
    """Outcome of a single boundary function call, for observability."""

    boundary_name: str = Field(description="Which boundary was crossed")
    success: bool = Field(description="Whether the call succeeded")
    latency_ms: float = Field(description="Wall-clock time in milliseconds")
    error: str | None = Field(default=None, description="Error message if failed")
    timestamp: str = Field(default="", description="ISO timestamp of the call")


class ContractViolationError(Exception):
    """Raised when data at a boundary fails Pydantic validation (fail loud).

    Not to be confused with ContractViolation, which is the schema-level model.
    """

    def __init__(self, boundary_name: str, direction: str, errors: list[dict[str, Any]]) -> None:
        self.boundary_name = boundary_name
        self.direction = direction
        self.errors = errors
        first = errors[0] if errors else {"msg": "unknown"}
        super().__init__(
            f"Contract violation at {boundary_name} ({direction}): "
            f"{len(errors)} error(s). First: {first}"
        )
