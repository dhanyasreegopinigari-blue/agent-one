import math
import re
from collections import defaultdict

from app.ingestion.types import Segment

PAGE_NUM_PATTERN = re.compile(
    r"^\s*(page\s*)?\d+(\s*(of|/)\s*\d+)?\s*$", re.IGNORECASE
)


def clean(segments: list[Segment], page_count: int) -> list[Segment]:
    # 1. Identify repeating headers/footers if page_count >= 4
    repeating_keys = set()
    if page_count >= 4:
        key_pages: dict[str, set[int]] = defaultdict(set)
        for seg in segments:
            y0 = seg.bbox[1]
            y1 = seg.bbox[3]
            is_edge = (y1 <= 0.08 * seg.page_h) or (y0 >= 0.92 * seg.page_h)
            if is_edge:
                key = re.sub(r"\d+", "#", seg.text.strip().lower())
                key_pages[key].add(seg.page)

        threshold = max(3, math.ceil(0.5 * page_count))
        for key, pages in key_pages.items():
            if len(pages) >= threshold:
                repeating_keys.add(key)

    cleaned: list[Segment] = []
    for seg in segments:
        y0 = seg.bbox[1]
        y1 = seg.bbox[3]

        # Check page numbers
        is_top_or_bottom_10 = (y1 <= 0.10 * seg.page_h) or (y0 >= 0.90 * seg.page_h)
        if is_top_or_bottom_10 and PAGE_NUM_PATTERN.match(seg.text):
            continue

        # Check repeating headers/footers
        is_edge_8 = (y1 <= 0.08 * seg.page_h) or (y0 >= 0.92 * seg.page_h)
        if is_edge_8:
            key = re.sub(r"\d+", "#", seg.text.strip().lower())
            if key in repeating_keys:
                continue

        # Strip whitespace, collapse internal whitespace
        norm_text = re.sub(r"\s+", " ", seg.text.strip())
        if not norm_text:
            continue

        cleaned.append(
            Segment(
                page=seg.page,
                text=norm_text,
                bbox=seg.bbox,
                page_w=seg.page_w,
                page_h=seg.page_h,
            )
        )

    return cleaned
