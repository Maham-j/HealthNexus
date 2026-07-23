"""
App configuration — loads values from .env.
TODO: fill in settings as needed.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"


settings = Settings()
