"""@boundary decorator -- validates I/O, registers in ContractRegistry, logs to observability."""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, get_type_hints

from pydantic import BaseModel, ValidationError

from data_contracts.models import ContractViolationError
from data_contracts.registry import registry

logger = logging.getLogger(__name__)


def _get_pydantic_models(func: Callable[..., Any]) -> tuple[type[BaseModel] | None, type[BaseModel] | None]:
    """Extract input and output Pydantic model types from function signature."""
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    input_model = None
    for pname in sig.parameters:
        if pname == "self":
            continue
        hint = hints.get(pname)
        if hint and isinstance(hint, type) and issubclass(hint, BaseModel):
            input_model = hint
            break
    output_model = None
    ret = hints.get("return")
    if ret and isinstance(ret, type) and issubclass(ret, BaseModel):
        output_model = ret
    return input_model, output_model


def _try_log_observability(boundary_name: str, success: bool, latency_ms: float, error: str | None = None) -> None:
    """Log to llm_client observability if available. No-op if llm_client not installed."""
    try:
        from llm_client.observability import log_call  # type: ignore[import-not-found]
        log_call(call_type="boundary", task=boundary_name, trace_id=boundary_name,
                 success=success, latency_ms=latency_ms, cost=0.0, error=error)
    except (ImportError, Exception):
        pass


def boundary(
    name: str,
    version: str = "0.1.0",
    producer: str = "",
    consumers: list[str] | None = None,
    validate_input: bool = True,
    validate_output: bool = True,
) -> Callable[..., Any]:
    """Decorator that enforces typed contracts at project boundaries.

    Validates output against Pydantic model type, registers in ContractRegistry
    at decoration time, tracks call success/failure, and optionally logs to
    llm_client observability. Raises ContractViolationError on type mismatches.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        input_model, output_model = _get_pydantic_models(func)

        info = registry.register(
            name=name, input_type=input_model, output_type=output_model,
            version=version, producer=producer, consumers=consumers or [],
            description=func.__doc__ or "",
        )

        def _check_output(result: Any) -> None:
            if not validate_output or not output_model or isinstance(result, output_model):
                return
            try:
                output_model.model_validate(result if isinstance(result, dict) else {"__invalid__": result})
            except ValidationError as e:
                raise ContractViolationError(name, "output", e.errors()) from e

        def _finalize(start: float, success: bool, error_msg: str | None) -> None:
            registry.record_call(name, success)
            _try_log_observability(name, success, (time.monotonic() - start) * 1000, error_msg)

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                start, success, error_msg = time.monotonic(), False, None
                try:
                    result = await func(*args, **kwargs)
                    _check_output(result)
                    success = True
                    return result
                except ContractViolationError:
                    raise
                except Exception as exc:
                    error_msg = str(exc)
                    raise
                finally:
                    _finalize(start, success, error_msg)
        else:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start, success, error_msg = time.monotonic(), False, None
                try:
                    result = func(*args, **kwargs)
                    _check_output(result)
                    success = True
                    return result
                except ContractViolationError:
                    raise
                except Exception as exc:
                    error_msg = str(exc)
                    raise
                finally:
                    _finalize(start, success, error_msg)

        wrapper._boundary_info = info  # type: ignore[attr-defined]
        return wrapper

    return decorator
