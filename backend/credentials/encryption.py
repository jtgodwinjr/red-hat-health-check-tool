from cryptography.fernet import Fernet
from django.conf import settings

_fernet_instance = None


def get_or_create_fernet_key() -> bytes:
    key_path = settings.FERNET_KEY_PATH
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    key_path.chmod(0o600)  # Owner read/write only
    return key


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = get_or_create_fernet_key()
        _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
