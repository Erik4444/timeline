from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/timeline.db"
    data_dir: Path = Path("./data")

    ollama_url: str = "http://localhost:11434"
    lmstudio_url: str = "http://localhost:1234/v1"
    ai_backend: str = "auto"  # "auto" | "ollama" | "lmstudio" | "none"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_llm_model: str = "mistral:7b-instruct"
    lmstudio_embed_model: str = "nomic-embed-text-v1.5"
    lmstudio_llm_model: str = "mistral-7b-instruct"

    import_batch_size: int = 500
    thumbnail_max_size: int = 300

    semantic_search_threshold: float = 0.75
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
