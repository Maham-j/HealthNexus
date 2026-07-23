"""
Central place for all app configuration.
Reads from .env — never hardcode secrets here.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # LLM
    llm_provider: str = "gemini"  # gemini | openai | groq
    gemini_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
