"""Runtime configuration, read once from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

_FALSE_VALUES = {"0", "false", "no", "off"}


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    """Read a positive integer from the environment, falling back on bad input."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(int(raw), minimum)
    except ValueError:
        return default


def _float_env(name: str, default: float, minimum: float = 1.0) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(float(raw), minimum)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable application settings.

    The API key is excluded from ``repr`` so it can never leak through logs.
    """

    groq_api_key: str = field(default="", repr=False)
    groq_model: str = "llama-3.3-70b-versatile"
    use_ai: bool = True
    llm_timeout_seconds: float = 20.0
    rate_limit_per_minute: int = 20
    max_body_bytes: int = 10_000

    @property
    def ai_enabled(self) -> bool:
        """AI ideas are used only when switched on AND a key is present."""
        return self.use_ai and bool(self.groq_api_key)


def load_settings() -> Settings:
    """Build settings from environment variables (see ``.env.example``)."""
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", Settings.groq_model).strip(),
        use_ai=os.getenv("USE_AI", "true").strip().lower() not in _FALSE_VALUES,
        llm_timeout_seconds=_float_env("LLM_TIMEOUT_SECONDS", Settings.llm_timeout_seconds),
        rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", Settings.rate_limit_per_minute),
        max_body_bytes=_int_env("MAX_BODY_BYTES", Settings.max_body_bytes, minimum=1_000),
    )