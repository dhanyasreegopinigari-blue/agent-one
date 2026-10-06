from dataclasses import dataclass


class IngestionError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Segment:
    page: int
    text: str
    bbox: tuple[float, float, float, float]
    page_w: float
    page_h: float


@dataclass
class Chunk:
    id: int
    text: str
    page_start: int
    page_end: int
    regions: list[dict]
    char_count: int
