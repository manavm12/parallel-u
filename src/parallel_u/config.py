"""Configuration for Parallel U MVP."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    mino_api_key: str = ""
    mino_base_url: str = "https://mino.ai"
    debug: bool = False

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
