"""
Application configuration for Blockchain-Based Secure Password Vault.

Centralizes environment settings, security parameters, and file paths.
"""

import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask configuration
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-in-production")
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

# Database
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

# Encryption key storage
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
SECRET_KEY_FILE = os.path.join(INSTANCE_DIR, "secret.key")

# Session security
SESSION_TIMEOUT = timedelta(minutes=30)
PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT

# Pagination defaults
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50

# Password policy
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Blockchain mining difficulty (leading zero bits in hash prefix)
BLOCKCHAIN_DIFFICULTY = 2
