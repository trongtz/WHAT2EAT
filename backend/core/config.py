from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 ngày
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_INTENT_PARSER: bool = False
    OPENAI_TIMEOUT_SECONDS: float = 8.0
    AUTO_CREATE_TABLES: bool = False
    AUTO_SEED: bool = False

    class Config:
        env_file = ".env" # Tự động load từ file .env

# Tạo một instance duy nhất để dùng chung cho toàn dự án
settings = Settings()
