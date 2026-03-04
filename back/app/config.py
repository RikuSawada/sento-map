from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    cors_origin: str = "http://localhost:4200"
    jwt_access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
