"""File storage for thumbnails, videos and study materials.

LocalStorage keeps files on disk (development). S3Storage works with any
S3-compatible service and signs requests with AWS Signature Version 4.
"""
import hashlib
import hmac
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit

import requests


def _encode(value):
    return quote(str(value), safe="-_.~")


def content_disposition(filename):
    ascii_name = filename.encode("ascii", "ignore").decode().replace('"', "").replace("\\", "")
    return f"attachment; filename=\"{ascii_name or 'download'}\"; filename*=UTF-8''{_encode(filename)}"


class LocalStorage:
    def __init__(self, root, secret):
        self.root = Path(root).resolve()
        self.secret = secret.encode()

    def path(self, key):
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def save(self, stream, key, content_type, download_name=None):
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as target:
            shutil.copyfileobj(stream, target)

    def delete(self, key):
        self.path(key).unlink(missing_ok=True)

    def signature(self, key, expires, download_name):
        message = f"{key}\n{expires}\n{download_name or ''}".encode()
        return hmac.new(self.secret, message, hashlib.sha256).hexdigest()

    def verify(self, key, expires, download_name, signature):
        if not expires.isdigit() or int(expires) < time.time():
            return False
        expected = self.signature(key, expires, download_name)
        return hmac.compare_digest(expected.encode(), signature.encode())

    def url(self, base_url, key, expires_in=6 * 3600, download_name=None):
        """A temporary link, so <video> and downloads work without an auth header."""
        expires = str(int(time.time()) + expires_in)
        query = {"expires": expires, "signature": self.signature(key, expires, download_name)}
        if download_name:
            query["download"] = download_name
        return f"{base_url}/api/files/signed/{key}?{urlencode(query)}"


class S3Storage:
    def __init__(self, endpoint, region, bucket, access_key, secret_key):
        self.endpoint = endpoint.rstrip("/")
        self.region = region
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key

    def presign(self, method, url, expires_in, extra_query=None, timestamp=None):
        """Adds an AWS Signature V4 query-string signature to a URL."""
        timestamp = timestamp or datetime.now(timezone.utc)
        amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
        day = amz_date[:8]
        scope = f"{day}/{self.region}/s3/aws4_request"
        parts = urlsplit(url)
        query = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self.access_key}/{scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires_in),
            "X-Amz-SignedHeaders": "host",
        }
        query.update(extra_query or {})
        canonical_query = "&".join(f"{_encode(k)}={_encode(v)}" for k, v in sorted(query.items()))
        canonical_request = "\n".join([
            method, parts.path or "/", canonical_query,
            f"host:{parts.netloc}\n", "host", "UNSIGNED-PAYLOAD",
        ])
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256", amz_date, scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ])
        signing_key = ("AWS4" + self.secret_key).encode()
        for item in (day, self.region, "s3", "aws4_request"):
            signing_key = hmac.new(signing_key, item.encode(), hashlib.sha256).digest()
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        return f"{parts.scheme}://{parts.netloc}{parts.path}?{canonical_query}&X-Amz-Signature={signature}"

    def object_url(self, key):
        return f"{self.endpoint}/{self.bucket}/{quote(key)}"

    def save(self, stream, key, content_type, download_name=None):
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
        headers = {"Content-Type": content_type, "Content-Length": str(size)}
        if download_name:
            headers["Content-Disposition"] = content_disposition(download_name)
        url = self.presign("PUT", self.object_url(key), 3600)
        response = requests.put(url, data=stream, headers=headers, timeout=(15, 600))
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Storage upload failed ({response.status_code}): {response.text[:300]}")

    def delete(self, key):
        # Best effort: a leftover object must not break the user's request.
        try:
            requests.delete(self.presign("DELETE", self.object_url(key), 300), timeout=30)
        except requests.RequestException:
            pass

    def url(self, base_url, key, expires_in=6 * 3600, download_name=None):
        extra = {}
        if download_name:
            extra["response-content-disposition"] = content_disposition(download_name)
        return self.presign("GET", self.object_url(key), expires_in, extra)


def build_storage(config):
    if config["STORAGE_BACKEND"] == "s3":
        return S3Storage(config["S3_ENDPOINT"], config["S3_REGION"], config["S3_BUCKET"],
                         config["S3_ACCESS_KEY_ID"], config["S3_SECRET_ACCESS_KEY"])
    return LocalStorage(config["UPLOAD_DIR"], config["SECRET_KEY"])
