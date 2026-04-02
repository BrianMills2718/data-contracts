"""Tests for ContractRegistry."""

import json

from pydantic import Field

from data_contracts import BoundaryModel, ContractRegistry


class SampleModel(BoundaryModel):
    name: str = Field(description="A name")
    value: int = Field(description="A value")


def _make_registry() -> ContractRegistry:
    """Create a test registry without loading from disk."""
    reg = ContractRegistry.__new__(ContractRegistry)
    reg._boundaries = {}
    reg._pipelines = []
    reg._persist_path = None  # type: ignore[assignment]
    return reg


class TestRegistration:
    def test_register_and_get(self):
        """Register a boundary and retrieve it by name."""
        reg = _make_registry()
        reg.register(name="test.basic", input_type=SampleModel, version="1.0.0", producer="proj")
        info = reg.get("test.basic")
        assert info is not None
        assert info.version == "1.0.0"
        assert info.producer == "proj"

    def test_register_captures_schema(self):
        """Registration should capture Pydantic model JSON schema."""
        reg = _make_registry()
        reg.register(name="test.schema", input_type=SampleModel, output_type=SampleModel)
        info = reg.get("test.schema")
        assert info is not None
        assert info.input_schema is not None
        assert "name" in info.input_schema["properties"]
        assert info.output_schema is not None

    def test_register_preserves_counts_on_update(self):
        """Re-registering should preserve call/error counts."""
        reg = _make_registry()
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
        reg = _make_registry()
        assert reg.get("does.not.exist") is None


class TestListing:
    def test_list_all(self):
        """list_all returns all registered boundaries."""
        reg = _make_registry()
        reg.register(name="a.one", producer="a")
        reg.register(name="b.two", producer="b")
        assert len(reg.list_all()) == 2

    def test_list_by_producer(self):
        """list_by_producer filters to specific producer."""
        reg = _make_registry()
        reg.register(name="a.one", producer="a")
        reg.register(name="a.two", producer="a")
        reg.register(name="b.one", producer="b")

        a_boundaries = reg.list_by_producer("a")
        assert len(a_boundaries) == 2
        assert all(b.producer == "a" for b in a_boundaries)

    def test_list_by_consumer(self):
        """list_by_consumer finds boundaries consumed by a project."""
        reg = _make_registry()
        reg.register(name="a.export", producer="a", consumers=["b", "c"])
        reg.register(name="d.export", producer="d", consumers=["b"])
        reg.register(name="e.export", producer="e", consumers=["x"])

        b_consumes = reg.list_by_consumer("b")
        assert len(b_consumes) == 2


class TestCallTracking:
    def test_record_success(self):
        """Successful call increments call_count only."""
        reg = _make_registry()
        reg.register(name="test.calls")
        reg.record_call("test.calls", success=True)
        info = reg.get("test.calls")
        assert info is not None
        assert info.call_count == 1
        assert info.error_count == 0

    def test_record_failure(self):
        """Failed call increments both call_count and error_count."""
        reg = _make_registry()
        reg.register(name="test.fails")
        reg.record_call("test.fails", success=False)
        info = reg.get("test.fails")
        assert info is not None
        assert info.call_count == 1
        assert info.error_count == 1

    def test_record_call_nonexistent_is_noop(self):
        """Recording a call for a non-registered boundary does nothing."""
        reg = _make_registry()
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

    def test_pipeline_round_trip(self, tmp_path):
        """Declared pipelines persist and reload correctly."""
        path = tmp_path / "registry.json"
        reg = ContractRegistry(persist_path=path)
        reg.declare_pipeline("my_pipeline", ["step_a", "step_b", "step_c"])

        reg2 = ContractRegistry(persist_path=path)
        pipelines = reg2.list_pipelines()
        assert len(pipelines) == 1
        assert pipelines[0].name == "my_pipeline"
        assert pipelines[0].steps == ["step_a", "step_b", "step_c"]

    def test_clear(self):
        """clear() removes all boundaries."""
        reg = _make_registry()
        reg.register(name="a.one")
        reg.register(name="b.two")
        assert len(reg.list_all()) == 2
        reg.clear()
        assert len(reg.list_all()) == 0


# --- Composability query models ---

class ProducerOut(BoundaryModel):
    """Output with name and score."""
    name: str = Field(description="Entity name")
    score: float = Field(description="Relevance score")
    tags: list[str] = Field(description="Tags", default_factory=list)


class CompatibleIn(BoundaryModel):
    """Input that only requires name and score -- compatible with ProducerOut."""
    name: str = Field(description="Entity name")
    score: float = Field(description="Relevance score")


class IncompatibleIn(BoundaryModel):
    """Input requiring a field ProducerOut doesn't provide."""
    name: str = Field(description="Entity name")
    category: str = Field(description="Required category")


class MiddleStep(BoundaryModel):
    """Model used as both input and output of a middle pipeline step."""
    name: str = Field(description="Entity name")
    score: float = Field(description="Relevance score")


class TestGetCompatibleConsumers:
    def test_returns_compatible_boundaries(self):
        """get_compatible_consumers returns boundaries whose input matches output."""
        reg = _make_registry()
        reg.register(name="source", output_type=ProducerOut)
        reg.register(name="good_sink", input_type=CompatibleIn)
        reg.register(name="bad_sink", input_type=IncompatibleIn)

        consumers = reg.get_compatible_consumers("source")
        consumer_names = [c.name for c in consumers]
        assert "good_sink" in consumer_names
        assert "bad_sink" not in consumer_names

    def test_returns_empty_for_no_output_schema(self):
        """Boundary with no output_schema has no compatible consumers."""
        reg = _make_registry()
        reg.register(name="no_output", input_type=CompatibleIn)
        reg.register(name="sink", input_type=CompatibleIn)
        assert reg.get_compatible_consumers("no_output") == []

    def test_returns_empty_for_unknown_boundary(self):
        """Unknown boundary name returns empty list."""
        reg = _make_registry()
        assert reg.get_compatible_consumers("ghost") == []

    def test_excludes_self(self):
        """A boundary should not appear as its own consumer."""
        reg = _make_registry()
        reg.register(name="self_ref", input_type=CompatibleIn, output_type=ProducerOut)
        consumers = reg.get_compatible_consumers("self_ref")
        assert all(c.name != "self_ref" for c in consumers)


class TestGetCompatibleProducers:
    def test_returns_compatible_boundaries(self):
        """get_compatible_producers returns boundaries whose output matches input."""
        reg = _make_registry()
        reg.register(name="good_source", output_type=ProducerOut)
        reg.register(name="bad_source", output_type=IncompatibleIn)
        reg.register(name="sink", input_type=CompatibleIn)

        producers = reg.get_compatible_producers("sink")
        producer_names = [p.name for p in producers]
        assert "good_source" in producer_names
        # bad_source output has 'category' but sink doesn't require it -- check actual compat
        # bad_source output: {name: str, category: str}. sink input: {name: str, score: float}.
        # bad_source is missing 'score' which sink requires -> incompatible
        assert "bad_source" not in producer_names

    def test_returns_empty_for_no_input_schema(self):
        """Boundary with no input_schema has no compatible producers."""
        reg = _make_registry()
        reg.register(name="no_input", output_type=ProducerOut)
        reg.register(name="source", output_type=ProducerOut)
        assert reg.get_compatible_producers("no_input") == []

    def test_returns_empty_for_unknown_boundary(self):
        """Unknown boundary name returns empty list."""
        reg = _make_registry()
        assert reg.get_compatible_producers("ghost") == []


class TestValidatePipeline:
    def test_valid_pipeline(self):
        """Pipeline with compatible steps returns no violations."""
        reg = _make_registry()
        reg.register(name="step1", output_type=ProducerOut)
        reg.register(name="step2", input_type=CompatibleIn, output_type=MiddleStep)
        reg.register(name="step3", input_type=MiddleStep)

        violations = reg.validate_pipeline(["step1", "step2", "step3"])
        assert violations == []

    def test_pipeline_catches_incompatibility(self):
        """Pipeline with incompatible adjacent steps returns violations."""
        reg = _make_registry()
        reg.register(name="step1", output_type=ProducerOut)
        reg.register(name="step2", input_type=IncompatibleIn, output_type=MiddleStep)

        violations = reg.validate_pipeline(["step1", "step2"])
        assert len(violations) > 0
        assert any(v.kind == "missing_field" for v in violations)

    def test_pipeline_missing_boundary(self):
        """Pipeline referencing unknown boundary returns missing_boundary violation."""
        reg = _make_registry()
        reg.register(name="step1", output_type=ProducerOut)

        violations = reg.validate_pipeline(["step1", "ghost_step"])
        assert len(violations) == 1
        assert violations[0].kind == "missing_boundary"

    def test_pipeline_missing_output_schema(self):
        """Pipeline step without output_schema returns missing_schema violation."""
        reg = _make_registry()
        reg.register(name="no_out", input_type=CompatibleIn)
        reg.register(name="step2", input_type=CompatibleIn)

        violations = reg.validate_pipeline(["no_out", "step2"])
        assert len(violations) == 1
        assert violations[0].kind == "missing_schema"

    def test_pipeline_missing_input_schema(self):
        """Pipeline step without input_schema returns missing_schema violation."""
        reg = _make_registry()
        reg.register(name="step1", output_type=ProducerOut)
        reg.register(name="no_in", output_type=MiddleStep)

        violations = reg.validate_pipeline(["step1", "no_in"])
        assert len(violations) == 1
        assert violations[0].kind == "missing_schema"

    def test_pipeline_single_step_no_violations(self):
        """Single-step pipeline has nothing to validate, returns empty."""
        reg = _make_registry()
        reg.register(name="only_step", output_type=ProducerOut)
        # validate_pipeline with < 2 steps returns empty (no pairs to check)
        violations = reg.validate_pipeline(["only_step"])
        assert violations == []


class TestDeclarePipeline:
    def test_declare_and_list(self):
        """Declared pipeline appears in list_pipelines."""
        reg = _make_registry()
        reg._persist_path = None  # disable auto-save
        # Patch save to no-op so declare_pipeline doesn't crash without a path
        reg.save = lambda: None  # type: ignore[method-assign]
        reg.declare_pipeline("my_pipeline", ["a", "b", "c"])
        pipelines = reg.list_pipelines()
        assert len(pipelines) == 1
        assert pipelines[0].name == "my_pipeline"
        assert pipelines[0].steps == ["a", "b", "c"]

    def test_declare_replaces_existing(self):
        """Re-declaring a pipeline with same name replaces it."""
        reg = _make_registry()
        reg.save = lambda: None  # type: ignore[method-assign]
        reg.declare_pipeline("pipe", ["a", "b"])
        reg.declare_pipeline("pipe", ["x", "y", "z"])
        pipelines = reg.list_pipelines()
        assert len(pipelines) == 1
        assert pipelines[0].steps == ["x", "y", "z"]

    def test_remove_pipeline(self):
        """remove_pipeline deletes by name and returns True; unknown returns False."""
        reg = _make_registry()
        reg.save = lambda: None  # type: ignore[method-assign]
        reg.declare_pipeline("pipe", ["a", "b"])
        assert reg.remove_pipeline("pipe") is True
        assert reg.list_pipelines() == []
        assert reg.remove_pipeline("pipe") is False


class TestRunChecks:
    def test_no_pipelines_returns_zero(self):
        """run_checks with no declared pipelines exits 0."""
        from data_contracts.check_schemas import run_checks
        reg = _make_registry()
        assert run_checks(registry=reg) == 0

    def test_violations_return_one(self):
        """run_checks with a declared pipeline having violations exits 1."""
        from data_contracts.check_schemas import run_checks
        reg = _make_registry()
        reg.save = lambda: None  # type: ignore[method-assign]
        reg.register(name="step1", output_type=ProducerOut)
        reg.register(name="step2", input_type=IncompatibleIn)
        reg.declare_pipeline("test_pipe", ["step1", "step2"])
        assert run_checks(registry=reg) == 1

    def test_compatible_pipeline_returns_zero(self):
        """run_checks with a compatible declared pipeline exits 0."""
        from data_contracts.check_schemas import run_checks
        reg = _make_registry()
        reg.save = lambda: None  # type: ignore[method-assign]
        reg.register(name="step1", output_type=ProducerOut)
        reg.register(name="step2", input_type=CompatibleIn)
        reg.declare_pipeline("good_pipe", ["step1", "step2"])
        assert run_checks(registry=reg) == 0
