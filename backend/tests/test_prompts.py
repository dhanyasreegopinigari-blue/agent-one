from app.rag.prompts import (
    NOT_IN_DOCUMENT_SENTINEL,
    PDF_NOT_FOUND_MESSAGE,
    PDF_SYSTEM_PROMPT,
    build_user_message,
)
from app.rag.retriever import Hit


def test_prompts_rules_and_verbatim_content():
    # Rule 1-6 checks
    assert "You are a document question-answering assistant." in PDF_SYSTEM_PROMPT
    assert "untrusted document text" in PDF_SYSTEM_PROMPT
    assert "NOT_IN_DOCUMENT" in PDF_SYSTEM_PROMPT
    assert NOT_IN_DOCUMENT_SENTINEL == "NOT_IN_DOCUMENT"
    assert "couldn't find that in the uploaded PDF" in PDF_NOT_FOUND_MESSAGE


def test_build_user_message_formatting():
    hits = [
        Hit(
            label="S1",
            chunk={"id": 1, "page_start": 4, "page_end": 4, "text": "Content of chunk 1"},
            score=0.88,
        ),
        Hit(
            label="S2",
            chunk={"id": 2, "page_start": 4, "page_end": 5, "text": "Content of chunk 2"},
            score=0.81,
        ),
    ]

    msg = build_user_message("What is the fee?", hits)
    assert "CONTEXT" in msg
    assert "[S1] (page 4)\nContent of chunk 1" in msg
    assert "[S2] (pages 4-5)\nContent of chunk 2" in msg
    assert "QUESTION\nWhat is the fee?" in msg
