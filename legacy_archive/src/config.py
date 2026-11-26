from dataclasses import dataclass
import os

@dataclass
class Config:
    # Retry policy (tweak in session)
    MAX_RETRIES: int = 3
    BACKOFF_BASE_SECONDS: float = 0.4
    BACKOFF_MAX_SECONDS: float = 3.0

    # Planner behavior
    MAX_REVISIONS: int = 2
    CRITIQUE_PASS_SCORE: int = 7  # 0-10

    # Demo knob: simulate random transient failures in tools
    SIMULATE_TRANSIENT_FAILURES: bool = True
    TRANSIENT_FAILURE_RATE: float = 0.25


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def load_config() -> Config:
    """Load config with optional env overrides.

    This makes workshops easier (no code edits required) and keeps tests deterministic.
    """
    cfg = Config()
    cfg.SIMULATE_TRANSIENT_FAILURES = _env_bool("SIMULATE_TRANSIENT_FAILURES", cfg.SIMULATE_TRANSIENT_FAILURES)
    cfg.TRANSIENT_FAILURE_RATE = _env_float("TRANSIENT_FAILURE_RATE", cfg.TRANSIENT_FAILURE_RATE)
    return cfg

CONFIG = load_config()
