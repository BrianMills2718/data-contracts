"""Tests for ContractRegistry."""

import json

import pytest
from pydantic import BaseModel, Field

from data_contracts import BoundaryModel, ContractRegistry
from data_contracts.models import ContractInfo


class SampleModel(BoundaryModel):
    name: str = Field(description="A name")
    value: int = Field(description="A value")


class TestRegistration:
    def test_register_and_get(self):
        """Register a boundary and retrieve it by name."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="test.basic", input_type=SampleModel, version="1.0.0", producer="proj")
        info = reg.get("test.basic")
        assert info is not None
        assert info.version == "1.0.0"
        assert info.producer == "proj"

    def test_register_captures_schema(self):
        """Registration should capture Pydantic model JSON schema."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="test.schema", input_type=SampleModel, output_type=SampleModel)
        info = reg.get("test.schema")
        assert info is not None
        assert info.input_schema is not None
        assert "name" in info.input_schema["properties"]
        assert info.output_schema is not None

    def test_register_preserves_counts_on_update(self):
        """Re-registering should preserve call/error counts."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="test.update", version="1.0.0")
        reg.record_call("test.update", success=True)
        reg.record_call("test.update", success=False)

        reg.register(name="test.update", version="2.0.0")
        info = reg.get("test.update")
        assert info is not None
        assert info.version == "2.0.0"
        assert info.call_count == 2
        assert info.error_count == 1

    def test_get_nonexistent_returns_none(self):
        """Getting a non-registered boundary returns None."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]
        assert reg.get("does.not.exist") is None


class TestListing:
    def test_list_all(self):
        """list_all returns all registered boundaries."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="a.one", producer="a")
        reg.register(name="b.two", producer="b")
        assert len(reg.list_all()) == 2

    def test_list_by_producer(self):
        """list_by_producer filters to specific producer."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="a.one", producer="a")
        reg.register(name="a.two", producer="a")
        reg.register(name="b.one", producer="b")

        a_boundaries = reg.list_by_producer("a")
        assert len(a_boundaries) == 2
        assert all(b.producer == "a" for b in a_boundaries)

    def test_list_by_consumer(self):
        """list_by_consumer finds boundaries consumed by a project."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="a.export", producer="a", consumers=["b", "c"])
        reg.register(name="d.export", producer="d", consumers=["b"])
        reg.register(name="e.export", producer="e", consumers=["x"])

        b_consumes = reg.list_by_consumer("b")
        assert len(b_consumes) == 2


class TestCallTracking:
    def test_record_success(self):
        """Successful call increments call_count only."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="test.calls")
        reg.record_call("test.calls", success=True)
        info = reg.get("test.calls")
        assert info is not None
        assert info.call_count == 1
        assert info.error_count == 0

    def test_record_failure(self):
        """Failed call increments both call_count and error_count."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="test.fails")
        reg.record_call("test.fails", success=False)
        info = reg.get("test.fails")
        assert info is not None
        assert info.call_count == 1
        assert info.error_count == 1

    def test_record_call_nonexistent_is_noop(self):
        """Recording a call for a non-registered boundary does nothing."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.record_call("ghost.boundary", success=True)  # should not raise


class TestPersistence:
    def test_save_and_reload(self, tmp_path):
        """Registry should round-trip through JSON."""
        path = tmp_path / "registry.json"
        reg = ContractRegistry(persist_path=path)
        reg.register(name="persist.test", version="1.0.0", producer="proj", consumers=["other"])
        reg.record_call("persist.test", success=True)
        reg.save()

        assert path.exists()
        data = json.loads(path.read_text())
        assert "persist.test" in data["contracts"]

        # Reload
        reg2 = ContractRegistry(persist_path=path)
        info = reg2.get("persist.test")
        assert info is not None
        assert info.version == "1.0.0"
        assert info.call_count == 1

    def test_clear(self):
        """clear() removes all boundaries."""
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._boundaries = {}
        reg._persist_path = None  # type: ignore[assignment]

        reg.register(name="a.one")
        reg.register(name="b.two")
        assert len(reg.list_all()) == 2
        reg.clear()
        assert len(reg.list_all()) == 0
