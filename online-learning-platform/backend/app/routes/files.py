"""Serves stored files: public thumbnails and time-limited links for course content."""
import re

from flask import Blueprint, current_app, redirect, request, send_file

from ..errors import ApiError
from ..storage import LocalStorage

bp = Blueprint("files", __name__)

KEY_RE = re.compile(r"^(thumbnails|videos|materials)/[a-f0-9]{32}\.[a-z0-9]{2,5}$")


def _local_file(storage, key, **options):
    path = storage.path(key)
    if not path.is_file():
        raise ApiError("File not found.", 404)
    # conditional=True enables range requests, which video seeking needs.
    return send_file(path, conditional=True, **options)


@bp.get("/files/public/<path:key>")
def public_file(key):
    if not KEY_RE.match(key) or not key.startswith("thumbnails/"):
        raise ApiError("File not found.", 404)
    storage = current_app.extensions["storage"]
    if isinstance(storage, LocalStorage):
        response = _local_file(storage, key, max_age=86400)
    else:
        response = redirect(storage.url("", key, expires_in=3600))
        response.headers["Cache-Control"] = "public, max-age=1800"
    return response


@bp.get("/files/signed/<path:key>")
def signed_file(key):
    storage = current_app.extensions["storage"]
    download = request.args.get("download")
    if (not isinstance(storage, LocalStorage) or not KEY_RE.match(key)
            or not storage.verify(key, request.args.get("expires", ""), download,
                                  request.args.get("signature", ""))):
        raise ApiError("This link is invalid or has expired. Reload the page and try again.", 403)
    options = {"as_attachment": True, "download_name": download} if download else {}
    response = _local_file(storage, key, **options)
    response.headers["Cache-Control"] = "private, max-age=3600"
    return response
