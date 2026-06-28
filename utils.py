"""
Shared utilities: validation, CSRF, session helpers, and decorators.
"""

import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable

import bcrypt
from flask import flash, redirect, request, session, url_for
from markupsafe import escape

import config


EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.match(username.strip()))


def validate_master_password(password: str) -> tuple[bool, str]:
    if len(password) < config.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters."
    if len(password) > config.MAX_PASSWORD_LENGTH:
        return False, f"Password must not exceed {config.MAX_PASSWORD_LENGTH} characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, ""


def sanitize_input(value: str) -> str:
    """Strip whitespace and escape HTML entities."""
    if value is None:
        return ""
    return escape(value.strip())


def generate_csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf_token(token: str) -> bool:
    expected = session.get("csrf_token")
    if not expected or not token:
        return False
    return secrets.compare_digest(expected, token)


def update_session_activity() -> None:
    session["last_activity"] = datetime.now(timezone.utc).isoformat()
    session.permanent = True


def is_session_expired() -> bool:
    last = session.get("last_activity")
    if not last:
        return True
    last_activity = datetime.fromisoformat(last)
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - last_activity > config.SESSION_TIMEOUT


def login_required(view: Callable):
    """Decorator requiring authenticated, non-expired session."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if is_session_expired():
            session.clear()
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("auth.login"))
        update_session_activity()
        return view(*args, **kwargs)

    return wrapped


def get_pagination(page: int, per_page: int, total: int) -> dict:
    per_page = min(max(per_page, 1), config.MAX_PAGE_SIZE)
    total_pages = max((total + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
