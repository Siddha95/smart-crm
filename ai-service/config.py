from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    claude_api_key: str = ""
    openai_api_key: str = ""

    db_name: str = "smart_crm"
    db_user: str = ""
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432

    class Config:
        env_file = ".env"


settings = Settings()
