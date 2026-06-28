"""
Blockchain-Based Secure Password Vault — Flask Application Entry Point.
"""

import os

from flask import Flask, redirect, session, url_for
from markupsafe import Markup

import config
import database
from auth import auth_bp
from encryption import encryption_manager
from vault import vault_bp


def create_app():
    """Application factory for the Password Vault."""
    app = Flask(__name__)
    app.config.from_object(config)
    app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME

    try:
        os.makedirs(config.INSTANCE_DIR, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create instance directory. {e}")

    try:
        database.init_db()
    except Exception as e:
        print(f"Warning: Database initialization skipped or failed. {e}")

    try:
        encryption_manager.load_or_create_key()
    except Exception as e:
        print(f"Warning: Encryption key load/create failed. {e}")

    app.register_blueprint(auth_bp)
    app.register_blueprint(vault_bp)

    @app.context_processor
    def inject_globals():
        return {
            "current_user": session.get("username"),
        }

    @app.template_filter("nl2br")
    def nl2br(value):
        if not value:
            return ""
        escaped = Markup.escape(str(value))
        return Markup(escaped.replace("\n", Markup("<br>")))

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("vault.dashboard"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def not_found(_error):
        return redirect(url_for("index"))

    @app.errorhandler(500)
    def server_error(_error):
        return (
            "<h1>Internal Server Error</h1><p>Please try again later.</p>",
            500,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
