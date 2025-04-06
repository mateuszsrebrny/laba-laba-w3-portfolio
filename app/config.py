from functools import lru_cache

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., validation_alias="DATABASE_URL")

    model_config = ConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
