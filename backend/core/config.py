from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    TARGET_DATABASE_URL: Optional[str] = None
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 ngày
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MODE_CLASSIFIER: bool = False
    OPENAI_INTENT_PARSER: bool = False
    OPENAI_AGENT_PLANNER: bool = False
    OPENAI_AGENTIC_RERANKER: bool = False
    OPENAI_RERANK_SHORTLIST_SIZE: int = 12
    OPENAI_TIMEOUT_SECONDS: float = 8.0
    AUTO_CREATE_TABLES: bool = False
    AUTO_SEED: bool = False

    class Config:
        env_file = ".env" # Tự động load từ file .env

# Tạo một instance duy nhất để dùng chung cho toàn dự án
settings = Settings()
