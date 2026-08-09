from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str = "placeholder_token"
    db_url: str = "sqlite+aiosqlite:///./gymmini.sqlite3"
    telegraph_token: str = "placeholder"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
