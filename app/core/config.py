from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "root"
    DB_PASSWORD: str = "password1234"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_health"
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CONNECT_TIMEOUT_SECONDS: float = 1.0
    REDIS_SOCKET_TIMEOUT_SECONDS: float = 5.0
    AI_ANALYSIS_TIMEOUT_SECONDS: float = 3.0

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
