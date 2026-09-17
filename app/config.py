from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Book-recommender"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://book_recommender:book_recommender@localhost:5432/book_recommender"
    )
    secret_key: str = "development-only-change-me"
    session_cookie_secure: bool = False
    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    recommendation_limit: int = Field(default=12, ge=1, le=48)
    search_limit: int = Field(default=8, ge=1, le=20)

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def split_hosts(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        unsafe_secret = (
            len(self.secret_key) < 32
            or self.secret_key == "development-only-change-me"
            or self.secret_key.startswith("replace-with-")
        )
        if self.app_env == "production" and unsafe_secret:
            raise ValueError("SECRET_KEY must be a non-placeholder value of at least 32 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
