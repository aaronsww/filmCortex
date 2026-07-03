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

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 384


settings = Settings()
