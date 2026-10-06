import time

import pymupdf

from tests.conftest import HashEmbedder, make_jwt, make_pdf


def test_upload_non_pdf_rejected(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
    sess_id = sess["id"]

    files = {"file": ("test.txt", b"plain text not a pdf", "text/plain")}
    res = client.post(f"/sessions/{sess_id}/document", files=files, headers=headers)
    assert res.status_code == 415
    assert res.json()["error"]["code"] == "NOT_A_PDF"


def test_upload_to_web_session_rejected(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "web"}, headers=headers).json()
    sess_id = sess["id"]

    pdf_bytes = make_pdf(["Some sample content for testing"])
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    res = client.post(f"/sessions/{sess_id}/document", files=files, headers=headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "WRONG_SESSION_TYPE"


def test_upload_oversize_rejected(client, temp_settings, monkeypatch):
    monkeypatch.setattr(temp_settings, "max_upload_mb", 1)  # 1 MB
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
    sess_id = sess["id"]

    # 1.5 MB fake PDF with %PDF- header
    oversized = b"%PDF-" + b"0" * (1500 * 1024)
    files = {"file": ("big.pdf", oversized, "application/pdf")}
    res = client.post(f"/sessions/{sess_id}/document", files=files, headers=headers)
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_and_ingestion_lifecycle(client, temp_settings, monkeypatch):
    embedder = HashEmbedder()
    monkeypatch.setattr("app.ingestion.pipeline._get_embedder", lambda override=None: embedder)

    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
    sess_id = sess["id"]

    # Create valid PDF with enough text
    sample_page = "Contract Agreement between Alpha and Beta. " * 30
    pdf_bytes = make_pdf([sample_page, sample_page])
    files = {"file": ("agreement.pdf", pdf_bytes, "application/pdf")}

    res = client.post(f"/sessions/{sess_id}/document", files=files, headers=headers)
    assert res.status_code == 202
    res_data = res.json()
    assert res_data["document"]["status"] in ("processing", "ready")
    assert res_data["title"] == "agreement"

    # Poll status until ready
    for _ in range(30):
        stat = client.get(f"/sessions/{sess_id}/status", headers=headers).json()
        if stat["status"] == "ready":
            break
        time.sleep(0.1)

    assert stat["status"] == "ready"
    assert stat["progress"] == 100
    assert stat["page_count"] == 2
    assert stat["n_chunks"] > 0

    # Second upload to ready session must be rejected with 409 DOCUMENT_EXISTS
    res_second = client.post(f"/sessions/{sess_id}/document", files=files, headers=headers)
    assert res_second.status_code == 409
    assert res_second.json()["error"]["code"] == "DOCUMENT_EXISTS"

    # Download document
    doc_res = client.get(f"/sessions/{sess_id}/document", headers=headers)
    assert doc_res.status_code == 200
    assert doc_res.headers["content-type"] == "application/pdf"
    assert b"%PDF-" in doc_res.content[:10]


def test_upload_no_text_pdf_fails_and_allows_reupload(client, temp_settings, monkeypatch):
    embedder = HashEmbedder()
    monkeypatch.setattr("app.ingestion.pipeline._get_embedder", lambda override=None: embedder)

    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
    sess_id = sess["id"]

    # PDF with no text
    doc = pymupdf.open()
    doc.new_page()
    empty_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("empty.pdf", empty_bytes, "application/pdf")}
    res = client.post(f"/sessions/{sess_id}/document", files=files, headers=headers)
    assert res.status_code == 202

    # Poll until failed
    for _ in range(30):
        stat = client.get(f"/sessions/{sess_id}/status", headers=headers).json()
        if stat["status"] == "failed":
            break
        time.sleep(0.1)

    assert stat["status"] == "failed"
    assert stat["error_code"] == "PDF_NO_TEXT"

    # Re-upload with valid PDF is now allowed because previous failed
    good_page = "Valid contract text that has plenty of characters to pass the threshold. " * 20
    good_bytes = make_pdf([good_page])
    files_good = {"file": ("valid.pdf", good_bytes, "application/pdf")}
    res_retry = client.post(f"/sessions/{sess_id}/document", files=files_good, headers=headers)
    assert res_retry.status_code == 202
