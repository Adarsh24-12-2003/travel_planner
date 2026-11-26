from __future__ import annotations
from typing import Callable, Any, Optional
from pydantic import BaseModel, ValidationError
import traceback

class GuardError(RuntimeError):
    pass

def safe_call(
    step_name: str,
    fn: Callable[[], Any],
    *,
    expect_model: Optional[type[BaseModel]] = None,
) -> Any:
    """Run a function with guardrails.
    - Converts exceptions into GuardError with useful context
    - Optionally validates the return value against a Pydantic model
    """
    try:
        out = fn()
        if expect_model is not None:
            if isinstance(out, expect_model):
                return out
            return expect_model.model_validate(out)
        return out
    except ValidationError as ve:
        raise GuardError(f"[{step_name}] output validation failed: {ve}") from ve
    except Exception as e:
        tb = traceback.format_exc(limit=4)
        raise GuardError(f"[{step_name}] failed: {e}\n{tb}") from e
