from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

from app.storage import S3Storage


def test_presigned_url_matches_aws_published_example():
    """The worked example from the AWS Signature V4 query-string documentation."""
    storage = S3Storage("https://examplebucket.s3.amazonaws.com", "us-east-1", "",
                        "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    url = storage.presign("GET", "https://examplebucket.s3.amazonaws.com/test.txt", 86400,
                          timestamp=datetime(2013, 5, 24, tzinfo=timezone.utc))
    signature = parse_qs(urlsplit(url).query)["X-Amz-Signature"][0]
    assert signature == "aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404"


def test_s3_upload_and_links(monkeypatch):
    sent = {}

    class Reply:
        status_code = 200
        text = ""

    def fake_put(url, data, headers, timeout):
        sent.update(url=url, body=data.read(), headers=headers)
        return Reply()

    monkeypatch.setattr("app.storage.requests.put", fake_put)
    storage = S3Storage("https://ref.storage.supabase.co/storage/v1/s3", "ap-south-1", "media",
                        "id", "secret")
    storage.save(BytesIO(b"hello"), "materials/abc.pdf", "application/pdf", "My notes.pdf")
    assert sent["body"] == b"hello" and sent["headers"]["Content-Length"] == "5"
    assert "attachment" in sent["headers"]["Content-Disposition"]
    assert urlsplit(sent["url"]).path == "/storage/v1/s3/media/materials/abc.pdf"
    link = storage.url("ignored", "materials/abc.pdf", download_name="My notes.pdf")
    assert "response-content-disposition=" in link and "X-Amz-Signature=" in link
