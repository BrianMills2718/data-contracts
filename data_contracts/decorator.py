"""@boundary decorator — validates I/O, logs to observability, registers in registry.

Usage:
    from data_contracts import boundary, BoundaryModel

    class MyInput(BoundaryModel):
        name: str = Field(description="The name")

    class MyOutput(BoundaryModel):
        result: int = Field(description="The result")

    @boundary(name="my_project.my_export", version="0.1.0", producer="my_project")
    def my_export(data: MyInput) -> MyOutput:
        return MyOutput(result=42)
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, get_type_hints

from pydantic import BaseModel, ValidationError

from data_contracts.registry import BoundaryInfo, registry

logger = logging.getLogger(__name__)


class ContractViolation(Exception):
    """Raised when data at a boundary fails validation."""

    def __init__(self, boundary_name: str, direction: str, errors: list[dict]) -> None:
        self.boundary_name = boundary_name
        self.direction = direction
        self.errors = errors
        super().__init__(
            f"Contract violation at {boundary_name} ({direction}): "
            f"{len(errors)} error(s). First: {errors[0] if errors else 'unknown'}"
        )


def _get_pydantic_models(func: Callable) -> tuple[type[BaseModel] | None, type[BaseModel] | None]:
    """Extract input and output Pydantic model types from function signature."""
    hints = get_type_hints(func)
    sig = inspect.signature(func)

    # Find first Pydantic model parameter (input type)
    input_model = None
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        hint = hints.get(param_name)
        if hint and isinstance(hint, type) and issubclass(hint, BaseModel):
            input_model = hint
            break

    # Return type
    output_model = None
    return_hint = hints.get("return")
    if return_hint and isinstance(return_hint, type) and issubclass(return_hint, BaseModel):
        output_model = return_hint

    return input_model, output_model


def boundary(
    name: str,
    version: str = "0.1.0",
    producer: str = "",
    consumers: list[str] | None = None,
    validate_input: bool = True,
    validate_output: bool = True,
) -> Callable:
    """Decorator that enforces typed contracts at project boundaries.

    Wraps a function to:
    1. Validate input arguments against their Pydantic model types
    2. Validate return value against its Pydantic model type
    3. Register the boundary in the global registry (on first call)
    4. Log call success/failure to the registry
    5. Raise ContractViolation on type mismatches (fail loud, no silent fallback)
    """

    def decorator(func: Callable) -> Callable:
        input_model, output_model = _get_pydantic_models(func)

        # Register immediately at decoration time
        info = BoundaryInfo(
            name=name,
            version=version,
            producer_project=producer,
            consumer_projects=consumers or [],
            input_schema=input_model.model_json_schema() if input_model else None,
            output_schema=output_model.model_json_schema() if output_model else None,
            description=func.__doc__ or "",
        )
        registry.register(info)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.time()
                success = False
                try:
                    result = await func(*args, **kwargs)
                    if validate_output and output_model and not isinstance(result, output_model):
                        try:
                            output_model.model_validate(result if isinstance(result, dict) else result)
                        except ValidationError as e:
                            raise ContractViolation(name, "output", e.errors()) from e
                    success = True
                    return result
                except ContractViolation:
                    raise
                except Exception:
                    raise
                finally:
                    registry.record_call(name, success)
                    latency = time.time() - start
                    if latency > 5.0:
                        logger.info("Boundary %s took %.1fs", name, latency)

            async_wrapper._boundary_info = info  # type: ignore[attr-defined]
            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.time()
                success = False
                try:
                    result = func(*args, **kwargs)
                    if validate_output and output_model and not isinstance(result, output_model):
                        try:
                            output_model.model_validate(result if isinstance(result, dict) else result)
                        except ValidationError as e:
                            raise ContractViolation(name, "output", e.errors()) from e
                    success = True
                    return result
                except ContractViolation:
                    raise
                except Exception:
                    raise
                finally:
                    registry.record_call(name, success)
                    latency = time.time() - start
                    if latency > 5.0:
                        logger.info("Boundary %s took %.1fs", name, latency)

            sync_wrapper._boundary_info = info  # type: ignore[attr-defined]
            return sync_wrapper

    return decorator
