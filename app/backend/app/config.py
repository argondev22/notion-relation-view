from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/notion_relation_view"

    # JWT
    JWT_SECRET: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Encryption
    ENCRYPTION_KEY: str = "your-encryption-key-change-this-in-production"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"

    # Notion API Timeouts (seconds)
    NOTION_TIMEOUT_DATABASE_LIST: float = 60.0
    NOTION_TIMEOUT_DATABASE_QUERY: float = 90.0
    NOTION_TIMEOUT_PAGE_FETCH: float = 30.0

    class Config:
        env_file = ".env"


settings = Settings()
