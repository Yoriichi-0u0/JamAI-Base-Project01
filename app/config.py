"""Application configuration for Realfun AI Admin Copilot."""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    """Configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="",
        populate_by_name=True,
    )

    jamai_project_id: str = Field(..., validation_alias=AliasChoices("jamai_project_id", "JAMAI_PROJECT_ID"))
    jamai_pat: str = Field(..., validation_alias=AliasChoices("jamai_pat", "JAMAI_PAT"))
    jamai_action_table_id: str = Field(
        ..., validation_alias=AliasChoices("jamai_action_table_id", "JAMAI_ACTION_TABLE_ID")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Loading and validation happen only once to keep Streamlit hot-reload fast.
    """

    return Settings()  # type: ignore[arg-type]


__all__: list[str] = ["Settings", "get_settings"]
