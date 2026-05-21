"""
One-time setup: encrypts your .env file into .env.enc and saves the key to .env.key.

Usage:
    1. Create .env from .env.example and fill in your secrets
    2. Run: py setup_env.py
    3. Delete .env  (the plaintext file is no longer needed)
    4. Add .env to .gitignore so it is never committed

The program reads .env.key at runtime to decrypt .env.enc in memory.
Never commit .env or .env.key to version control.
"""
from pathlib import Path
from cryptography.fernet import Fernet

ENV_FILE = Path(".env")
ENC_FILE = Path(".env.enc")
KEY_FILE = Path(".env.key")


def main() -> None:
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found. Copy .env.example → .env and fill in your API key first.")
        return

    # Generate a new key (or reuse existing one if present)
    if KEY_FILE.exists():
        answer = input(f"{KEY_FILE} already exists. Overwrite? [y/N]: ").strip().lower()
        if answer != "y":
            print("Using existing key.")
            key = KEY_FILE.read_bytes()
        else:
            key = Fernet.generate_key()
            KEY_FILE.write_bytes(key)
            print(f"New key written to {KEY_FILE}")
    else:
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        print(f"Key written to {KEY_FILE}")

    fernet = Fernet(key)
    plaintext = ENV_FILE.read_bytes()
    encrypted = fernet.encrypt(plaintext)
    ENC_FILE.write_bytes(encrypted)
    print(f"Encrypted .env written to {ENC_FILE}")
    print()
    print("Next steps:")
    print(f"  • Delete {ENV_FILE}  (plaintext no longer needed)")
    print(f"  • Keep {KEY_FILE} secret — do NOT commit it")
    print(f"  • Commit {ENC_FILE} safely (it is ciphertext)")


if __name__ == "__main__":
    main()
