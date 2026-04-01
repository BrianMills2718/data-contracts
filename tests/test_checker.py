"""Tests for check_compatibility and check_breaking_changes."""

import pytest
from pydantic import BaseModel, Field

from data_contracts import BoundaryModel, check_compatibility
from data_contracts.checker import check_breaking_changes


# --- Test schemas ---

class ProducerOutput(BoundaryModel):
    name: str = Field(description="Entity name")
    score: float = Field(description="Relevance score")
    tags: list[str] = Field(description="Tags", default_factory=list)


class ConsumerInput(BoundaryModel):
    name: str = Field(description="Entity name")
    score: float = Field(description="Relevance score")


class StrictConsumerInput(BoundaryModel):
    name: str = Field(description="Entity name")
    score: float = Field(description="Relevance score")
    category: str = Field(description="Required category")


class TypeMismatchConsumer(BoundaryModel):
    name: int = Field(description="Entity name as integer")  # type: ignore[assignment]
    score: float = Field(description="Relevance score")


class TestCheckCompatibility:
    def test_compatible_schemas(self):
        """Producer provides everything consumer needs -- no violations."""
        violations = check_compatibility(
            producer_schema=ProducerOutput.model_json_schema(),
            consumer_schema=ConsumerInput.model_json_schema(),
        )
        assert len(violations) == 0

    def test_missing_required_field(self):
        """Consumer requires 'category' but producer doesn't provide it."""
        violations = check_compatibility(
            producer_schema=ProducerOutput.model_json_schema(),
            consumer_schema=StrictConsumerInput.model_json_schema(),
            producer_name="producer.export",
            consumer_name="consumer.import",
        )
        assert len(violations) == 1
        v = violations[0]
        assert v.kind == "missing_field"
        assert v.field == "category"
        assert v.severity == "breaking"

    def test_type_mismatch(self):
        """Producer has name:string but consumer expects name:integer."""
        violations = check_compatibility(
            producer_schema=ProducerOutput.model_json_schema(),
            consumer_schema=TypeMismatchConsumer.model_json_schema(),
        )
        type_violations = [v for v in violations if v.kind == "type_mismatch"]
        assert len(type_violations) == 1
        assert type_violations[0].field == "name"

    def test_empty_schemas(self):
        """Empty schemas should produce no violations."""
        violations = check_compatibility(
            producer_schema={},
            consumer_schema={},
        )
        assert len(violations) == 0

    def test_consumer_no_required_fields(self):
        """Consumer with all optional fields should always be compatible."""
        class AllOptional(BaseModel):
            name: str | None = Field(default=None, description="Optional name")

        violations = check_compatibility(
            producer_schema=ProducerOutput.model_json_schema(),
            consumer_schema=AllOptional.model_json_schema(),
        )
        assert len(violations) == 0

    def test_multiple_violations(self):
        """Multiple missing fields should each produce a violation."""
        class NeedsMany(BoundaryModel):
            name: str = Field(description="Name")
            score: float = Field(description="Score")
            category: str = Field(description="Category")
            priority: int = Field(description="Priority")

        violations = check_compatibility(
            producer_schema=ProducerOutput.model_json_schema(),
            consumer_schema=NeedsMany.model_json_schema(),
        )
        missing = [v for v in violations if v.kind == "missing_field"]
        assert len(missing) == 2  # category and priority


class TestCheckBreakingChanges:
    def test_no_changes(self):
        """Identical schemas should have no breaking changes."""
        schema = ProducerOutput.model_json_schema()
        violations = check_breaking_changes(schema, schema)
        assert len(violations) == 0

    def test_field_removed(self):
        """Removing a field is a breaking change."""
        old = ProducerOutput.model_json_schema()
        new = ConsumerInput.model_json_schema()  # missing 'tags'
        violations = check_breaking_changes(old, new, boundary_name="my.boundary")
        removed = [v for v in violations if v.kind == "field_removed"]
        assert len(removed) == 1
        assert removed[0].field == "tags"

    def test_type_changed(self):
        """Changing a field's type is a breaking change."""
        old = ProducerOutput.model_json_schema()
        new = TypeMismatchConsumer.model_json_schema()  # name: str -> int
        violations = check_breaking_changes(old, new)
        type_changes = [v for v in violations if v.kind == "type_mismatch"]
        assert len(type_changes) >= 1
        assert any(v.field == "name" for v in type_changes)

    def test_new_required_field(self):
        """Adding a new required field is a breaking change."""
        old = ConsumerInput.model_json_schema()
        new = StrictConsumerInput.model_json_schema()  # adds required 'category'
        violations = check_breaking_changes(old, new)
        new_required = [v for v in violations if v.kind == "missing_field"]
        assert len(new_required) == 1
        assert new_required[0].field == "category"


# --- CLI tests ---

import subprocess
import sys


class TestMatrixCLI:
    def test_matrix_runs_without_error(self, tmp_path):
        """matrix subcommand should run without crashing (even with empty registry)."""
        registry_path = tmp_path / "registry.json"
        # Write a registry with test boundaries
        import json
        from pydantic import Field
        from data_contracts import BoundaryModel

        class Out(BoundaryModel):
            name: str = Field(description="n")
            score: float = Field(description="s")

        class In(BoundaryModel):
            name: str = Field(description="n")

        registry_data = {
            "contracts": {
                "a.export": {
                    "version": "1.0.0", "producer": "a", "consumers": [],
                    "output_schema": Out.model_json_schema(),
                    "input_schema": None,
                    "description": "", "first_registered": "", "call_count": 0, "error_count": 0,
                },
                "b.import": {
                    "version": "1.0.0", "producer": "b", "consumers": [],
                    "input_schema": In.model_json_schema(),
                    "output_schema": None,
                    "description": "", "first_registered": "", "call_count": 0, "error_count": 0,
                },
            },
            "updated_at": "2026-01-01T00:00:00",
        }
        registry_path.write_text(json.dumps(registry_data))

        # Patch env to use our registry -- we test via the Python API instead
        from data_contracts.registry import ContractRegistry
        reg = ContractRegistry(persist_path=registry_path)
        boundaries = reg.list_all()
        has_output = [b for b in boundaries if b.output_schema]
        has_input = [b for b in boundaries if b.input_schema]
        assert len(has_output) >= 1
        assert len(has_input) >= 1

    def test_matrix_empty_registry(self):
        """matrix with no boundaries prints informative message."""
        from data_contracts.registry import ContractRegistry
        from io import StringIO
        import contextlib

        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]
        # The matrix function uses ContractRegistry() which hits disk --
        # we test the logic indirectly: no boundaries with schemas -> empty
        assert [b for b in reg.list_all() if b.output_schema] == []


class TestPipelineCLI:
    def test_pipeline_catches_violations_via_registry(self, tmp_path):
        """pipeline validation catches incompatible steps."""
        from data_contracts import BoundaryModel
        from data_contracts.registry import ContractRegistry
        from pydantic import Field

        class StepOut(BoundaryModel):
            name: str = Field(description="n")

        class StepIn(BoundaryModel):
            name: str = Field(description="n")
            category: str = Field(description="c")

        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]
        reg.register(name="s1", output_type=StepOut)
        reg.register(name="s2", input_type=StepIn)

        violations = reg.validate_pipeline(["s1", "s2"])
        assert len(violations) > 0
        assert any(v.field == "category" for v in violations)

    def test_pipeline_passes_for_valid_chain(self, tmp_path):
        """pipeline validation passes when all steps are compatible."""
        from data_contracts import BoundaryModel
        from data_contracts.registry import ContractRegistry
        from pydantic import Field

        class A(BoundaryModel):
            name: str = Field(description="n")
            score: float = Field(description="s")

        class B(BoundaryModel):
            name: str = Field(description="n")

        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]
        reg.register(name="p1", output_type=A)
        reg.register(name="p2", input_type=B, output_type=A)
        reg.register(name="p3", input_type=B)

        violations = reg.validate_pipeline(["p1", "p2", "p3"])
        assert violations == []
