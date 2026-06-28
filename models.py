"""
Data models for Users, Vault entries, and Blockchain blocks.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class User:
    """Registered vault user."""

    id: int
    username: str
    email: str
    master_password_hash: str
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            master_password_hash=row["master_password_hash"],
            created_at=row["created_at"],
        )


@dataclass
class VaultEntry:
    """Encrypted password vault entry."""

    id: int
    user_id: int
    website: str
    username: str
    encrypted_password: str
    category: str
    notes: str
    created_at: str
    updated_at: str
    plain_password: Optional[str] = None

    @classmethod
    def from_row(cls, row: Any) -> "VaultEntry":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            website=row["website"],
            username=row["username"],
            encrypted_password=row["encrypted_password"],
            category=row["category"] or "General",
            notes=row["notes"] or "",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class Block:
    """Single blockchain block for audit trail."""

    block_number: int
    timestamp: str
    website: str
    action: str
    user: str
    previous_hash: str
    current_hash: str
    nonce: int

    @classmethod
    def from_row(cls, row: Any) -> "Block":
        return cls(
            block_number=row["block_number"],
            timestamp=row["timestamp"],
            website=row["website"] or "",
            action=row["action"],
            user=row["user_account"] if "user_account" in row.keys() else row["user"],
            previous_hash=row["previous_hash"],
            current_hash=row["current_hash"],
            nonce=row["nonce"],
        )

    def to_dict(self) -> dict:
        return {
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "website": self.website,
            "action": self.action,
            "user": self.user,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "nonce": self.nonce,
        }


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
