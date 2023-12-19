from pydantic_settings import BaseSettings
from pathlib import Path


class BotSettings(BaseSettings):
    telegram_api_key: str
    proxy_http: str
    proxy_https: str
    openAI_api_key: str

    class Config:
        case_sensitive = False
        BASE_DIR = Path(__file__).resolve().parent.parent
        env_file = (str(BASE_DIR) + "/.env").replace("//", "/")

try:
    settings = BotSettings()
except Exception as e:
    print(str(e))
