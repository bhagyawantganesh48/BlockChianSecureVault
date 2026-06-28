# 🛡️ BlockChain Secure Vault

<div align="center">

**A production-quality, blockchain-audited password manager with AES-256 encryption**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://block-chian-secure-vault.vercel.app)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-Educational-orange?style=for-the-badge)](#license)

</div>

---

## 📖 What is this?

**BlockChain Secure Vault** is a full-stack password manager that stores your credentials encrypted with **AES-256** and records every action (add, edit, delete) in a **custom-built blockchain audit trail** — so any tampering with your password history is instantly detectable.

It demonstrates how blockchain technology can be used **outside of cryptocurrency** as an immutable, tamper-evident logging system.

> **Live at:** https://block-chian-secure-vault.vercel.app

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **AES-256 Encryption** | All vault passwords encrypted via Fernet (AES-128-CBC + HMAC-SHA256) |
| ⛓️ **Blockchain Audit Trail** | Every action creates an immutable SHA-256 linked block with proof-of-work |
| 🔬 **Encryption Lab** | Real-time step-by-step visualization of the encryption process as you type |
| 🔑 **Secure Auth** | bcrypt-hashed master passwords, session timeouts, CSRF protection |
| 📊 **Dashboard** | Password strength distribution, category breakdown, recent blockchain activity |
| 🔍 **Blockchain Explorer** | Visual block-by-block chain verification with tamper detection |
| 🎲 **Password Generator** | Cryptographically secure passwords using Python's `secrets` module |
| 📈 **Strength Analyzer** | Live entropy-based analysis (Weak / Medium / Strong) |
| 🗄️ **Dual DB Support** | PostgreSQL (production/Vercel) + SQLite (local development) |
| 📱 **Responsive UI** | Dark-mode glassmorphism design, Bootstrap 5, fully mobile-friendly |

---

## ⛓️ How & Why We Use Blockchain

### The Problem with Normal Audit Logs

Traditional password managers store a log in a database table. This is **unsafe** — a database admin or attacker who gets write access can silently:
- Delete entries from the audit log
- Edit action records to hide their tracks
- Add fake entries to frame other users

**You'd never know.**

### The Blockchain Solution

Instead of a plain log table, every action creates a **cryptographically linked block**. Changing any past record breaks the entire chain — making tampering **instantly detectable**.

### What Triggers a Block?

Every time you interact with the vault, a block is mined and saved to the database:

```python
# In vault.py — called after every vault operation
_record_block(website, "Add Password")     # → new block
_record_block(website, "Update Password")  # → new block
_record_block(website, "Delete Password")  # → new block
```

### Anatomy of a Block

```python
Block = {
  "block_number"  : 7,                    # Sequential index
  "timestamp"     : "2026-06-28T05:03:48Z",  # UTC time of action
  "website"       : "github.com",          # Which vault entry
  "action"        : "Add Password",        # What happened
  "user"          : "Ganesh2548",          # Who did it
  "previous_hash" : "00a3f2b8c1...",      # ← The chain link!
  "current_hash"  : "009c41de27...",      # SHA-256 of all the above + nonce
  "nonce"         : 184                   # Proof-of-work value
}
```

### The Chain Link (Tamper Detection)

```
Genesis Block          Block 1                 Block 2                 Block 3
┌──────────────┐      ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ Action:      │      │ Action:      │        │ Action:      │        │ Action:      │
│ Genesis      │      │ Add Password │        │ Update Pass  │        │ Delete Pass  │
│ prev: 000... │─────▶│ prev: a3f2..│────────▶│ prev: b91c.. │───────▶│ prev: c40d.. │
│ hash: a3f2.. │      │ hash: b91c..│        │ hash: c40d.. │        │ hash: d7e1.. │
└──────────────┘      └──────────────┘        └──────────────┘        └──────────────┘

     ↑ Tamper Block 1?  →  Block 2's previous_hash no longer matches  →  Chain INVALID ✗
```

Each block's `current_hash` is the **SHA-256 of all its fields combined**, including the previous block's hash. If an attacker changes even a single character in Block 1, its hash changes — which means Block 2's `previous_hash` no longer matches reality. The entire chain from that point breaks.

### Proof of Work (Mining)

The app doesn't accept just any hash. It requires the hash to **start with "00"** (configurable difficulty):

```python
while not current_hash.startswith("00"):
    nonce += 1
    current_hash = sha256(block_data + nonce)
```

This means to re-forge a tampered chain, an attacker would have to **re-mine every block after the tampered one** — computationally expensive and detectable.

### Verification

The `verify_chain()` function runs on every Dashboard and Blockchain Explorer load:

```python
# blockchain.py
def verify_chain(blocks):
    for i, block in enumerate(blocks):
        # ✅ Check: block's own hash is mathematically correct
        # ✅ Check: previous_hash matches the actual previous block
        # ✅ Check: hash satisfies proof-of-work difficulty
    return True, "Blockchain verified successfully."
```

### Why Not Just a Log Table?

| Regular Database Log | Blockchain Audit Trail |
|---------------------|------------------------|
| Admin can edit/delete rows silently | Any edit breaks the hash chain — detectable |
| No way to prove records are original | Cryptographic proof of integrity |
| No computational cost to forge | Proof-of-work makes re-forging expensive |
| Requires trust in the admin | Self-verifying — trust the math, not the person |

---

## 🔐 How Encryption Works (AES-256 via Fernet)

The app uses Python's [`cryptography`](https://cryptography.io) library's **Fernet** spec, which internally uses:
- **AES-128-CBC** for encryption
- **HMAC-SHA256** for integrity/authentication
- Together forming a **256-bit security equivalent** system

### The 5-Step Encryption Process

> You can see all these steps in real-time in the built-in **Encryption Lab** (`/encryption-lab`)!

```
Step 1: Your password → UTF-8 bytes
        e.g. "MyPass1!" → 4d 79 50 61 73 73 31 21

Step 2: Random 128-bit IV generated (unique every time)
        e.g. 3a f2 9c 01 b7 44 e8 12 ...

Step 3: AES-128-CBC encrypts the padded bytes with IV + encryption key
        → raw ciphertext bytes

Step 4: HMAC-SHA256 signature computed over [version + timestamp + IV + ciphertext]
        → 32-byte authentication tag

Step 5: All parts joined and Base64-encoded → Fernet Token
        e.g. gAAAAABm...  (this is what gets stored in the DB)
```

### Fernet Token Anatomy

```
┌─────────┬────────────────┬──────────────────┬─────────────────────┬─────────────────────┐
│ Version │   Timestamp    │   IV (16 bytes)  │  Ciphertext (var.)  │  HMAC (32 bytes)    │
│  1 byte │   8 bytes      │   128 bits       │  AES-CBC output     │  SHA-256 signature  │
│  0x80   │  Unix epoch    │  random / unique │  your password      │  integrity proof    │
└─────────┴────────────────┴──────────────────┴─────────────────────┴─────────────────────┘
                           └─────────────── all Base64url encoded ────────────────────────┘
```

### Encryption Key Management

| Environment | Key Storage |
|-------------|------------|
| **Local Dev** | `instance/secret.key` (auto-generated on first run) |
| **Vercel (Production)** | `ENCRYPTION_KEY` environment variable |

The key is **32 bytes** (256 bits) — the first 16 bytes are the signing key (HMAC), the last 16 bytes are the encryption key (AES). It is **never stored in the database** or committed to source code.

---

## 🔬 Encryption Lab

A unique interactive page at `/encryption-lab` that visualizes the entire AES-256 encryption pipeline in real time:

- Type any password into the input field
- Watch the **5 encryption steps animate** one by one as the backend encrypts
- See the actual **hex bytes** for the UTF-8 encoding, IV, ciphertext, and HMAC
- View the **Fernet token anatomy** — color-coded breakdown of every component
- Track **encryption metrics**: plaintext bytes, encrypted size, expansion factor, time taken

---

## 🏗️ Architecture

```
PasswordVault/
├── app.py                  # Flask application factory + Vercel entrypoint
├── config.py               # Environment-aware configuration
├── database.py             # Dual-DB layer (PostgreSQL + SQLite fallback)
├── blockchain.py           # Custom blockchain engine (SHA-256, PoW)
├── encryption.py           # AES-256 Fernet encryption manager
├── auth.py                 # Registration, login, logout routes
├── vault.py                # Vault CRUD, Encryption Lab, API routes
├── models.py               # Block, User, VaultEntry data models
├── password_generator.py   # Secure random password generation
├── password_strength.py    # Entropy-based strength analysis
├── utils.py                # CSRF, session, validation helpers
├── vercel.json             # Vercel serverless deployment config
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/style.css       # Custom dark-mode glassmorphism styles
│   └── js/main.js          # Interactive UI logic
└── templates/
    ├── base.html           # Layout with sidebar navigation
    ├── dashboard.html      # Stats + recent blockchain activity
    ├── passwords.html      # Vault list with search/filter/pagination
    ├── add_password.html   # Add entry form
    ├── edit_password.html  # Edit entry form
    ├── blockchain.html     # Block-by-block chain explorer
    ├── encryption_lab.html # Real-time encryption visualizer
    ├── generator.html      # Password generator
    ├── profile.html        # User stats
    ├── login.html          # Authentication
    └── register.html       # Registration
```

---

## 🔒 Security Features

| Feature | Implementation |
|---------|----------------|
| CSRF Protection | Per-session token validated on every form POST |
| Session Timeout | 30-minute inactivity expiry with server-side check |
| SQL Injection | 100% parameterized queries — no string concatenation |
| XSS Protection | MarkupSafe HTML escaping on all user inputs |
| Master Password | bcrypt with random salt — only hash stored, never plaintext |
| Vault Passwords | AES-256 Fernet encrypted at rest — key never in DB |
| Audit Integrity | Blockchain with SHA-256 + proof-of-work — tamper-evident |
| Key Management | Environment variable injection for production (never in code) |

---

## 🚀 Deployment (Vercel)

This app is deployed on **Vercel** with a **PostgreSQL** database.

### Environment Variables Required

Set these in your Vercel Project → Settings → Environment Variables:

| Variable | Description |
|----------|-------------|
| `ENCRYPTION_KEY` | Fernet key — generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FLASK_SECRET_KEY` | Random secret for Flask sessions — generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `POSTGRES_URL` | Auto-injected when you link a Vercel Postgres database |

### Steps to Deploy

1. Fork/clone this repository
2. Import the repo into [Vercel](https://vercel.com/new)
3. Go to **Storage** tab → Create a **Vercel Postgres** database → Link it to your project
4. Add `ENCRYPTION_KEY` and `FLASK_SECRET_KEY` in Environment Variables
5. Vercel auto-deploys on every push to `main`

---

## 💻 Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/bhagyawantganesh48/BlockChianSecureVault.git
cd BlockChianSecureVault

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open **http://localhost:5000** in your browser.

1. Click **Register** to create your account
2. **Log in** with your master password
3. Add passwords — each addition creates a **blockchain block**
4. Explore the **Dashboard**, **Blockchain Explorer**, **Encryption Lab**, and **Generator**

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.x |
| Database | PostgreSQL (prod), SQLite (dev) |
| Encryption | `cryptography` — Fernet / AES-128-CBC + HMAC-SHA256 |
| Password Hashing | `bcrypt` |
| Blockchain | Custom SHA-256 implementation with Proof-of-Work |
| Frontend | Bootstrap 5, custom CSS (glassmorphism dark mode) |
| Deployment | Vercel (serverless Python), Vercel Postgres |
| Templates | Jinja2 |

---

## 🗺️ Roadmap

- [ ] Two-factor authentication (TOTP / Authenticator app)
- [ ] Export / import encrypted vault backup (JSON/CSV)
- [ ] Browser extension integration
- [ ] Per-user isolated blockchain chains
- [ ] Argon2id password hashing upgrade
- [ ] Rate limiting and account lockout policy
- [ ] Docker containerization
- [ ] REST API with JWT authentication
- [ ] Shared vault entries between users

---

## 📄 License

Educational / demonstration project. Built to showcase blockchain concepts applied outside of cryptocurrency — specifically as a tamper-evident audit logging system for a real-world application.

---

<div align="center">
  Built with ❤️ by <a href="https://github.com/bhagyawantganesh48">bhagyawantganesh48</a>
</div>
