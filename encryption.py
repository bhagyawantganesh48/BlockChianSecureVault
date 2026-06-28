"""
AES-256 encryption and decryption using Fernet (cryptography library).
"""

import os

from cryptography.fernet import Fernet, InvalidToken

import config


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class EncryptionManager:
    """Manages AES-256 encryption key lifecycle and cipher operations."""

    def __init__(self, key_file: str = config.SECRET_KEY_FILE):
        self.key_file = key_file
        self._fernet: Fernet | None = None

    def _ensure_instance_dir(self) -> None:
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)

    def load_or_create_key(self) -> bytes:
        """Load existing key or generate a new Fernet key."""
        env_key = os.environ.get("ENCRYPTION_KEY")
        if env_key:
            return env_key.encode("utf-8")

        self._ensure_instance_dir()
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as handle:
                key = handle.read()
            if not key:
                raise EncryptionError("Encryption key file is empty.")
            return key

        key = Fernet.generate_key()
        with open(self.key_file, "wb") as handle:
            handle.write(key)
        return key

    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            key = self.load_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext password and return URL-safe base64 ciphertext."""
        if plaintext is None:
            raise EncryptionError("Cannot encrypt empty value.")
        token = self.fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext and return original plaintext password."""
        try:
            plaintext = self.fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as exc:
            raise EncryptionError("Invalid encryption key or corrupted data.") from exc


# Singleton used across the application
encryption_manager = EncryptionManager()
