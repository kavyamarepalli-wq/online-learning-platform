from flask import current_app, request


def api_base():
    return current_app.config["PUBLIC_API_URL"] or request.host_url.rstrip("/")


def thumbnail_url(key):
    return f"{api_base()}/api/files/public/{key}" if key else None


def file_url(key, download_name=None):
    if not key:
        return None
    return current_app.extensions["storage"].url(api_base(), key, download_name=download_name)
