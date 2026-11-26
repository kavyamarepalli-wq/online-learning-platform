"""Local development server:  python run.py"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = app.config["APP_ENV"] == "development"
    app.run(host="127.0.0.1", port=port, debug=debug)
