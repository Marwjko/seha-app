import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FONT_PATH: str = "fonts/NotoSansArabic-Thin.ttf"
    TEXT_COLOR: str = "#3A6DB5"
    BOLD_STEPS: int = 6
    BOLD_OFFSET: float = 0.25
    SECRET: str = os.getenv("SECRET_KEY", "super-secret-key-change-me-in-production")
    DATABASE_URL: str = "site.db"

    class Config:
        env_file = ".env"

settings = Settings()
