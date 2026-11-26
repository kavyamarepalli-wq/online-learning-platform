"""Validates uploaded files (extension, size and file signature) before storing them."""
import os
import uuid

from flask import current_app, g, request

from .errors import ApiError

OFFICE = "application/vnd.openxmlformats-officedocument."

RULES = {
    "thumbnail": {
        "folder": "thumbnails", "max_mb": 5,
        "types": {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"},
    },
    "video": {
        "folder": "videos", "max_mb": None,  # limited by MAX_UPLOAD_MB
        "types": {"mp4": "video/mp4", "webm": "video/webm"},
    },
    "material": {
        "folder": "materials", "max_mb": 25,
        "types": {
            "pdf": "application/pdf", "zip": "application/zip", "txt": "text/plain",
            "md": "text/markdown", "csv": "text/csv", "png": "image/png",
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "docx": OFFICE + "wordprocessingml.document",
            "pptx": OFFICE + "presentationml.presentation",
            "xlsx": OFFICE + "spreadsheetml.sheet",
        },
    },
}


def _signature_ok(extension, head):
    if extension == "png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in ("jpg", "jpeg"):
        return head.startswith(b"\xff\xd8\xff")
    if extension == "webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if extension == "pdf":
        return head.startswith(b"%PDF-")
    if extension in ("zip", "docx", "pptx", "xlsx"):
        return head.startswith(b"PK")
    if extension == "mp4":
        return head[4:8] == b"ftyp"
    if extension == "webm":
        return head.startswith(b"\x1a\x45\xdf\xa3")
    return b"\x00" not in head  # plain text formats


def save_upload(kind, field="file", required=True):
    """Stores the file sent in `field`. Returns its details, or None if optional and absent."""
    upload = request.files.get(field)
    if not upload or not upload.filename:
        if required:
            raise ApiError("Please choose a file.", 422, {field: "Please choose a file."})
        return None

    rule = RULES[kind]
    name = os.path.basename(upload.filename.replace("\\", "/")).replace("\x00", "")
    name = "".join(ch for ch in name if ch.isprintable())
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if extension not in rule["types"]:
        allowed = ", ".join(sorted(rule["types"]))
        message = f"Unsupported file type. Allowed: {allowed}."
        raise ApiError(message, 422, {field: message})

    stream = upload.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    limit_mb = min(rule["max_mb"] or 10**6, current_app.config["MAX_UPLOAD_MB"])
    if size == 0 or size > limit_mb * 1024 * 1024:
        message = "The file is empty." if size == 0 else f"The file must be {limit_mb} MB or smaller."
        raise ApiError(message, 422, {field: message})
    head = stream.read(4096)
    stream.seek(0)
    if not _signature_ok(extension, head):
        message = f"The file content does not look like a .{extension} file."
        raise ApiError(message, 422, {field: message})

    if len(name) > 150:
        name = name[: 149 - len(extension)] + "." + extension
    key = f"{rule['folder']}/{uuid.uuid4().hex}.{extension}"
    content_type = rule["types"][extension]
    current_app.extensions["storage"].save(
        stream, key, content_type, download_name=name if kind == "material" else None)
    g.setdefault("delete_on_failure", []).append(key)
    return {"key": key, "name": name, "content_type": content_type, "size": size}


def delete_later(*keys):
    """Removes stored files after the current request's changes are committed."""
    g.setdefault("delete_on_success", []).extend(k for k in keys if k)
