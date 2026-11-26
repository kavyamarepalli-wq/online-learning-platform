"""In-memory sliding-window rate limiting for sign-in and sign-up.

Counts are kept per server process, which is enough for a single small instance.
Use a shared store such as Redis if you run several instances.
"""
import threading
import time
from collections import defaultdict, deque

from flask import current_app, request

from .errors import ApiError

_hits = defaultdict(deque)
_lock = threading.Lock()


def limit(bucket, maximum, window_seconds, identity=""):
    if not current_app.config["RATE_LIMITS"]:
        return
    key = (bucket, request.remote_addr or "?", identity)
    current = time.monotonic()
    with _lock:
        if len(_hits) > 10000:
            _hits.clear()
        hits = _hits[key]
        while hits and current - hits[0] > window_seconds:
            hits.popleft()
        if len(hits) >= maximum:
            raise ApiError("Too many attempts. Please wait a few minutes and try again.", 429)
        hits.append(current)


def reset():
    with _lock:
        _hits.clear()
