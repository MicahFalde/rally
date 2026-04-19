from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://rally:rally_dev@localhost:5432/rally"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    geocodio_api_key: str = ""

    # Voter file storage
    voter_file_upload_dir: str = "/tmp/rally_uploads"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
