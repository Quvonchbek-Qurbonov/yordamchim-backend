from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #Mode
    DEBUG: bool = False

    # Application Settings
    APP_NAME: str = "Challenges Controller"
    APP_VERSION: str = "1.0.0"

    # Machines settings
    LAB_TIMEOUT_SECONDS: int = 600

    #Database
    DATABASE_URL: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    #JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = "app/.env"


settings = Settings()