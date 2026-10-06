import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pymupdf

from app.config import get_settings
from app.ingestion.types import IngestionError, Segment


@dataclass
class ParsedPdf:
    page_count: int
    segments: list[Segment]


class PdfParser(Protocol):
    def parse(self, path: Path) -> ParsedPdf: ...


def normalize_block_text(text: str) -> str:
    raw_lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not raw_lines:
        return ""
    out_lines = [raw_lines[0]]
    for nxt in raw_lines[1:]:
        prev = out_lines[-1]
        if prev.endswith("-") and len(prev) > 1 and nxt and nxt[0].islower():
            out_lines[-1] = prev[:-1] + nxt
        else:
            out_lines.append(nxt)
    joined = " ".join(out_lines)
    return re.sub(r"\s+", " ", joined).strip()


class PyMuPdfParser:
    def parse(self, path: Path) -> ParsedPdf:
        settings = get_settings()
        try:
            doc = pymupdf.open(path)
        except Exception as e:
            raise IngestionError("PDF_CORRUPT", f"Failed to open PDF: {e}") from e

        try:
            if doc.needs_pass:
                raise IngestionError("PDF_ENCRYPTED", "This PDF is password-protected.")

            if doc.page_count > settings.max_pages:
                raise IngestionError(
                    "PDF_TOO_MANY_PAGES",
                    f"PDF has {doc.page_count} pages (max {settings.max_pages}).",
                )

            all_segments: list[Segment] = []

            for page in doc:
                page_num = page.number + 1
                page_w = float(page.rect.width)
                page_h = float(page.rect.height)

                raw_blocks = page.get_text("blocks")
                # b: (x0, y0, x1, y1, text, block_no, block_type)
                text_blocks = [b for b in raw_blocks if b[6] == 0 and b[4].strip()]
                if not text_blocks:
                    continue

                # Detect 2-column layout
                w = page_w
                left = [b for b in text_blocks if b[2] < 0.55 * w]
                right = [b for b in text_blocks if b[0] > 0.45 * w]
                wide = [b for b in text_blocks if (b[2] - b[0]) > 0.6 * w]

                if len(left) >= 3 and len(right) >= 3 and len(wide) <= 2:
                    top_col_y0 = min(b[1] for b in (left + right))
                    header_wide = sorted(
                        [b for b in wide if b[3] <= top_col_y0],
                        key=lambda b: (b[1], b[0]),
                    )
                    sorted_left = sorted(left, key=lambda b: (b[1], b[0]))
                    sorted_right = sorted(right, key=lambda b: (b[1], b[0]))
                    remaining_wide = sorted(
                        [b for b in wide if b[3] > top_col_y0],
                        key=lambda b: (b[1], b[0]),
                    )
                    ordered = header_wide + sorted_left + sorted_right + remaining_wide
                else:
                    ordered = text_blocks

                for b in ordered:
                    norm_text = normalize_block_text(b[4])
                    alnum_count = sum(1 for c in norm_text if c.isalnum())
                    if alnum_count < 2:
                        continue
                    all_segments.append(
                        Segment(
                            page=page_num,
                            text=norm_text,
                            bbox=(float(b[0]), float(b[1]), float(b[2]), float(b[3])),
                            page_w=page_w,
                            page_h=page_h,
                        )
                    )

            total_chars = sum(len(s.text) for s in all_segments)
            if total_chars < settings.min_text_chars:
                raise IngestionError(
                    "PDF_NO_TEXT",
                    "This PDF has no extractable text (it may be scanned). OCR is not supported yet.",
                )

            return ParsedPdf(page_count=doc.page_count, segments=all_segments)
        finally:
            doc.close()
