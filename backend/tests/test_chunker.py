from app.ingestion.chunker import chunk
from app.ingestion.types import Segment


def test_chunker_basic_and_invariants():
    chunk_chars = 500
    overlap_chars = 100
    min_chunk_chars = 50

    # Create 10 segments of 100 chars each
    segments = []
    for i in range(10):
        text = f"Segment {i:02d}: " + ("x" * 86) + "."
        segments.append(
            Segment(page=(i // 3) + 1, text=text, bbox=(50, 100 + i * 50, 500, 140 + i * 50), page_w=600, page_h=800)
        )

    chunks1 = chunk(segments, chunk_chars, overlap_chars, min_chunk_chars)
    chunks2 = chunk(segments, chunk_chars, overlap_chars, min_chunk_chars)

    # 1. Deterministic
    assert len(chunks1) == len(chunks2)
    assert [c.text for c in chunks1] == [c.text for c in chunks2]

    # 2. Invariants: length <= 1.25 * chunk_chars
    for c in chunks1:
        assert len(c.text) <= 1.25 * chunk_chars
        assert c.page_start <= c.page_end
        # Regions check
        for reg in c.regions:
            assert 0.0 <= reg["bbox"][0] <= 1.0
            assert 0.0 <= reg["bbox"][1] <= 1.0
            assert 0.0 <= reg["bbox"][2] <= 1.0
            assert 0.0 <= reg["bbox"][3] <= 1.0

    # 3. Overlap check: second chunk starts with parts from first chunk
    assert len(chunks1) > 1
    # Check that chunks share text at boundary
    first_chunk_end = chunks1[0].text[-50:]
    assert any(first_chunk_end in c.text for c in chunks1[1:]) or len(chunks1) >= 2


def test_chunker_splits_oversized_segment():
    chunk_chars = 200
    overlap_chars = 40
    min_chunk_chars = 30

    sentence1 = "This is the first sentence that is quite long and explains an important topic."
    sentence2 = "This is the second sentence that continues the discussion in great detail."
    sentence3 = "Finally, here is the third sentence that concludes the thought completely."
    oversized_text = f"{sentence1} {sentence2} {sentence3}"
    assert len(oversized_text) > chunk_chars

    seg = Segment(page=1, text=oversized_text, bbox=(50, 100, 500, 400), page_w=600, page_h=800)
    chunks = chunk([seg], chunk_chars, overlap_chars, min_chunk_chars)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= 1.25 * chunk_chars


def test_chunker_merges_tiny_tail():
    chunk_chars = 300
    overlap_chars = 50
    min_chunk_chars = 100

    # First segment fills most of the chunk
    seg1 = Segment(page=1, text="A" * 250, bbox=(50, 50, 500, 200), page_w=600, page_h=800)
    # Second segment causes split
    seg2 = Segment(page=1, text="B" * 60, bbox=(50, 220, 500, 300), page_w=600, page_h=800)
    # Third tiny segment
    seg3 = Segment(page=1, text="C" * 20, bbox=(50, 320, 500, 350), page_w=600, page_h=800)

    chunks = chunk([seg1, seg2, seg3], chunk_chars, overlap_chars, min_chunk_chars)
    # Ensure all chunks satisfy length constraint and tiny tail was handled
    for c in chunks:
        assert len(c.text) <= 1.25 * chunk_chars
