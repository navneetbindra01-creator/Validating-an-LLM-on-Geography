"""
Runtime secret loader — decrypts .env.enc in memory using .env.key.
Populates os.environ so the rest of the app can use os.getenv() as normal.

Falls back to a plaintext .env if .env.enc is absent (dev convenience).
"""
import os
from pathlib import Path

ENC_FILE = Path(".env.enc")
KEY_FILE = Path(".env.key")
ENV_FILE = Path(".env")


def _parse_env(text: str) -> dict[str, str]:
    """Parse KEY=VALUE lines, ignoring blanks and comments."""
    env: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        # Strip optional surrounding quotes
        value = value.strip().strip('"').strip("'")
        env[key.strip()] = value
    return env


def load() -> None:
    """Decrypt .env.enc and inject variables into os.environ."""
    if ENC_FILE.exists():
        if not KEY_FILE.exists():
            raise FileNotFoundError(
                f"{KEY_FILE} not found. Run `py setup_env.py` to generate it, "
                "or set XAI_API_KEY directly in your environment."
            )
        from cryptography.fernet import Fernet, InvalidToken

        key = KEY_FILE.read_bytes()
        try:
            fernet = Fernet(key)
            plaintext = fernet.decrypt(ENC_FILE.read_bytes()).decode("utf-8")
        except InvalidToken:
            raise ValueError(
                f"Failed to decrypt {ENC_FILE}. The key in {KEY_FILE} may not match. "
                "Re-run `py setup_env.py` to regenerate."
            )
        pairs = _parse_env(plaintext)
    elif ENV_FILE.exists():
        # Plaintext fallback for local dev without encryption
        pairs = _parse_env(ENV_FILE.read_text(encoding="utf-8"))
    else:
        # Allow env vars to be set directly in the environment (CI, containers)
        return

    for k, v in pairs.items():
        os.environ.setdefault(k, v)
