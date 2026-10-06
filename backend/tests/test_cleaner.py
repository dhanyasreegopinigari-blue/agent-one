from app.ingestion.cleaner import clean
from app.ingestion.types import Segment


def test_cleaner_removes_page_numbers():
    segments = [
        # Top page number (y1 <= 10% of 1000 = 100)
        Segment(page=1, text="Page 1", bbox=(50, 20, 100, 50), page_w=800, page_h=1000),
        # Real content
        Segment(page=1, text="Hello world, this is a real paragraph.", bbox=(50, 150, 750, 200), page_w=800, page_h=1000),
        # Bottom page number (y0 >= 90% of 1000 = 900)
        Segment(page=1, text="1 of 10", bbox=(350, 920, 450, 950), page_w=800, page_h=1000),
        # Middle text with "Page 1" should NOT be removed
        Segment(page=1, text="Page 1 contains important terms.", bbox=(50, 500, 750, 530), page_w=800, page_h=1000),
    ]

    cleaned = clean(segments, page_count=1)
    texts = [s.text for s in cleaned]
    assert "Page 1" not in texts
    assert "1 of 10" not in texts
    assert "Hello world, this is a real paragraph." in texts
    assert "Page 1 contains important terms." in texts


def test_cleaner_repeating_header_footer():
    # Only triggers when page_count >= 4
    segments = []
    for p in range(1, 5):
        # Repeating header at y1 <= 80 (top 8% of 1000)
        segments.append(Segment(page=p, text="Confidential Document 2026", bbox=(50, 10, 300, 40), page_w=800, page_h=1000))
        # Unique page content
        segments.append(Segment(page=p, text=f"Important content on page {p}.", bbox=(50, 200, 750, 300), page_w=800, page_h=1000))
        # Repeating footer at y0 >= 920 (bottom 8% of 1000)
        segments.append(Segment(page=p, text="All rights reserved Contoso Ltd", bbox=(50, 940, 400, 970), page_w=800, page_h=1000))

    cleaned = clean(segments, page_count=4)
    texts = [s.text for s in cleaned]
    assert all("Confidential Document" not in t for t in texts)
    assert all("All rights reserved" not in t for t in texts)
    assert len(cleaned) == 4
    for p in range(1, 5):
        assert f"Important content on page {p}." in texts


def test_cleaner_does_not_remove_header_if_few_pages():
    # When page_count < 4, repeating headers should not be dropped
    segments = [
        Segment(page=1, text="Document Header", bbox=(50, 10, 300, 40), page_w=800, page_h=1000),
        Segment(page=1, text="Content 1", bbox=(50, 200, 750, 300), page_w=800, page_h=1000),
        Segment(page=2, text="Document Header", bbox=(50, 10, 300, 40), page_w=800, page_h=1000),
        Segment(page=2, text="Content 2", bbox=(50, 200, 750, 300), page_w=800, page_h=1000),
    ]

    cleaned = clean(segments, page_count=2)
    texts = [s.text for s in cleaned]
    assert texts.count("Document Header") == 2
