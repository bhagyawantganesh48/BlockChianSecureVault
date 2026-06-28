"""
Secure random password generator using Python secrets module.
"""

import secrets
import string
from typing import Dict


def generate_password(
    length: int = 16,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_numbers: bool = True,
    use_symbols: bool = True,
) -> Dict:
    """
    Generate a cryptographically secure random password.

    Ensures at least one character from each selected charset is included.
    """
    if length < 4 or length > 128:
        raise ValueError("Password length must be between 4 and 128.")

    charsets = []
    required_chars = []

    if use_lowercase:
        charsets.append(string.ascii_lowercase)
        required_chars.append(secrets.choice(string.ascii_lowercase))
    if use_uppercase:
        charsets.append(string.ascii_uppercase)
        required_chars.append(secrets.choice(string.ascii_uppercase))
    if use_numbers:
        charsets.append(string.digits)
        required_chars.append(secrets.choice(string.digits))
    if use_symbols:
        symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        charsets.append(symbols)
        required_chars.append(secrets.choice(symbols))

    if not charsets:
        raise ValueError("At least one character type must be selected.")

    if length < len(required_chars):
        raise ValueError("Length is too short for selected character types.")

    pool = "".join(charsets)
    remaining = length - len(required_chars)
    password_chars = required_chars + [secrets.choice(pool) for _ in range(remaining)]
    secrets.SystemRandom().shuffle(password_chars)
    password = "".join(password_chars)

    return {
        "password": password,
        "length": length,
        "options": {
            "uppercase": use_uppercase,
            "lowercase": use_lowercase,
            "numbers": use_numbers,
            "symbols": use_symbols,
        },
    }
