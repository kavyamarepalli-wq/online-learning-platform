from ..db import now


def log(db, user_id, action, details=""):
    db.execute("INSERT INTO activity_logs (user_id, action, details, created_at) VALUES (?, ?, ?, ?)",
               (user_id, action, details[:500], now()))
