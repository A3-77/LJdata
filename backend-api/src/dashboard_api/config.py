from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://dashboard:dashboard@localhost:5432/dashboard")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("API_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )


settings = Settings()

