from pydantic import SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.schemas.types import AppEnv


class EmailSettings(BaseSettings):
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: SecretStr

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


class RedisSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")

    @property
    def redis_url(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class Settings(BaseSettings):
    APP_ENV: AppEnv
    APP_HOST: str

    DB_HOST: str
    DB_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    REDIS_HOST: str
    REDIS_PORT: int

    DB_AVAILABLE: bool = True
    REDIS_AVAILABLE: bool = True

    @property
    def REDIS_URL(self):  # redis://username:password@host:port/db
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def REDIS_URL_FOR_TASKS(self):  # redis://username:password@host:port/db
        """redis db=2 для celery"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"

    @property
    def DB_URL_ASYNC(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    @property
    def DB_URL_SYNC(self):
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int

    UNCONFIRMED_REGISTRATION_EXPIRE_MINUTES: int
    CONFIRM_CODE_EXPIRE_MINUTES: int
    FORGOT_PASSWORD_EXPIRE_MINUTES: int

    email_settings: EmailSettings = EmailSettings()  # type: ignore reportCallIssue
    redis_settings: RedisSettings = RedisSettings()  # type: ignore reportCallIssue

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")

    ALLOWED_EXTENSIONS: set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".heic",
        ".heif",
        ".webp",
        ".tiff",
        ".bmp",
    }

    UNIT_IMAGES_LIMIT: int = 10

    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET: str
    S3_ENDPOINT_URL: str
    S3_PUBLIC_URL: str

    ROOT_PATH: str


settings = Settings()  # type: ignore reportCallIssue
