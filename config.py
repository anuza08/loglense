from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jenkins_url: str = "http://localhost:8080"
    jenkins_user: str = "admin"
    jenkins_token: str = ""

    anthropic_api_key: str = ""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 2048

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
