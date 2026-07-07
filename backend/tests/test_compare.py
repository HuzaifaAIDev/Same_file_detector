import io


def _txt_file(content: str, name: str = "file.txt"):
    return (name, io.BytesIO(content.encode("utf-8")), "text/plain")


def test_compare_requires_auth(client):
    resp = client.post("/api/v1/compare")
    assert resp.status_code == 401


def test_compare_identical_text_files(client, auth_headers):
    files = [
        ("base_files", _txt_file("The quick brown fox jumps over the lazy dog.", "base.txt")),
        ("compare_files", _txt_file("The quick brown fox jumps over the lazy dog.", "same.txt")),
        ("compare_files", _txt_file("Completely unrelated content about spreadsheets.", "diff.txt")),
    ]
    resp = client.post("/api/v1/compare", files=files, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["base_file_count"] == 1
    assert body["compare_file_count"] == 2

    results = {r["file_name"].split("_", 1)[-1]: r for r in body["results"]}
    same_result = next(r for r in body["results"] if "same.txt" in r["file_name"])
    diff_result = next(r for r in body["results"] if "diff.txt" in r["file_name"])
    assert same_result["status"] == "EXACT"
    assert same_result["score"] >= 90
    assert diff_result["status"] == "DIFFERENT"


def test_compare_rejects_disallowed_extension(client, auth_headers):
    files = [
        ("base_files", ("base.exe", io.BytesIO(b"binary"), "application/octet-stream")),
        ("compare_files", _txt_file("hello", "c.txt")),
    ]
    resp = client.post("/api/v1/compare", files=files, headers=auth_headers)
    assert resp.status_code == 422


def test_path_compare_disabled_by_default(client, auth_headers):
    resp = client.post(
        "/api/v1/compare/paths",
        json={"base_files": ["a.txt"], "compare_files": ["b.txt"]},
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_comparison_history(client, auth_headers):
    files = [
        ("base_files", _txt_file("history test content", "base.txt")),
        ("compare_files", _txt_file("history test content", "same.txt")),
    ]
    client.post("/api/v1/compare", files=files, headers=auth_headers)

    resp = client.get("/api/v1/compare/history", headers=auth_headers)
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) >= 1

    job_id = jobs[0]["id"]
    detail = client.get(f"/api/v1/compare/history/{job_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert "results" in detail.json()
