from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Vibeconomics Agentic Framework"
    # EXAMPLE_API_KEY: str = "your_api_key_here"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
