"""
Password vault CRUD, dashboard, blockchain explorer, and password generator routes.
"""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

import config
import database
from blockchain import blockchain
from encryption import EncryptionError, encryption_manager
from password_generator import generate_password
from password_strength import analyze_password
from utils import (
    generate_csrf_token,
    get_pagination,
    login_required,
    sanitize_input,
    validate_csrf_token,
)

vault_bp = Blueprint("vault", __name__)

CATEGORIES = [
    "General",
    "Social",
    "Finance",
    "Work",
    "Shopping",
    "Entertainment",
    "Development",
    "Other",
]


def _current_user_id() -> int:
    return session["user_id"]


def _current_username() -> str:
    return session["username"]


def _record_block(website: str, action: str) -> None:
    blockchain.add_block(website, action, _current_username())


@vault_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = _current_user_id()
    username = _current_username()
    entries = database.get_all_vault_entries(user_id)

    strong_count = 0
    weak_count = 0
    category_counts = {}
    strength_distribution = {"Strong": 0, "Medium": 0, "Weak": 0}

    for entry in entries:
        try:
            plain = encryption_manager.decrypt(entry.encrypted_password)
            analysis = analyze_password(plain)
            strength_distribution[analysis["label"]] += 1
            if analysis["strength"] == "strong":
                strong_count += 1
            elif analysis["strength"] == "weak":
                weak_count += 1
        except EncryptionError:
            strength_distribution["Weak"] += 1
            weak_count += 1

        cat = entry.category or "General"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    recent_activity = database.get_recent_blocks(username, limit=5)
    all_blocks = database.get_all_blocks()
    chain_valid, chain_message = blockchain.verify_chain(all_blocks)

    return render_template(
        "dashboard.html",
        total_passwords=len(entries),
        strong_count=strong_count,
        weak_count=weak_count,
        block_count=database.count_blocks(username),
        recent_activity=recent_activity,
        category_counts=category_counts,
        strength_distribution=strength_distribution,
        chain_valid=chain_valid,
        chain_message=chain_message,
        csrf_token=generate_csrf_token(),
    )


@vault_bp.route("/passwords")
@login_required
def passwords():
    user_id = _current_user_id()
    search = sanitize_input(request.args.get("search", ""))
    category = sanitize_input(request.args.get("category", ""))
    sort_by = sanitize_input(request.args.get("sort_by", "updated_at"))
    sort_order = sanitize_input(request.args.get("sort_order", "DESC"))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", config.DEFAULT_PAGE_SIZE, type=int)

    entries, total = database.get_vault_entries(
        user_id, search, category, sort_by, sort_order, page, per_page
    )
    pagination = get_pagination(page, per_page, total)
    categories = database.get_vault_categories(user_id)

    return render_template(
        "passwords.html",
        entries=entries,
        pagination=pagination,
        search=search,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        categories=categories,
        all_categories=CATEGORIES,
        csrf_token=generate_csrf_token(),
    )


@vault_bp.route("/password/add", methods=["GET", "POST"])
@login_required
def add_password():
    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token.", "danger")
            return redirect(url_for("vault.add_password"))

        website = sanitize_input(request.form.get("website", ""))
        username = sanitize_input(request.form.get("username", ""))
        password = request.form.get("password", "")
        category = sanitize_input(request.form.get("category", "General")) or "General"
        notes = sanitize_input(request.form.get("notes", ""))

        if not website or not username or not password:
            flash("Website, username, and password are required.", "danger")
            return render_template(
                "add_password.html",
                csrf_token=session.get("csrf_token"),
                website=website,
                username=username,
                category=category,
                notes=notes,
                categories=CATEGORIES,
            )

        try:
            encrypted = encryption_manager.encrypt(password)
            database.create_vault_entry(
                _current_user_id(), website, username, encrypted, category, notes
            )
            _record_block(website, "Add Password")
            flash("Password added successfully. Blockchain block created.", "success")
            return redirect(url_for("vault.passwords"))
        except EncryptionError as exc:
            flash(str(exc), "danger")
        except Exception:
            flash("Failed to save password.", "danger")

    return render_template(
        "add_password.html",
        csrf_token=generate_csrf_token(),
        categories=CATEGORIES,
    )


@vault_bp.route("/password/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_password(entry_id: int):
    entry = database.get_vault_entry(entry_id, _current_user_id())
    if not entry:
        flash("Password entry not found.", "danger")
        return redirect(url_for("vault.passwords"))

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token.", "danger")
            return redirect(url_for("vault.edit_password", entry_id=entry_id))

        website = sanitize_input(request.form.get("website", ""))
        username = sanitize_input(request.form.get("username", ""))
        password = request.form.get("password", "")
        category = sanitize_input(request.form.get("category", "General")) or "General"
        notes = sanitize_input(request.form.get("notes", ""))

        if not website or not username or not password:
            flash("Website, username, and password are required.", "danger")
            return render_template(
                "edit_password.html",
                entry=entry,
                csrf_token=session.get("csrf_token"),
                categories=CATEGORIES,
            )

        try:
            encrypted = encryption_manager.encrypt(password)
            database.update_vault_entry(
                entry_id,
                _current_user_id(),
                website,
                username,
                encrypted,
                category,
                notes,
            )
            _record_block(website, "Update Password")
            flash("Password updated successfully. Blockchain block created.", "success")
            return redirect(url_for("vault.passwords"))
        except EncryptionError as exc:
            flash(str(exc), "danger")
        except Exception:
            flash("Failed to update password.", "danger")

    try:
        entry.plain_password = encryption_manager.decrypt(entry.encrypted_password)
    except EncryptionError:
        entry.plain_password = ""
        flash("Could not decrypt stored password.", "warning")

    return render_template(
        "edit_password.html",
        entry=entry,
        csrf_token=generate_csrf_token(),
        categories=CATEGORIES,
    )


@vault_bp.route("/password/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_password(entry_id: int):
    if not validate_csrf_token(request.form.get("csrf_token", "")):
        flash("Invalid CSRF token.", "danger")
        return redirect(url_for("vault.passwords"))

    entry = database.get_vault_entry(entry_id, _current_user_id())
    if not entry:
        flash("Password entry not found.", "danger")
        return redirect(url_for("vault.passwords"))

    try:
        database.delete_vault_entry(entry_id, _current_user_id())
        _record_block(entry.website, "Delete Password")
        flash("Password deleted. Blockchain block created.", "success")
    except Exception:
        flash("Failed to delete password.", "danger")

    return redirect(url_for("vault.passwords"))


@vault_bp.route("/password/reveal/<int:entry_id>")
@login_required
def reveal_password(entry_id: int):
    entry = database.get_vault_entry(entry_id, _current_user_id())
    if not entry:
        return jsonify({"success": False, "error": "Not found"}), 404
    try:
        plain = encryption_manager.decrypt(entry.encrypted_password)
        return jsonify({"success": True, "password": plain})
    except EncryptionError as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@vault_bp.route("/blockchain")
@login_required
def blockchain_explorer():
    username = _current_username()
    all_blocks = database.get_all_blocks()
    user_blocks = database.get_all_blocks(username)
    chain_valid, chain_message = blockchain.verify_chain(all_blocks)

    block_map = {block.block_number: block for block in all_blocks}
    block_status = []
    for block in user_blocks:
        expected = blockchain.calculate_hash(
            block.block_number,
            block.timestamp,
            block.website,
            block.action,
            block.user,
            block.previous_hash,
            block.nonce,
        )
        hash_valid = block.current_hash == expected
        link_valid = True
        if block.block_number > 0:
            prev = block_map.get(block.block_number - 1)
            link_valid = prev is not None and block.previous_hash == prev.current_hash
        elif block.previous_hash != "0" * 64:
            link_valid = False
        block_status.append({"block": block, "valid": hash_valid and link_valid})

    return render_template(
        "blockchain.html",
        blocks=block_status,
        chain_valid=chain_valid,
        chain_message=chain_message,
        csrf_token=generate_csrf_token(),
    )


@vault_bp.route("/generator", methods=["GET", "POST"])
@login_required
def generator():
    result = None
    error = None

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token.", "danger")
            return redirect(url_for("vault.generator"))

        length = request.form.get("length", 16, type=int)
        use_uppercase = request.form.get("uppercase") == "on"
        use_lowercase = request.form.get("lowercase") == "on"
        use_numbers = request.form.get("numbers") == "on"
        use_symbols = request.form.get("symbols") == "on"

        try:
            result = generate_password(
                length, use_uppercase, use_lowercase, use_numbers, use_symbols
            )
            result["analysis"] = analyze_password(result["password"])
        except ValueError as exc:
            error = str(exc)

    return render_template(
        "generator.html",
        csrf_token=generate_csrf_token(),
        result=result,
        error=error,
    )


@vault_bp.route("/api/strength", methods=["POST"])
def api_strength():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    return jsonify(analyze_password(password))
