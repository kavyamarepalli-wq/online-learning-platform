"""Command line tools.

    python manage.py init-db
    python manage.py create-admin --email you@example.com --name "Your Name"
"""
import argparse
import getpass
import sys

from app import create_app
from app.db import connect, init_db
from app.errors import ApiError
from app.services.users import create_user
from app.validation import password_problem


def main():
    parser = argparse.ArgumentParser(description="Online Learning Platform management")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="create any missing tables")
    admin = sub.add_parser("create-admin", help="create an administrator account")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", default="Platform Admin")
    admin.add_argument("--password", help="omit to be asked securely")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.command == "init-db":
            init_db(app.config["DATABASE_URL"])
            print("Database is ready.")
            return
        password = args.password or getpass.getpass("Password: ")
        problem = password_problem(password)
        if problem:
            sys.exit(problem)
        db = connect(app.config["DATABASE_URL"])
        try:
            create_user(db, args.name, args.email.strip().lower(), password, "admin")
            db.commit()
            print(f"Administrator {args.email} created.")
        except ApiError as error:
            sys.exit(error.message)
        finally:
            db.close()


if __name__ == "__main__":
    main()
