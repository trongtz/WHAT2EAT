from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 ngày

    class Config:
        env_file = ".env" # Tự động load từ file .env

# Tạo một instance duy nhất để dùng chung cho toàn dự án
settings = Settings()