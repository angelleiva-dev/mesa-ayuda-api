from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída desde variables de entorno o archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://mesa:mesa@localhost:5432/mesa_ayuda"
    secret_key: str = "dev-secret-cambiar-en-produccion"
    access_token_minutes: int = 60
    algorithm: str = "HS256"


settings = Settings()
