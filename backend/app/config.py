"""
SPECTRA Component D — Configuration via environment variables.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration is loaded from environment variables / .env file."""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Component B (ORACLE brain)
    component_b_url: str = "http://localhost:8001"

    # CORS — comma-separated origins
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Feature flags
    mock_mode: bool = False
    demo_mode: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Session TTL in seconds (1 hour default)
    session_ttl: int = 3600

    # Game
    game_duration: int = 300  # overridden to 90 when demo_mode is True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def effective_game_duration(self) -> int:
        return 90 if self.demo_mode else self.game_duration


settings = Settings()
