"""Entry point: python run.py (loads config/.env then starts uvicorn)."""
import os
from pathlib import Path

# Load config/.env without requiring python-dotenv.
env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import uvicorn
from app.settings import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, log_level="info")
