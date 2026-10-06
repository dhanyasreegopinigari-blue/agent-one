from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["development", "production", "test"] = "development"
    data_dir: Path = Path("./data")

    # CORS
    cors_origins: str = "http://localhost:3000"      # comma-separated
    cors_origin_regex: str | None = None              # e.g. ^https://agent-one-[a-z0-9-]+\.vercel\.app$

    # Auth (Supabase)
    auth_disabled: bool = False                       # dev/test ONLY; refused when env=production
    dev_user_id: str = "dev-user"
    supabase_url: str | None = None                   # https://<ref>.supabase.co
    supabase_jwt_secret: str | None = None            # set => HS256 verification; unset => JWKS

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"            # [VERIFY] pulled and suitable
    ollama_embed_model: str = "nomic-embed-text"      # [VERIFY] pulled
    ollama_num_ctx: int = 8192
    ollama_keep_alive: str = "30m"
    ollama_connect_timeout_s: float = 3.0
    ollama_first_token_timeout_s: float = 90.0        # cold model load can be slow
    ollama_idle_timeout_s: float = 30.0
    ollama_retries: int = 1                           # retries on connect errors before fallback
    ollama_breaker_fails: int = 3
    ollama_breaker_cooldown_s: int = 30

    # Gemini (fallback only)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3-flash-preview"      # [VERIFY] run scripts/list_gemini_models.py
    allow_gemini_fallback: bool = True

    # Generation
    temperature: float = 0.1
    max_output_tokens: int = 1024

    # Embedding
    embed_doc_prefix: str = "search_document: "       # nomic-embed-text convention; set "" for other models
    embed_query_prefix: str = "search_query: "
    embed_batch_size: int = 16

    # Ingestion
    max_upload_mb: int = 50
    max_pages: int = 500
    min_text_chars: int = 200
    chunk_chars: int = 2400                           # ≈ 600 tokens
    chunk_overlap_chars: int = 360
    min_chunk_chars: int = 200

    # Retrieval
    top_k: int = 6
    min_score: float = 0.40                           # TUNE in P9 with scripts/eval_live.py
    score_margin: float = 0.12
    max_context_chars: int = 12000
    history_turns: int = 4

    # Limits
    max_sessions_per_user: int = 100
    max_concurrent_generations: int = 2
    index_cache_size: int = 8

    # Web search
    web_search_provider: Literal["searxng", "tavily"] = "searxng"
    searxng_url: str = "http://searxng:8080"
    tavily_api_key: str | None = None
    web_max_results: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.env == "production" and s.auth_disabled:
        raise RuntimeError("AUTH_DISABLED must be false when ENV=production")
    return s
