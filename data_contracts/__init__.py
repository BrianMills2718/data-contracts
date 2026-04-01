"""Typed data contracts for cross-project boundaries.

Enforces Pydantic models at every function that crosses a project boundary.
Provides @boundary decorator for validation, registration, and observability.
"""

from data_contracts.models import BoundaryModel
from data_contracts.decorator import boundary
from data_contracts.registry import BoundaryInfo, BoundaryRegistry, registry

__all__ = [
    "BoundaryModel",
    "boundary",
    "BoundaryInfo",
    "BoundaryRegistry",
    "registry",
]
