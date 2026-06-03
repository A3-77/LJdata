from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://dashboard:dashboard@127.0.0.1:5432/dashboard")
    database_connect_timeout: int = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "3"))
    database_preflight_timeout: float = float(os.getenv("DATABASE_PREFLIGHT_TIMEOUT", "1.0"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("API_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )
    upload_dir: Path = Path(os.getenv("DASHBOARD_UPLOAD_DIR", str(REPO_ROOT / "data" / "uploads")))
    import_python: str = os.getenv("DASHBOARD_IMPORT_PYTHON", sys.executable)
    import_service_src: Path = Path(
        os.getenv("DASHBOARD_IMPORT_SERVICE_SRC", str(REPO_ROOT / "import-service" / "src"))
    )
    default_region_code: str = os.getenv("DASHBOARD_DEFAULT_REGION_CODE", "LN")
    default_region_name: str = os.getenv("DASHBOARD_DEFAULT_REGION_NAME", "辽宁区域")
    default_template_code: str = os.getenv("DASHBOARD_DEFAULT_TEMPLATE_CODE", "franchise_contribution_v1")
    import_api_token: str | None = os.getenv("DASHBOARD_IMPORT_API_TOKEN") or None


settings = Settings()
