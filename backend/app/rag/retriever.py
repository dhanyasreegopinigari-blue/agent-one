from dataclasses import dataclass
from typing import Any


@dataclass
class Hit:
    label: str
    chunk: dict[str, Any]
    score: float


def hit_to_source(hit: Hit) -> dict[str, Any]:
    c = hit.chunk
    snippet = c.get("text", "")[:300]
    return {
        "id": hit.label,
        "chunk_id": c.get("id", 0),
        "page_start": c.get("page_start", 1),
        "page_end": c.get("page_end", 1),
        "snippet": snippet,
        "score": round(hit.score, 4),
        "regions": c.get("regions", []),
    }


async def retrieve(
    question: str,
    session_id: str,
    *,
    embedder: Any,
    cache: Any,
    settings: Any,
) -> list[Hit]:
    store, chunks = cache.get(session_id)
    q = await embedder.embed_query(question)
    raw = store.search(q, settings.top_k)
    if not raw:
        return []

    top = raw[0][1]
    kept = [
        (i, s)
        for i, s in raw
        if s >= settings.min_score and s >= top - settings.score_margin
    ]
    if not kept:
        return []

    budget = settings.max_context_chars
    selected_hits: list[Hit] = []
    current_chars = 0

    for n, (i, s) in enumerate(kept):
        chunk_data = dict(chunks[i])
        text_len = len(chunk_data.get("text", ""))

        if n == 0:
            if text_len > budget:
                chunk_data["text"] = chunk_data["text"][:budget]
            current_chars += len(chunk_data["text"])
            selected_hits.append(Hit(label=f"S{n+1}", chunk=chunk_data, score=s))
        else:
            if current_chars + text_len > budget:
                break
            current_chars += text_len
            selected_hits.append(Hit(label=f"S{n+1}", chunk=chunk_data, score=s))

    return selected_hits
