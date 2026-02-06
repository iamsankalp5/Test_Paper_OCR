"""
Global application settings using Pydantic BaseSettings.
Loads configuration from environment variables.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Agentic AI Test Papers", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # MongoDB
    mongodb_url: str = Field(..., env="MONGODB_URL")
    mongodb_db_name: str = Field(default="agentic_ai_db", env="MONGODB_DB_NAME")
    
    # # OpenAI
    # openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    # openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")

    # Google Gemini
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")

    # NEW: Authentication settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",  # Change this!
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, env="JWT_EXPIRATION_MINUTES")  # 24 hours
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    # Storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: str = Field(default="jpg,jpeg,png,pdf", env="ALLOWED_EXTENSIONS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # Tesseract
    tesseract_cmd: str = Field(default="/usr/bin/tesseract", env="TESSERACT_CMD")
    
    # SMTP
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: str = Field(default="", env="SMTP_USER")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert comma-separated extensions to list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for getting settings instance."""
    return settings