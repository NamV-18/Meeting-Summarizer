from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str | None = None
    asr_model: str = "gpt-4o-mini-transcribe"
    llm_model: str = "gpt-4o-mini"
    database_url: str = "sqlite:///./data.db"
    asr_provider: str = "openai"  # openai | faster-whisper
    llm_provider: str = "openai"  # openai | heuristic

    class Config:
        env_file = ".env"


settings = Settings()  # load on import


