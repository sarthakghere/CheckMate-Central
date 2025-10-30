# utils/encryption.py
import os
from cryptography.fernet import Fernet
from django.conf import settings


def get_cipher():
    key = os.getenv("BACKUP_ENCRYPTION_KEY")
    if not key:
        raise ValueError("Encryption key not found in environment variables.")
    return Fernet(key)


def encrypt_file(input_path, output_path=None):
    cipher = get_cipher()
    with open(input_path, "rb") as f:
        data = f.read()
    encrypted = cipher.encrypt(data)

    # Write encrypted data
    if not output_path:
        output_path = f"{input_path}.enc"
    with open(output_path, "wb") as f:
        f.write(encrypted)
    return output_path


def decrypt_file(input_path, output_path):
    cipher = get_cipher()
    with open(input_path, "rb") as f:
        enc_data = f.read()
    dec_data = cipher.decrypt(enc_data)
    with open(output_path, "wb") as f:
        f.write(dec_data)
