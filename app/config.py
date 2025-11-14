"""Application Configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/video_pipeline"

    # Microservices
    prompt_parser_url: str = "http://localhost:8001"
    image_gen_url: str = "http://localhost:8002"
    video_gen_url: str = "http://localhost:8003"
    composition_url: str = "http://localhost:8004"

    # Configuration
    max_cost_per_video: float = 10.00
    api_timeout_seconds: int = 120
    max_concurrent_jobs: int = 10
    max_parallel_video_generations: int = 4

    # Logging
    log_level: str = "INFO"

    # Service Info
    service_name: str = "ai-video-orchestrator"
    version: str = "1.0.0"


# Global settings instance
settings = Settings()
