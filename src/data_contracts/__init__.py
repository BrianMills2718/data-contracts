"""Typed data contracts for cross-project boundaries.

Enforces Pydantic models at every function that crosses a project boundary.
Provides @boundary decorator for validation, registration, and observability.
"""

from data_contracts.checker import check_compatibility
from data_contracts.decorator import boundary
from data_contracts.models import (
    BoundaryModel,
    BoundaryResult,
    ContractInfo,
    ContractViolation,
    ContractViolationError,
    ProvenanceRecord,
)
from data_contracts.registry import ContractRegistry, registry

__all__ = [
    "BoundaryModel",
    "BoundaryResult",
    "ContractInfo",
    "ContractRegistry",
    "ContractViolation",
    "ContractViolationError",
    "ProvenanceRecord",
    "boundary",
    "check_compatibility",
    "registry",
]
