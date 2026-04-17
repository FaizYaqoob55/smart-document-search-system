import os
from pathlib import Path


def _load_dotenv(dotenv_path: Path):
    if not dotenv_path.exists():
        return
    with dotenv_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_root = Path(__file__).resolve().parents[1]
_load_dotenv(_root / ".env")


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))


settings = Settings()
