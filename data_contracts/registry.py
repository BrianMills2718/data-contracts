"""BoundaryRegistry — central registry of all typed boundaries.

Auto-populated when @boundary decorators are evaluated (import time).
Also supports manual registration and JSON persistence.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path.home() / "projects" / "data" / "contract_registry.json"


@dataclass
class BoundaryInfo:
    """Metadata about a registered boundary."""

    name: str
    version: str
    producer_project: str
    consumer_projects: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    description: str = ""
    first_registered: str = ""
    call_count: int = 0
    error_count: int = 0


class BoundaryRegistry:
    """Registry of all typed boundaries across the ecosystem.

    Auto-populated by @boundary decorator on import. Persists to JSON
    for dashboard consumption and cross-session continuity.
    """

    def __init__(self) -> None:
        self._boundaries: dict[str, BoundaryInfo] = {}
        self._load()

    def _load(self) -> None:
        """Load registry from disk if it exists."""
        if REGISTRY_PATH.exists():
            try:
                with open(REGISTRY_PATH) as f:
                    data = json.load(f)
                for name, info in data.get("contracts", {}).items():
                    self._boundaries[name] = BoundaryInfo(
                        name=name,
                        version=info.get("version", "0.0.0"),
                        producer_project=info.get("producer", ""),
                        consumer_projects=info.get("consumers", []),
                        input_schema=info.get("input_schema"),
                        output_schema=info.get("output_schema"),
                        description=info.get("description", ""),
                        first_registered=info.get("first_registered", ""),
                        call_count=info.get("call_count", 0),
                        error_count=info.get("error_count", 0),
                    )
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not load contract registry: %s", e)

    def save(self) -> None:
        """Persist registry to disk."""
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "contracts": {
                name: {
                    "version": info.version,
                    "producer": info.producer_project,
                    "consumers": info.consumer_projects,
                    "input_schema": info.input_schema,
                    "output_schema": info.output_schema,
                    "description": info.description,
                    "first_registered": info.first_registered,
                    "call_count": info.call_count,
                    "error_count": info.error_count,
                }
                for name, info in self._boundaries.items()
            },
            "updated_at": datetime.now().isoformat(),
        }
        with open(REGISTRY_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def register(self, info: BoundaryInfo) -> None:
        """Register a boundary. Updates existing if name matches."""
        existing = self._boundaries.get(info.name)
        if existing:
            # Preserve call counts and first_registered
            info.call_count = existing.call_count
            info.error_count = existing.error_count
            info.first_registered = existing.first_registered
        else:
            info.first_registered = datetime.now().isoformat()
        self._boundaries[info.name] = info

    def get(self, name: str) -> BoundaryInfo | None:
        """Get a boundary by name."""
        return self._boundaries.get(name)

    def list_all(self) -> list[BoundaryInfo]:
        """List all registered boundaries."""
        return list(self._boundaries.values())

    def list_by_project(self, project: str) -> list[BoundaryInfo]:
        """List boundaries for a specific producer project."""
        return [b for b in self._boundaries.values() if b.producer_project == project]

    def record_call(self, name: str, success: bool) -> None:
        """Record a boundary call for tracking."""
        info = self._boundaries.get(name)
        if info:
            info.call_count += 1
            if not success:
                info.error_count += 1

    def get_compatible_consumers(self, producer_name: str) -> list[BoundaryInfo]:
        """Find boundaries that consume what this producer outputs."""
        producer = self.get(producer_name)
        if not producer or not producer.output_schema:
            return []
        output_props = set(producer.output_schema.get("properties", {}).keys())
        compatible = []
        for b in self._boundaries.values():
            if b.name == producer_name or not b.input_schema:
                continue
            required = set(b.input_schema.get("required", []))
            if required and required.issubset(output_props):
                compatible.append(b)
        return compatible

    def check_all(self) -> list[dict]:
        """Check compatibility across declared producer→consumer pairs.

        For each boundary, checks if its output schema satisfies the input
        schema of boundaries consumed by its declared consumer projects.
        Only checks actual declared relationships, not all pairs.
        
        Returns list of violations.
        """
        violations = []
        
        # For each producer boundary, find consumer boundaries
        for producer in self._boundaries.values():
            if not producer.output_schema or not producer.consumer_projects:
                continue
            output_props = set(producer.output_schema.get("properties", {}).keys())
            
            # Find boundaries where producer_project matches one of our consumers
            for consumer_project in producer.consumer_projects:
                for consumer in self._boundaries.values():
                    if consumer.name == producer.name:
                        continue
                    if consumer.producer_project != consumer_project:
                        continue
                    if not consumer.input_schema:
                        continue
                    
                    required = set(consumer.input_schema.get("required", []))
                    if not required:
                        continue
                    
                    missing = required - output_props
                    if missing:
                        violations.append({
                            "producer": producer.name,
                            "consumer": consumer.name,
                            "missing_fields": list(missing),
                            "severity": "breaking",
                        })
        return violations


# Global singleton
registry = BoundaryRegistry()
