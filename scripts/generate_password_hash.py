"""
Run this once to generate a password hash for your demo user, then paste
the output into your .env as DEMO_PASSWORD_HASH.

Usage:
    python scripts/generate_password_hash.py
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if __name__ == "__main__":
    password = input("Enter the password to hash: ")
    hashed = pwd_context.hash(password)
    print("\nAdd this line to your .env:")
    print(f"DEMO_PASSWORD_HASH={hashed}")
