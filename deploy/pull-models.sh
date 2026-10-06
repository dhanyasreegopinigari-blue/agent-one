#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source ../backend/.env
docker compose exec ollama ollama pull "${OLLAMA_CHAT_MODEL:-llama3.1:8b}"
docker compose exec ollama ollama pull "${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
docker compose exec ollama ollama list
