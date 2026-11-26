from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Type, Tuple, Any, Optional
import time
import random

@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_seconds: float = 0.4
    max_seconds: float = 3.0
    retry_on: Tuple[Type[BaseException], ...] = (TimeoutError, ConnectionError)

def exponential_backoff(attempt: int, base: float, cap: float) -> float:
    # attempt starts at 1
    delay = base * (2 ** (attempt - 1))
    # small jitter
    delay = delay * (0.75 + random.random() * 0.5)
    return min(delay, cap)

def with_retries(fn: Callable[..., Any], policy: RetryPolicy, on_retry: Optional[Callable[[int, BaseException], None]] = None):
    def _wrapped(*args, **kwargs):
        last_err = None
        for attempt in range(1, policy.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except policy.retry_on as e:
                last_err = e
                if on_retry:
                    on_retry(attempt, e)
                if attempt == policy.max_retries:
                    raise
                time.sleep(exponential_backoff(attempt, policy.base_seconds, policy.max_seconds))
        raise last_err  # defensive
    return _wrapped
