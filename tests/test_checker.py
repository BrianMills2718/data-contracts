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
