import os
from functools import lru_cache

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., validation_alias="DATABASE_URL")

    git_commit: str = Field(
        "unknown", validation_alias="RENDER_GIT_COMMIT"
    )  # fallback handled below

    model_config = ConfigDict(env_file=".env")

    # fallback to GIT_COMMIT if RENDER_GIT_COMMIT is not set
    def __init__(self, **data):
        super().__init__(**data)
        if self.git_commit == "unknown":
            self.git_commit = os.getenv("GIT_COMMIT", "unknown")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_git_commit() -> str:
    return get_settings().git_commit
