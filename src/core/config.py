from pydantic_settings import BaseSettings

class Settings(BaseSettings) :

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    GEMINI_API_KEY: str

    IMAGE_KIT_PRIVATE: str
    IMAGE_KIT_PUBLIC: str
    IMAGE_KIT_URL: str

    REDIS_URL: str

    OTP_TTL_SECONDS: int
    OTP_COOLDOWN_SECONDS: int
    OTP_MAX_ATTEMPTS: int
    PENDING_REG_TTL_SECONDS: int

    BREVO_API_KEY: str
    SENDER_EMAIL: str
    SENDER_NAME: str

    class Config:
        env_file = "src/.env"


settings = Settings()