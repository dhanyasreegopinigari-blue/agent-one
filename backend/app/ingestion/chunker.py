import re
from collections import defaultdict

from app.ingestion.types import Chunk, Segment

SENTENCE_SPLIT_REGEX = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"(\[])')


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    parts = []
    remaining = sentence
    while len(remaining) > max_chars:
        # Find whitespace nearest max_chars
        idx = remaining.rfind(" ", 0, max_chars)
        if idx == -1:
            idx = max_chars
        part = remaining[:idx].strip()
        if part:
            parts.append(part)
        remaining = remaining[idx:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def _split_oversized_segment(seg: Segment, chunk_chars: int) -> list[Segment]:
    if len(seg.text) <= chunk_chars:
        return [seg]

    sentences = [s.strip() for s in SENTENCE_SPLIT_REGEX.split(seg.text) if s.strip()]
    if not sentences:
        sentences = [seg.text]

    pieces: list[str] = []
    current_piece = ""

    for s in sentences:
        sub_parts = _split_long_sentence(s, chunk_chars) if len(s) > chunk_chars else [s]
        for sp in sub_parts:
            if not current_piece:
                current_piece = sp
            elif len(current_piece) + 1 + len(sp) <= chunk_chars:
                current_piece += " " + sp
            else:
                pieces.append(current_piece)
                current_piece = sp

    if current_piece:
        pieces.append(current_piece)

    return [
        Segment(
            page=seg.page,
            text=p,
            bbox=seg.bbox,
            page_w=seg.page_w,
            page_h=seg.page_h,
        )
        for p in pieces
    ]


def _build_chunk(chunk_id: int, segments: list[Segment]) -> Chunk:
    text = "\n".join(s.text for s in segments)
    pages = sorted({s.page for s in segments})
    page_start = min(pages)
    page_end = max(pages)

    # Group bboxes by page to compute union
    page_bboxes: dict[int, list[tuple[float, float, float, float]]] = defaultdict(list)
    page_dims: dict[int, tuple[float, float]] = {}
    for s in segments:
        page_bboxes[s.page].append(s.bbox)
        page_dims[s.page] = (s.page_w, s.page_h)

    regions: list[dict] = []
    for p in pages:
        bboxes = page_bboxes[p]
        w, h = page_dims[p]
        min_x0 = min(b[0] for b in bboxes)
        min_y0 = min(b[1] for b in bboxes)
        max_x1 = max(b[2] for b in bboxes)
        max_y1 = max(b[3] for b in bboxes)

        # Normalize 0..1 and clamp
        norm_bbox = [
            round(min(1.0, max(0.0, min_x0 / w)), 4),
            round(min(1.0, max(0.0, min_y0 / h)), 4),
            round(min(1.0, max(0.0, max_x1 / w)), 4),
            round(min(1.0, max(0.0, max_y1 / h)), 4),
        ]
        regions.append({"page": p, "bbox": norm_bbox})

    return Chunk(
        id=chunk_id,
        text=text,
        page_start=page_start,
        page_end=page_end,
        regions=regions,
        char_count=len(text),
    )


def chunk(
    segments: list[Segment],
    chunk_chars: int,
    overlap_chars: int,
    min_chunk_chars: int,
) -> list[Chunk]:
    if not segments:
        return []

    # 1. Split oversized segments
    norm_segments: list[Segment] = []
    for seg in segments:
        norm_segments.extend(_split_oversized_segment(seg, chunk_chars))

    # 2. Accumulate chunks with overlap
    raw_chunks: list[list[Segment]] = []
    cur: list[Segment] = []
    cur_len = 0

    for s in norm_segments:
        s_len = len(s.text)
        additional_len = (1 + s_len) if cur else s_len
        if cur and (cur_len + additional_len > chunk_chars):
            raw_chunks.append(list(cur))
            # Seed overlap by walking backwards
            overlap_segs: list[Segment] = []
            overlap_len = 0
            for prev_seg in reversed(cur):
                prev_len = len(prev_seg.text)
                cost = (1 + prev_len) if overlap_segs else prev_len
                if overlap_len + cost <= overlap_chars:
                    overlap_segs.append(prev_seg)
                    overlap_len += cost
                else:
                    break
            overlap_segs.reverse()
            cur = list(overlap_segs)
            cur_len = sum(len(x.text) for x in cur) + max(0, len(cur) - 1)

        cur.append(s)
        cur_len = sum(len(x.text) for x in cur) + max(0, len(cur) - 1)

    if cur:
        raw_chunks.append(cur)

    # 3. Handle tiny final chunk
    if len(raw_chunks) > 1:
        last_chunk = raw_chunks[-1]
        last_text = "\n".join(s.text for s in last_chunk)
        if len(last_text) < min_chunk_chars:
            prev_chunk = raw_chunks[-2]
            # Merge without duplicating segments already present from overlap
            prev_ids = {id(s) for s in prev_chunk}
            to_add = [s for s in last_chunk if id(s) not in prev_ids]
            merged_segs = prev_chunk + to_add
            merged_text = "\n".join(s.text for s in merged_segs)
            if len(merged_text) <= 1.25 * chunk_chars:
                raw_chunks[-2] = merged_segs
                raw_chunks.pop()

    # 4. Build Chunk objects
    return [_build_chunk(idx, segs) for idx, segs in enumerate(raw_chunks)]
