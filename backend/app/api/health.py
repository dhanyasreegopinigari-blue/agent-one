import httpx
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health():
    settings = get_settings()

    # Ollama check
    ollama_reachable = False
    chat_model_available = False
    embed_model_available = False

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                ollama_reachable = True
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                chat_name = settings.ollama_chat_model
                embed_name = settings.ollama_embed_model

                chat_model_available = any(
                    m == chat_name or m == f"{chat_name}:latest" for m in models
                )
                embed_model_available = any(
                    m == embed_name or m == f"{embed_name}:latest" for m in models
                )
    except Exception:
        ollama_reachable = False

    # Gemini check
    gemini_configured = bool(settings.gemini_api_key)
    gemini_fallback = settings.allow_gemini_fallback

    # Web search check
    web_reachable = False
    if settings.web_search_provider == "searxng":
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(settings.searxng_url.rstrip("/"))
                web_reachable = resp.status_code < 500
        except Exception:
            web_reachable = False
    else:
        web_reachable = bool(settings.tavily_api_key)

    is_ok = ollama_reachable and chat_model_available and embed_model_available
    status = "ok" if is_ok else "degraded"

    return {
        "status": status,
        "ollama": {
            "reachable": ollama_reachable,
            "chat_model": {
                "name": settings.ollama_chat_model,
                "available": chat_model_available,
            },
            "embed_model": {
                "name": settings.ollama_embed_model,
                "available": embed_model_available,
            },
        },
        "gemini": {
            "configured": gemini_configured,
            "fallback_enabled": gemini_fallback,
        },
        "web_search": {
            "provider": settings.web_search_provider,
            "reachable": web_reachable,
        },
        "version": "3.0.0",
    }
