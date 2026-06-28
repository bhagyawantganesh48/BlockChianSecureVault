"""
SQLite and PostgreSQL database connection, schema initialization, and data access layer.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Any, List, Optional, Tuple

import config
from models import Block, User, VaultEntry, utc_now_iso

DB_URL = os.environ.get("DATABASE_URL")
if DB_URL:
    import psycopg2
    from psycopg2.extras import DictCursor


@contextmanager
def get_connection():
    if DB_URL:
        conn = psycopg2.connect(DB_URL, cursor_factory=DictCursor)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def db_execute(conn, query: str, params: tuple = ()):
    if DB_URL:
        query = query.replace("?", "%s")
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    else:
        return conn.execute(query, params)


def db_insert_returning_id(conn, query: str, params: tuple = ()) -> int:
    if DB_URL:
        query = query.replace("?", "%s")
        query = query.strip()
        if not query.endswith("RETURNING id"):
            query += " RETURNING id"
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()["id"]
    else:
        cursor = conn.execute(query, params)
        return cursor.lastrowid


def init_db() -> None:
    """Create database tables if they do not exist."""
    schema = """
        CREATE TABLE IF NOT EXISTS users (
            id {pk_type},
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            master_password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vault (
            id {pk_type},
            user_id INTEGER NOT NULL,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS blockchain (
            block_number INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            website TEXT,
            action TEXT NOT NULL,
            user_account TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            current_hash TEXT NOT NULL,
            nonce INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_vault_user_id ON vault(user_id);
        CREATE INDEX IF NOT EXISTS idx_vault_website ON vault(website);
        CREATE INDEX IF NOT EXISTS idx_blockchain_user ON blockchain(user_account);
    """
    
    if DB_URL:
        schema = schema.format(pk_type="SERIAL PRIMARY KEY")
    else:
        schema = schema.format(pk_type="INTEGER PRIMARY KEY AUTOINCREMENT")

    with get_connection() as conn:
        if DB_URL:
            cursor = conn.cursor()
            cursor.execute(schema)
        else:
            conn.executescript(schema)


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def create_user(username: str, email: str, password_hash: str) -> int:
    with get_connection() as conn:
        return db_insert_returning_id(
            conn,
            """
            INSERT INTO users (username, email, master_password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, utc_now_iso()),
        )


def get_user_by_username(username: str) -> Optional[User]:
    with get_connection() as conn:
        row = db_execute(
            conn, "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return User.from_row(row) if row else None


def get_user_by_email(email: str) -> Optional[User]:
    with get_connection() as conn:
        row = db_execute(
            conn, "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return User.from_row(row) if row else None


def get_user_by_id(user_id: int) -> Optional[User]:
    with get_connection() as conn:
        row = db_execute(
            conn, "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User.from_row(row) if row else None


# ---------------------------------------------------------------------------
# Vault operations
# ---------------------------------------------------------------------------

def create_vault_entry(
    user_id: int,
    website: str,
    username: str,
    encrypted_password: str,
    category: str,
    notes: str,
) -> int:
    now = utc_now_iso()
    with get_connection() as conn:
        return db_insert_returning_id(
            conn,
            """
            INSERT INTO vault
                (user_id, website, username, encrypted_password, category, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, website, username, encrypted_password, category, notes, now, now),
        )


def get_vault_entry(entry_id: int, user_id: int) -> Optional[VaultEntry]:
    with get_connection() as conn:
        row = db_execute(
            conn,
            "SELECT * FROM vault WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        ).fetchone()
        return VaultEntry.from_row(row) if row else None


def update_vault_entry(
    entry_id: int,
    user_id: int,
    website: str,
    username: str,
    encrypted_password: str,
    category: str,
    notes: str,
) -> bool:
    with get_connection() as conn:
        cursor = db_execute(
            conn,
            """
            UPDATE vault
            SET website = ?, username = ?, encrypted_password = ?,
                category = ?, notes = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                website,
                username,
                encrypted_password,
                category,
                notes,
                utc_now_iso(),
                entry_id,
                user_id,
            ),
        )
        return cursor.rowcount > 0


def delete_vault_entry(entry_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = db_execute(
            conn,
            "DELETE FROM vault WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        )
        return cursor.rowcount > 0


def get_vault_entries(
    user_id: int,
    search: str = "",
    category: str = "",
    sort_by: str = "updated_at",
    sort_order: str = "DESC",
    page: int = 1,
    per_page: int = 10,
) -> Tuple[List[VaultEntry], int]:
    """Return paginated vault entries and total count."""
    allowed_sort = {"website", "username", "category", "created_at", "updated_at"}
    if sort_by not in allowed_sort:
        sort_by = "updated_at"
    sort_order = "ASC" if sort_order.upper() == "ASC" else "DESC"

    conditions = ["user_id = ?"]
    params: List[Any] = [user_id]

    if search:
        conditions.append(
            "(website LIKE ? OR username LIKE ? OR category LIKE ? OR notes LIKE ?)"
        )
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if category:
        conditions.append("category = ?")
        params.append(category)

    where_clause = " AND ".join(conditions)
    offset = (max(page, 1) - 1) * per_page

    with get_connection() as conn:
        total_row = db_execute(
            conn,
            f"SELECT COUNT(*) as count FROM vault WHERE {where_clause}",
            tuple(params),
        ).fetchone()
        
        total = total_row["count"] if DB_URL else total_row[0]

        rows = db_execute(
            conn,
            f"""
            SELECT * FROM vault
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
            """,
            tuple(params + [per_page, offset]),
        ).fetchall()

    return [VaultEntry.from_row(row) for row in rows], total


def get_vault_categories(user_id: int) -> List[str]:
    with get_connection() as conn:
        rows = db_execute(
            conn,
            """
            SELECT DISTINCT category FROM vault
            WHERE user_id = ? AND category IS NOT NULL AND category != ''
            ORDER BY category
            """,
            (user_id,),
        ).fetchall()
    return [row["category"] for row in rows]


def count_vault_entries(user_id: int) -> int:
    with get_connection() as conn:
        row = db_execute(
            conn, "SELECT COUNT(*) as count FROM vault WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["count"] if DB_URL else row[0]


def get_all_vault_entries(user_id: int) -> List[VaultEntry]:
    with get_connection() as conn:
        rows = db_execute(
            conn,
            "SELECT * FROM vault WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [VaultEntry.from_row(row) for row in rows]


# ---------------------------------------------------------------------------
# Blockchain persistence
# ---------------------------------------------------------------------------

def save_block(block: Block) -> None:
    with get_connection() as conn:
        db_execute(
            conn,
            """
            INSERT INTO blockchain
                (block_number, timestamp, website, action, user_account, previous_hash, current_hash, nonce)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                block.block_number,
                block.timestamp,
                block.website,
                block.action,
                block.user,
                block.previous_hash,
                block.current_hash,
                block.nonce,
            ),
        )


def get_all_blocks(username: str = "") -> List[Block]:
    with get_connection() as conn:
        if username:
            rows = db_execute(
                conn,
                "SELECT * FROM blockchain WHERE user_account = ? ORDER BY block_number ASC",
                (username,),
            ).fetchall()
        else:
            rows = db_execute(
                conn, "SELECT * FROM blockchain ORDER BY block_number ASC"
            ).fetchall()
    return [Block.from_row(row) for row in rows]


def get_last_block() -> Optional[Block]:
    with get_connection() as conn:
        row = db_execute(
            conn, "SELECT * FROM blockchain ORDER BY block_number DESC LIMIT 1"
        ).fetchone()
        return Block.from_row(row) if row else None


def count_blocks(username: str = "") -> int:
    with get_connection() as conn:
        if username:
            row = db_execute(
                conn, "SELECT COUNT(*) as count FROM blockchain WHERE user_account = ?", (username,)
            ).fetchone()
        else:
            row = db_execute(conn, "SELECT COUNT(*) as count FROM blockchain").fetchone()
        return row["count"] if DB_URL else row[0]


def get_recent_blocks(username: str, limit: int = 5) -> List[Block]:
    with get_connection() as conn:
        rows = db_execute(
            conn,
            """
            SELECT * FROM blockchain
            WHERE user_account = ?
            ORDER BY block_number DESC
            LIMIT ?
            """,
            (username, limit),
        ).fetchall()
    return [Block.from_row(row) for row in rows]
