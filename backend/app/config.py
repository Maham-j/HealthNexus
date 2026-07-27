"""
Loads settings from .env.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # LLM
    llm_provider: str = "gemini"
    gemini_api_key: str = ""

    # Auth / JWT
    jwt_secret_key: str = "change_this_in_env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    demo_username: str = "admin"
    demo_password_hash: str = ""  # generated with hash_password(), stored here — never plain text

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
