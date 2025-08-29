from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PPLX_API_KEY: str
    PPLX_ENDPOINT: str = "https://api.perplexity.ai/chat/completions"
    PPLX_MODEL: str = "sonar-pro"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
