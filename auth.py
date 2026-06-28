"""
User authentication: registration, login, logout, and profile.
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import database
from utils import (
    generate_csrf_token,
    hash_password,
    login_required,
    sanitize_input,
    update_session_activity,
    validate_csrf_token,
    validate_email,
    validate_master_password,
    validate_username,
    verify_password,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("vault.dashboard"))

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        username = sanitize_input(request.form.get("username", ""))
        email = sanitize_input(request.form.get("email", ""))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password or not confirm:
            flash("All fields are required.", "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        if not validate_username(username):
            flash("Username must be 3-32 characters (letters, numbers, underscore).", "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        if not validate_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        valid, message = validate_master_password(password)
        if not valid:
            flash(message, "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        if database.get_user_by_username(username):
            flash("Username already exists.", "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        if database.get_user_by_email(email):
            flash("Email already registered.", "danger")
            return render_template(
                "register.html",
                csrf_token=session.get("csrf_token"),
                username=username,
                email=email,
            )

        try:
            password_hash = hash_password(password)
            user_id = database.create_user(username, email, password_hash)
            session.clear()
            session["user_id"] = user_id
            session["username"] = username
            update_session_activity()
            flash("Registration successful. Welcome to Password Vault!", "success")
            return redirect(url_for("vault.dashboard"))
        except Exception:
            flash("Registration failed. Please try again.", "danger")

    csrf_token = generate_csrf_token()
    return render_template("register.html", csrf_token=csrf_token)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("vault.dashboard"))

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token. Please try again.", "danger")
            return redirect(url_for("auth.login"))

        username = sanitize_input(request.form.get("username", ""))
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template(
                "login.html",
                csrf_token=session.get("csrf_token"),
                username=username,
            )

        user = database.get_user_by_username(username)
        if not user or not verify_password(password, user.master_password_hash):
            flash("Invalid username or password.", "danger")
            return render_template(
                "login.html",
                csrf_token=session.get("csrf_token"),
                username=username,
            )

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        update_session_activity()
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for("vault.dashboard"))

    csrf_token = generate_csrf_token()
    return render_template("login.html", csrf_token=csrf_token)


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    user = database.get_user_by_id(session["user_id"])
    csrf_token = generate_csrf_token()
    stats = {
        "passwords": database.count_vault_entries(user.id),
        "blocks": database.count_blocks(user.username),
        "member_since": user.created_at,
    }
    return render_template("profile.html", user=user, stats=stats, csrf_token=csrf_token)
