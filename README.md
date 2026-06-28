# Blockchain-Based Secure Password Vault

A production-quality password manager that combines **AES-256 encryption** for credential storage with a **custom blockchain** audit trail. Every add, update, and delete operation is immutably recorded — demonstrating blockchain concepts without cryptocurrency.

![Screenshots Placeholder](static/images/.gitkeep)

> Replace the placeholder above with screenshots of the Dashboard, Vault, and Blockchain Explorer.

---

## Features

- **User Authentication** — Registration, login, logout with bcrypt-hashed master passwords
- **AES-256 Encryption** — Vault passwords encrypted via Fernet (`cryptography` library)
- **Custom Blockchain** — SHA-256 linked blocks with proof-of-work for audit logging
- **Password Vault CRUD** — Search, filter, sort, pagination, reveal & copy
- **Dashboard** — Stats, category chart, strength distribution, recent activity
- **Blockchain Explorer** — Visual block cards with per-block and chain verification
- **Password Generator** — Cryptographically secure random passwords (`secrets` module)
- **Strength Analyzer** — Live regex + entropy analysis (Weak / Medium / Strong)
- **Modern UI** — Dark mode, glassmorphism, Bootstrap 5, responsive sidebar

---

## Security Features

| Feature | Implementation |
|---------|----------------|
| CSRF Protection | Session-based tokens on all forms |
| Session Timeout | 30-minute inactivity expiry |
| SQL Injection | Parameterized SQLite queries |
| XSS Protection | MarkupSafe HTML escaping |
| Master Password | bcrypt hash only — never stored plaintext |
| Vault Passwords | AES-256 Fernet encryption at rest |

---

## Requirements

- Python 3.11+
- pip

---

## Installation

```bash
cd PasswordVault
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## How to Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

1. **Register** a new account
2. **Login** with your credentials
3. **Add passwords** — each action creates a blockchain block
4. Explore the **Dashboard**, **Blockchain Explorer**, and **Generator**

---

## Folder Structure

```
PasswordVault/
├── app.py                  # Flask application factory
├── config.py               # Configuration settings
├── database.py             # SQLite schema & queries
├── blockchain.py           # Custom blockchain engine
├── encryption.py           # AES-256 Fernet encryption
├── auth.py                 # Authentication routes
├── vault.py                # Vault CRUD & feature routes
├── password_generator.py   # Secure password generation
├── password_strength.py    # Strength & entropy analysis
├── models.py               # Data models
├── utils.py                # Helpers & security utilities
├── requirements.txt
├── database.db             # Created at runtime
├── static/                 # CSS, JS, images
├── templates/              # Jinja2 HTML templates
├── instance/secret.key     # AES key (auto-generated)
└── tests/                  # Unit tests
```

---

## How Blockchain Works

```
Genesis Block (Block 0)
        │
        ▼
Block 1 — Action: Add Password
        │
        ▼
Block 2 — Action: Update Password
        │
        ▼
Block 3 — Action: Delete Password
```

Each block contains:

- **Block Number** — Sequential index
- **Timestamp** — UTC operation time
- **Website** — Affected vault entry
- **Action** — Add / Update / Delete
- **Previous Hash** — Link to prior block
- **Current Hash** — SHA-256 of block data + nonce
- **Nonce** — Proof-of-work value

If any block is tampered with, `verify_chain()` fails and the explorer shows a **broken chain** status.

---

## How AES Works

```
Plaintext Password  →  Fernet.encrypt()  →  Ciphertext  →  SQLite
Ciphertext          →  Fernet.decrypt()  →  Plaintext   →  Display
```

The encryption key is stored in `instance/secret.key` and generated automatically on first run.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Or:

```bash
python -m unittest discover -s tests -v
```

---

## Future Enhancements

- Two-factor authentication (TOTP)
- Export / import encrypted vault backup
- Browser extension integration
- Per-user isolated blockchain chains
- Argon2 password hashing
- Rate limiting and account lockout
- Docker containerization
- REST API with JWT authentication

---

## License

Educational / demonstration project. Use at your own discretion for non-production environments.
