from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FilmCortex"
    app_env: str = "development"
    app_debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = (
        "postgresql+asyncpg://filmcortex:filmcortex@localhost:5433/filmcortex"
    )

    tmdb_api_key: str = ""
    tmdb_requests_per_second: float = 30.0
    tmdb_export_cache_dir: str = ".cache/tmdb_exports"
    tmdb_top_rated_cursor_path: str = ".cache/tmdb_pipeline/top_rated_next_page"

    tmdb_initial_load_limit: int = 500
    tmdb_daily_export_limit: int = 100
    tmdb_trending_limit: int = 40
    tmdb_top_rated_limit: int = 100
    tmdb_discover_limit: int = 100

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_batch_size: int = 100
    embedding_dimensions: int = 384


settings = Settings()
