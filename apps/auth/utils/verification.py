import secrets


def generate_verification_code() -> str:
    """Generate a random 6-digit numeric verification code."""
    return f"{secrets.randbelow(1_000_000):06d}"
