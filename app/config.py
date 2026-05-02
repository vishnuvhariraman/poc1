from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "sanctions-screening-poc"
    screening_version: str = "v1.0.0"
    opensearch_host: str = os.getenv("OPENSEARCH_HOST", "opensearch")
    opensearch_port: int = int(os.getenv("OPENSEARCH_PORT", "9200"))
    opensearch_index: str = os.getenv("OPENSEARCH_INDEX", "sanctions-master-v1")
    postgres_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./screening.db",
    )
    hmac_secret: str = os.getenv("HMAC_SECRET", "dev-only-change-me")
    score_threshold: float = float(os.getenv("SCORE_THRESHOLD", "75"))


settings = Settings()
