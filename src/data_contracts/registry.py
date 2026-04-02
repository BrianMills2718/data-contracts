"""ContractRegistry -- singleton tracking all registered boundaries.

Auto-populated by @boundary decorator at import time. Persists to JSON.
Supports composability queries: find compatible producers/consumers and
validate multi-step pipelines.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from data_contracts.models import ContractInfo, ContractViolation

# Backwards-compatible alias: prompt_eval uses BoundaryInfo
BoundaryInfo = ContractInfo

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path.home() / "projects" / "data" / "contract_registry.json"


class ContractRegistry:
    """Central registry of all typed boundaries across the ecosystem."""

    def __init__(self, persist_path: Path | None = None) -> None:
        self._boundaries: dict[str, ContractInfo] = {}
        self._persist_path = persist_path or REGISTRY_PATH
        self._load()

    def _load(self) -> None:
        """Load registry from disk if it exists."""
        if not self._persist_path.exists():
            return
        try:
            with open(self._persist_path) as f:
                data = json.load(f)
            for name, d in data.get("contracts", {}).items():
                self._boundaries[name] = ContractInfo(
                    name=name, version=d.get("version", "0.0.0"),
                    producer=d.get("producer", ""), consumers=d.get("consumers", []),
                    input_schema=d.get("input_schema"), output_schema=d.get("output_schema"),
                    description=d.get("description", ""),
                    first_registered=d.get("first_registered", ""),
                    call_count=d.get("call_count", 0), error_count=d.get("error_count", 0),
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load contract registry: %s", e)

    def save(self) -> None:
        """Persist registry to disk."""
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "contracts": {n: i.model_dump(exclude={"name"}) for n, i in self._boundaries.items()},
            "updated_at": datetime.now().isoformat(),
        }
        with open(self._persist_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(
        self, name: str | ContractInfo, input_type: type | None = None,
        output_type: type | None = None, version: str = "0.1.0",
        producer: str = "", consumers: list[str] | None = None,
        description: str = "",
    ) -> ContractInfo:
        """Register a boundary. Updates existing entry, preserving call counts.

        Accepts either keyword args OR a pre-built ContractInfo as the first arg
        (for backward compat with prompt_eval's BoundaryInfo registration pattern).
        """
        if isinstance(name, ContractInfo):
            info = name
            existing = self._boundaries.get(info.name)
            if existing:
                info.first_registered = existing.first_registered
                info.call_count = existing.call_count
                info.error_count = existing.error_count
            self._boundaries[info.name] = info
            return info

        from pydantic import BaseModel
        input_schema = input_type.model_json_schema() if input_type and isinstance(input_type, type) and issubclass(input_type, BaseModel) else None
        output_schema = output_type.model_json_schema() if output_type and isinstance(output_type, type) and issubclass(output_type, BaseModel) else None
        existing = self._boundaries.get(name)
        info = ContractInfo(
            name=name, version=version, producer=producer, consumers=consumers or [],
            input_schema=input_schema, output_schema=output_schema, description=description,
            first_registered=existing.first_registered if existing else datetime.now().isoformat(),
            call_count=existing.call_count if existing else 0,
            error_count=existing.error_count if existing else 0,
        )
        self._boundaries[name] = info
        return info

    def get(self, name: str) -> ContractInfo | None:
        """Get a boundary by name."""
        return self._boundaries.get(name)

    def list_all(self) -> list[ContractInfo]:
        """List all registered boundaries."""
        return list(self._boundaries.values())

    def list_by_project(self, project: str) -> list[ContractInfo]:
        """Alias for list_by_producer (backward compat)."""
        return self.list_by_producer(project)

    def list_by_producer(self, producer: str) -> list[ContractInfo]:
        """List boundaries for a specific producer project."""
        return [b for b in self._boundaries.values() if b.producer == producer]

    def list_by_consumer(self, consumer: str) -> list[ContractInfo]:
        """List boundaries that a given project consumes from."""
        return [b for b in self._boundaries.values() if consumer in b.consumers]

    def get_compatible_consumers(self, boundary_name: str) -> list[ContractInfo]:
        """Find boundaries whose input_schema is compatible with this boundary's output.

        Given a boundary name, returns all other boundaries that could consume
        this boundary's output without schema violations.
        """
        from data_contracts.checker import check_compatibility

        source = self._boundaries.get(boundary_name)
        if not source or not source.output_schema:
            return []

        compatible: list[ContractInfo] = []
        for name, info in self._boundaries.items():
            if name == boundary_name or not info.input_schema:
                continue
            violations = check_compatibility(
                source.output_schema, info.input_schema,
                producer_name=boundary_name, consumer_name=name,
            )
            if not violations:
                compatible.append(info)
        return compatible

    def get_compatible_producers(self, boundary_name: str) -> list[ContractInfo]:
        """Find boundaries whose output_schema is compatible with this boundary's input.

        Given a boundary name, returns all other boundaries whose output could
        feed this boundary's input without schema violations.
        """
        from data_contracts.checker import check_compatibility

        target = self._boundaries.get(boundary_name)
        if not target or not target.input_schema:
            return []

        compatible: list[ContractInfo] = []
        for name, info in self._boundaries.items():
            if name == boundary_name or not info.output_schema:
                continue
            violations = check_compatibility(
                info.output_schema, target.input_schema,
                producer_name=name, consumer_name=boundary_name,
            )
            if not violations:
                compatible.append(info)
        return compatible

    def validate_pipeline(self, steps: list[str]) -> list[ContractViolation]:
        """Validate that an ordered list of boundaries forms a compatible pipeline.

        Checks that each step's output_schema is compatible with the next step's
        input_schema. Returns all violations found across the chain.
        """
        from data_contracts.checker import check_compatibility

        violations: list[ContractViolation] = []
        for i in range(len(steps) - 1):
            producer_name = steps[i]
            consumer_name = steps[i + 1]
            producer = self._boundaries.get(producer_name)
            consumer = self._boundaries.get(consumer_name)

            if not producer:
                violations.append(ContractViolation(
                    producer=producer_name, consumer=consumer_name,
                    field="(boundary)", kind="missing_boundary",
                    detail=f"Boundary '{producer_name}' not found in registry",
                ))
                continue
            if not consumer:
                violations.append(ContractViolation(
                    producer=producer_name, consumer=consumer_name,
                    field="(boundary)", kind="missing_boundary",
                    detail=f"Boundary '{consumer_name}' not found in registry",
                ))
                continue
            if not producer.output_schema:
                violations.append(ContractViolation(
                    producer=producer_name, consumer=consumer_name,
                    field="(schema)", kind="missing_schema",
                    detail=f"Boundary '{producer_name}' has no output_schema",
                ))
                continue
            if not consumer.input_schema:
                violations.append(ContractViolation(
                    producer=producer_name, consumer=consumer_name,
                    field="(schema)", kind="missing_schema",
                    detail=f"Boundary '{consumer_name}' has no input_schema",
                ))
                continue

            step_violations = check_compatibility(
                producer.output_schema, consumer.input_schema,
                producer_name=producer_name, consumer_name=consumer_name,
            )
            violations.extend(step_violations)

        return violations

    def record_call(self, name: str, success: bool) -> None:
        """Record a boundary call for tracking."""
        info = self._boundaries.get(name)
        if info:
            info.call_count += 1
            if not success:
                info.error_count += 1

    def clear(self) -> None:
        """Remove all registered boundaries (for testing)."""
        self._boundaries.clear()


# Global singleton
registry = ContractRegistry()
