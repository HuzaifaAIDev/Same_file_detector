"""Shared validation helpers for user-supplied input."""
import re
import string

SPECIAL_CHARS = string.punctuation


def password_requirements(password: str) -> dict[str, bool]:
    """Returns which password rules are satisfied — mirrors the live
    checklist shown on the frontend so validation logic isn't duplicated
    in two different shapes."""
    return {
        "min_length": len(password) >= 8,
        "uppercase": any(c.isupper() for c in password),
        "lowercase": any(c.islower() for c in password),
        "number": any(c.isdigit() for c in password),
        "special": any(c in SPECIAL_CHARS for c in password),
    }


def validate_password_strength(password: str) -> None:
    """Raises ValueError with the first unmet requirement's message."""
    checks = password_requirements(password)
    messages = {
        "min_length": "Password must be at least 8 characters long.",
        "uppercase": "Password must contain at least one uppercase letter.",
        "lowercase": "Password must contain at least one lowercase letter.",
        "number": "Password must contain at least one number.",
        "special": "Password must contain at least one special character.",
    }
    for key, ok in checks.items():
        if not ok:
            raise ValueError(messages[key])


USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{3,50}$")


def validate_username(username: str) -> None:
    if not USERNAME_RE.match(username):
        raise ValueError(
            "Username must be 3-50 characters and may only contain letters, "
            "numbers, dots and underscores."
        )
