# api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: str = "5432"
    db_user: str = "postgres"
    db_pass: str = "mysecretpassword"
    db_name: str = "mccaa_website"
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    admin_password: str = "mccaa-admin-2026"
    firecrawl_api_key: str = ""
    queue_poll_interval: int = 2  # seconds


settings = Settings()
