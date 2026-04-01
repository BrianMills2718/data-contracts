"""Tests for data_contracts: BoundaryModel, @boundary decorator, BoundaryRegistry."""

import asyncio
import pytest
from pydantic import Field, ValidationError

from data_contracts import BoundaryModel, boundary, registry


# --- Test Models ---

class SampleInput(BoundaryModel):
    name: str = Field(description="The name to process")
    count: int = Field(description="How many items", default=1)


class SampleOutput(BoundaryModel):
    result: str = Field(description="The processed result")
    items: list[str] = Field(description="List of items", default_factory=list)


class ExtraFieldModel(BoundaryModel):
    name: str = Field(description="Name")


# --- BoundaryModel Tests ---

class TestBoundaryModel:
    def test_strict_by_default(self):
        """BoundaryModel rejects extra fields."""
        with pytest.raises(ValidationError):
            SampleInput(name="test", count=1, extra_field="bad")

    def test_valid_creation(self):
        m = SampleInput(name="test", count=5)
        assert m.name == "test"
        assert m.count == 5

    def test_default_values(self):
        m = SampleInput(name="test")
        assert m.count == 1

    def test_permissive_allows_extras(self):
        Permissive = SampleInput.permissive()
        m = Permissive(name="test", count=1, extra_field="ok")
        assert m.name == "test"

    def test_schema_dict(self):
        schema = SampleInput.schema_dict()
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "count" in schema["properties"]

    def test_schema_has_descriptions(self):
        schema = SampleInput.schema_dict()
        assert schema["properties"]["name"].get("description") == "The name to process"


# --- @boundary Decorator Tests ---

class TestBoundaryDecorator:
    def test_sync_function_registration(self):
        @boundary(name="test.sync_fn", version="0.1.0", producer="test")
        def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result=data.name, items=["a", "b"])

        info = registry.get("test.sync_fn")
        assert info is not None
        assert info.version == "0.1.0"
        assert info.producer_project == "test"

    def test_sync_function_execution(self):
        @boundary(name="test.sync_exec", version="0.1.0", producer="test")
        def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result=data.name)

        result = my_fn(SampleInput(name="hello"))
        assert isinstance(result, SampleOutput)
        assert result.result == "hello"

    def test_async_function_execution(self):
        @boundary(name="test.async_exec", version="0.1.0", producer="test")
        async def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result=data.name)

        result = asyncio.run(my_fn(SampleInput(name="async_hello")))
        assert isinstance(result, SampleOutput)
        assert result.result == "async_hello"

    def test_records_call_success(self):
        @boundary(name="test.call_track", version="0.1.0", producer="test")
        def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result="ok")

        my_fn(SampleInput(name="test"))
        info = registry.get("test.call_track")
        assert info is not None
        assert info.call_count >= 1

    def test_records_call_failure(self):
        @boundary(name="test.call_fail", version="0.1.0", producer="test")
        def my_fn(data: SampleInput) -> SampleOutput:
            raise ValueError("intentional error")

        with pytest.raises(ValueError):
            my_fn(SampleInput(name="test"))

        info = registry.get("test.call_fail")
        assert info is not None
        assert info.error_count >= 1

    def test_schema_captured_in_registry(self):
        @boundary(name="test.schema_cap", version="0.1.0", producer="test")
        def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result="ok")

        info = registry.get("test.schema_cap")
        assert info is not None
        assert info.input_schema is not None
        assert "name" in info.input_schema.get("properties", {})
        assert info.output_schema is not None
        assert "result" in info.output_schema.get("properties", {})

    def test_consumer_projects(self):
        @boundary(name="test.consumers", version="0.1.0", producer="project_a", consumers=["project_b", "project_c"])
        def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result="ok")

        info = registry.get("test.consumers")
        assert info is not None
        assert "project_b" in info.consumer_projects

    def test_boundary_info_attached(self):
        @boundary(name="test.info_attach", version="0.1.0", producer="test")
        def my_fn(data: SampleInput) -> SampleOutput:
            return SampleOutput(result="ok")

        assert hasattr(my_fn, "_boundary_info")
        assert my_fn._boundary_info.name == "test.info_attach"


# --- BoundaryRegistry Tests ---

class TestBoundaryRegistry:
    def test_list_all(self):
        all_boundaries = registry.list_all()
        assert len(all_boundaries) > 0

    def test_list_by_project(self):
        results = registry.list_by_project("test")
        assert len(results) > 0

    def test_get_nonexistent(self):
        assert registry.get("nonexistent.boundary") is None

    def test_save_and_reload(self, tmp_path):
        import sys
        mod = sys.modules["data_contracts.registry"]
        test_path = tmp_path / "test_registry.json"
        original = mod.REGISTRY_PATH
        mod.REGISTRY_PATH = test_path

        try:
            from data_contracts.registry import BoundaryInfo, BoundaryRegistry
            test_reg = BoundaryRegistry()
            test_reg._boundaries = {}
            test_reg.register(BoundaryInfo(
                name="save.test", version="1.0.0", producer_project="test_proj",
            ))
            test_reg.save()

            assert test_path.exists()
            import json
            data = json.loads(test_path.read_text())
            assert "save.test" in data["contracts"]
        finally:
            mod.REGISTRY_PATH = original


# --- ProvenanceRecord Tests ---

class TestProvenanceRecord:
    def test_creation(self):
        from data_contracts.models import ProvenanceRecord
        from datetime import datetime

        p = ProvenanceRecord(
            source_agent="claude-code",
            source_project="research_v3",
            timestamp=datetime.now(),
            evidence=["https://example.com/doc"],
            confidence=0.85,
        )
        assert p.source_agent == "claude-code"
        assert p.confidence == 0.85

    def test_schema(self):
        from data_contracts.models import ProvenanceRecord
        schema = ProvenanceRecord.schema_dict()
        assert "source_agent" in schema["properties"]
        assert "evidence" in schema["properties"]
