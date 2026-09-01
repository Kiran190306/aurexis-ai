from app.api.v1.endpoints.files import validate_upload_file


def test_validate_upload_file_accepts_safe_file():
    extension = validate_upload_file("report.pdf", "application/pdf", 1024)
    assert extension == "pdf"


def test_validate_upload_file_rejects_mismatched_content_type():
    try:
        validate_upload_file("report.pdf", "text/html", 1024)
    except Exception as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("expected upload validation to reject the content type")
