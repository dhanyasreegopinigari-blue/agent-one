import pymupdf
import pytest

from app.ingestion.pdf_parser import PyMuPdfParser
from app.ingestion.types import IngestionError


def test_pdf_parser_corrupt_file(tmp_path):
    bad_pdf = tmp_path / "corrupt.pdf"
    bad_pdf.write_bytes(b"not a real pdf file at all")
    parser = PyMuPdfParser()
    with pytest.raises(IngestionError) as exc_info:
        parser.parse(bad_pdf)
    assert exc_info.value.code == "PDF_CORRUPT"


def test_pdf_parser_no_text(tmp_path):
    empty_pdf = tmp_path / "empty.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(empty_pdf))
    doc.close()

    parser = PyMuPdfParser()
    with pytest.raises(IngestionError) as exc_info:
        parser.parse(empty_pdf)
    assert exc_info.value.code == "PDF_NO_TEXT"


def test_pdf_parser_encrypted(tmp_path):
    enc_pdf = tmp_path / "encrypted.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Secret text that is encrypted")
    doc.save(
        str(enc_pdf),
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw="password123",
        owner_pw="owner123",
    )
    doc.close()

    parser = PyMuPdfParser()
    with pytest.raises(IngestionError) as exc_info:
        parser.parse(enc_pdf)
    assert exc_info.value.code == "PDF_ENCRYPTED"


def test_pdf_parser_too_many_pages(tmp_path, temp_settings, monkeypatch):
    monkeypatch.setattr(temp_settings, "max_pages", 2)
    pdf_path = tmp_path / "many_pages.pdf"
    doc = pymupdf.open()
    for _ in range(3):
        p = doc.new_page()
        p.insert_text((50, 50), "This is sample text on a page.")
    doc.save(str(pdf_path))
    doc.close()

    parser = PyMuPdfParser()
    with pytest.raises(IngestionError) as exc_info:
        parser.parse(pdf_path)
    assert exc_info.value.code == "PDF_TOO_MANY_PAGES"


def test_pdf_parser_two_column_order_and_dehyphenation(tmp_path):
    pdf_path = tmp_path / "twocol.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)

    # 1. Wide top header: y1 = 70
    page.insert_textbox(
        pymupdf.Rect(50, 30, 550, 70),
        "Title of the Two Column Agreement Document",
    )

    # 2. Left column: x1 < 0.55 * 600 = 330. Need >= 3 blocks.
    page.insert_textbox(
        pymupdf.Rect(50, 100, 250, 180),
        "Left block 1 with dehyphen-\nation test.",
    )
    page.insert_textbox(
        pymupdf.Rect(50, 200, 250, 280),
        "Left block 2 contains information about first party.",
    )
    page.insert_textbox(
        pymupdf.Rect(50, 300, 250, 380),
        "Left block 3 specifies the scope of work and conditions.",
    )

    # 3. Right column: x0 > 0.45 * 600 = 270. Need >= 3 blocks.
    page.insert_textbox(
        pymupdf.Rect(320, 100, 550, 180),
        "Right block 1 details financial payments and compensation.",
    )
    page.insert_textbox(
        pymupdf.Rect(320, 200, 550, 280),
        "Right block 2 details liability and indemnification clauses.",
    )
    page.insert_textbox(
        pymupdf.Rect(320, 300, 550, 380),
        "Right block 3 details governing law and dispute resolution.",
    )

    doc.save(str(pdf_path))
    doc.close()

    parser = PyMuPdfParser()
    parsed = parser.parse(pdf_path)
    assert parsed.page_count == 1
    texts = [s.text for s in parsed.segments]

    # Dehyphenation check: "dehyphenation"
    assert any("dehyphenation" in t for t in texts)

    # Order check: Header -> Left blocks -> Right blocks
    full_text = " ".join(texts)
    pos_header = full_text.find("Title of the Two Column")
    pos_left1 = full_text.find("Left block 1")
    pos_left3 = full_text.find("Left block 3")
    pos_right1 = full_text.find("Right block 1")

    assert pos_header < pos_left1
    assert pos_left1 < pos_left3
    assert pos_left3 < pos_right1
