from flask import request


def page_args(default_size=12, maximum=50):
    def number(name, fallback, top):
        try:
            return min(max(int(request.args.get(name, fallback)), 1), top)
        except ValueError:
            return fallback
    page = number("page", 1, 100000)
    size = number("per_page", default_size, maximum)
    return page, size, (page - 1) * size


def paged(items, total, page, size):
    return {"items": items, "total": total, "page": page, "per_page": size,
            "pages": max((total + size - 1) // size, 1)}


def search_pattern(text):
    """A lower-case LIKE pattern in which % and _ typed by the user are literal."""
    text = text.strip().lower()[:100]
    text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{text}%"
