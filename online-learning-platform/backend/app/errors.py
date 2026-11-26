"""One error type and JSON error responses for the whole API."""
from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, message, status=400, fields=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.fields = fields or {}


def error_response(message, status, fields=None):
    body = {"error": message}
    if fields:
        body["fields"] = fields
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return error_response(error.message, error.status, error.fields)

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        if not request.path.startswith("/api"):
            return error
        if error.code == 413:
            limit = app.config["MAX_UPLOAD_MB"]
            return error_response(f"That file is too large. The limit is {limit} MB.", 413)
        return error_response(error.description, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        app.logger.exception("Unhandled error: %s", error)
        return error_response("Something went wrong on the server. Please try again.", 500)
