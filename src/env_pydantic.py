from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    telegram_api_key: str
    proxy_http: str
    proxy_https: str
    openAI_api_key: str

    class Config:
        env_file = ".env"


settings = BotSettings()
