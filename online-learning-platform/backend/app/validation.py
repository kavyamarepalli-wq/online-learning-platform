"""Small, explicit input validation with per-field error messages."""
import re

from flask import request

from .errors import ApiError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("The request body must be a JSON object.")
    return data


def password_problem(password):
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if len(password) > 128:
        return "Password must be at most 128 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain at least one letter and one number."
    return None


class Validator:
    def __init__(self, data):
        self.data = data
        self.errors = {}

    def _raw(self, name):
        value = self.data.get(name)
        return "" if value is None else value

    def string(self, name, label, minimum=1, maximum=200):
        value = self._raw(name)
        if not isinstance(value, str):
            self.errors[name] = f"{label} must be text."
            return ""
        value = value.strip().replace("\x00", "")
        if minimum and not value:
            self.errors[name] = f"{label} is required."
        elif len(value) < minimum:
            self.errors[name] = f"{label} must be at least {minimum} characters."
        elif len(value) > maximum:
            self.errors[name] = f"{label} must be at most {maximum} characters."
        return value

    def email(self, name="email"):
        value = self.string(name, "Email", 1, 254).lower()
        if name not in self.errors and not EMAIL_RE.match(value):
            self.errors[name] = "Enter a valid email address."
        return value

    def password(self, name="password"):
        value = self._raw(name)
        if not isinstance(value, str) or not value:
            self.errors[name] = "Password is required."
            return ""
        problem = password_problem(value)
        if problem:
            self.errors[name] = problem
        return value

    def integer(self, name, label, minimum, maximum, default=None):
        value = self.data.get(name)
        if value in (None, "") and default is not None:
            return default
        try:
            if isinstance(value, bool) or (isinstance(value, float) and not value.is_integer()):
                raise ValueError
            value = int(value)
        except (TypeError, ValueError, OverflowError):
            self.errors[name] = f"{label} must be a whole number."
            return minimum
        if not minimum <= value <= maximum:
            self.errors[name] = f"{label} must be between {minimum} and {maximum}."
        return value

    def choice(self, name, label, options, default=None):
        value = self.data.get(name) or default
        if value not in options:
            self.errors[name] = f"Choose a valid {label.lower()}."
        return value

    def boolean(self, name, default=False):
        value = self.data.get(name, default)
        if not isinstance(value, bool):
            self.errors[name] = "Must be true or false."
        return bool(value)

    def check(self):
        if self.errors:
            raise ApiError("Please fix the highlighted fields.", 422, self.errors)
