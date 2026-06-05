from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    embedding_model: str = "models/text-embedding-004"

    # Telegram
    telegram_bot_token: str
    recruiter_chat_id: str

    # LangSmith
    langchain_tracing_v2: str = "true"
    langchain_api_key: str = ""
    langchain_project: str = "talentfilter-ai"

    # Paths
    chroma_persist_dir: str = "./data/chroma"
    database_url: str = "./data/talentfilter.db"

    # Lógica de negocio
    score_threshold: int = Field(default=85, ge=1, le=100)
    max_completeness_retries: int = Field(default=2, ge=1)


# Instancia global — importar desde cualquier módulo
settings = Settings()