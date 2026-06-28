"""
Password strength analyzer using regex checks and entropy calculation.
"""

import math
import re
from typing import Dict


STRENGTH_WEAK = "weak"
STRENGTH_MEDIUM = "medium"
STRENGTH_STRONG = "strong"


def _has_uppercase(password: str) -> bool:
    return bool(re.search(r"[A-Z]", password))


def _has_lowercase(password: str) -> bool:
    return bool(re.search(r"[a-z]", password))


def _has_digits(password: str) -> bool:
    return bool(re.search(r"\d", password))


def _has_special(password: str) -> bool:
    return bool(re.search(r"[^A-Za-z0-9]", password))


def calculate_entropy(password: str) -> float:
    """Calculate Shannon entropy based on character pool size."""
    if not password:
        return 0.0

    pool_size = 0
    if _has_lowercase(password):
        pool_size += 26
    if _has_uppercase(password):
        pool_size += 26
    if _has_digits(password):
        pool_size += 10
    if _has_special(password):
        pool_size += 32

    if pool_size == 0:
        return 0.0

    return len(password) * math.log2(pool_size)


def analyze_password(password: str) -> Dict:
    """
    Evaluate password strength.

    Returns dict with checks, entropy, score, label, and bootstrap color class.
    """
    length = len(password)
    checks = {
        "length": length >= 8,
        "uppercase": _has_uppercase(password),
        "lowercase": _has_lowercase(password),
        "digits": _has_digits(password),
        "special": _has_special(password),
    }
    entropy = round(calculate_entropy(password), 2)
    passed = sum(checks.values())

    if length == 0:
        strength = STRENGTH_WEAK
    elif length >= 12 and passed >= 4 and entropy >= 60:
        strength = STRENGTH_STRONG
    elif length >= 8 and passed >= 3 and entropy >= 40:
        strength = STRENGTH_MEDIUM
    else:
        strength = STRENGTH_WEAK

    labels = {
        STRENGTH_WEAK: "Weak",
        STRENGTH_MEDIUM: "Medium",
        STRENGTH_STRONG: "Strong",
    }
    colors = {
        STRENGTH_WEAK: "danger",
        STRENGTH_MEDIUM: "warning",
        STRENGTH_STRONG: "success",
    }

    return {
        "length": length,
        "checks": checks,
        "entropy": entropy,
        "strength": strength,
        "label": labels[strength],
        "color": colors[strength],
        "score": passed,
    }


def is_strong_password(password: str) -> bool:
    """Return True if password meets strong criteria."""
    return analyze_password(password)["strength"] == STRENGTH_STRONG
