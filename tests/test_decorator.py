"""Tests for the @boundary decorator."""

import asyncio

import pytest
from pydantic import Field

from data_contracts import BoundaryModel, ContractViolationError, boundary, registry


class InputModel(BoundaryModel):
    name: str = Field(description="The name to process")
    count: int = Field(description="How many items", default=1)


class OutputModel(BoundaryModel):
    result: str = Field(description="The processed result")
    items: list[str] = Field(description="List of items", default_factory=list)


class TestSyncBoundary:
    def test_sync_function_executes(self):
        """Decorated sync function should execute normally."""
        @boundary(name="test_dec.sync_exec", version="0.1.0", producer="test")
        def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result=data.name, items=["a"])

        result = my_fn(InputModel(name="hello"))
        assert result.result == "hello"
        assert result.items == ["a"]

    def test_sync_registers_at_decoration_time(self):
        """Boundary should be registered when decorator is evaluated, not on first call."""
        @boundary(name="test_dec.reg_at_dec", version="0.2.0", producer="proj_a")
        def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result="ok")

        info = registry.get("test_dec.reg_at_dec")
        assert info is not None
        assert info.version == "0.2.0"
        assert info.producer == "proj_a"

    def test_sync_captures_schemas(self):
        """Registry should contain input/output JSON schemas."""
        @boundary(name="test_dec.schema_cap", version="0.1.0", producer="test")
        def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result="ok")

        info = registry.get("test_dec.schema_cap")
        assert info is not None
        assert info.input_schema is not None
        assert "name" in info.input_schema.get("properties", {})
        assert info.output_schema is not None
        assert "result" in info.output_schema.get("properties", {})

    def test_sync_tracks_success(self):
        """Successful call should increment call_count."""
        @boundary(name="test_dec.track_ok", version="0.1.0", producer="test")
        def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result="ok")

        info_before = registry.get("test_dec.track_ok")
        count_before = info_before.call_count if info_before else 0

        my_fn(InputModel(name="test"))

        info_after = registry.get("test_dec.track_ok")
        assert info_after is not None
        assert info_after.call_count == count_before + 1
        assert info_after.error_count == 0

    def test_sync_tracks_failure(self):
        """Failed call should increment error_count."""
        @boundary(name="test_dec.track_fail", version="0.1.0", producer="test")
        def my_fn(data: InputModel) -> OutputModel:
            raise ValueError("intentional")

        with pytest.raises(ValueError, match="intentional"):
            my_fn(InputModel(name="test"))

        info = registry.get("test_dec.track_fail")
        assert info is not None
        assert info.error_count >= 1

    def test_sync_output_validation_bad_type(self):
        """Returning wrong type should raise ContractViolationError."""
        @boundary(name="test_dec.bad_output", version="0.1.0", producer="test")
        def my_fn(data: InputModel) -> OutputModel:
            return {"not": "a model"}  # type: ignore[return-value]

        with pytest.raises(ContractViolationError, match="output"):
            my_fn(InputModel(name="test"))

    def test_boundary_info_attached_to_wrapper(self):
        """The decorated function should have _boundary_info attribute."""
        @boundary(name="test_dec.info_attr", version="0.1.0", producer="test")
        def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result="ok")

        assert hasattr(my_fn, "_boundary_info")
        assert my_fn._boundary_info.name == "test_dec.info_attr"

    def test_consumer_projects_stored(self):
        """Consumer projects should be stored in registry."""
        @boundary(name="test_dec.consumers", version="0.1.0", producer="a", consumers=["b", "c"])
        def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result="ok")

        info = registry.get("test_dec.consumers")
        assert info is not None
        assert "b" in info.consumers
        assert "c" in info.consumers


class TestAsyncBoundary:
    def test_async_function_executes(self):
        """Decorated async function should execute normally."""
        @boundary(name="test_dec.async_exec", version="0.1.0", producer="test")
        async def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result=data.name)

        result = asyncio.run(my_fn(InputModel(name="async_hello")))
        assert result.result == "async_hello"

    def test_async_tracks_calls(self):
        """Async calls should be tracked in registry."""
        @boundary(name="test_dec.async_track", version="0.1.0", producer="test")
        async def my_fn(data: InputModel) -> OutputModel:
            return OutputModel(result="ok")

        asyncio.run(my_fn(InputModel(name="test")))
        info = registry.get("test_dec.async_track")
        assert info is not None
        assert info.call_count >= 1


class TestValidationControl:
    def test_disable_output_validation(self):
        """validate_output=False should skip output check."""
        @boundary(name="test_dec.no_validate", version="0.1.0", producer="test", validate_output=False)
        def my_fn(data: InputModel) -> OutputModel:
            return "not a model"  # type: ignore[return-value]

        result = my_fn(InputModel(name="test"))
        assert result == "not a model"

    def test_no_pydantic_params_still_works(self):
        """Functions without Pydantic params should still work."""
        @boundary(name="test_dec.plain_fn", version="0.1.0", producer="test")
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5
        info = registry.get("test_dec.plain_fn")
        assert info is not None
        assert info.input_schema is None
        assert info.output_schema is None
