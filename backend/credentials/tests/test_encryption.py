from credentials.encryption import encrypt_value, decrypt_value, get_or_create_fernet_key


def test_encrypt_decrypt_roundtrip():
    plaintext = "my-secret-password"
    ciphertext = encrypt_value(plaintext)
    assert ciphertext != plaintext
    assert decrypt_value(ciphertext) == plaintext


def test_encrypt_produces_different_ciphertext_each_call():
    plaintext = "same-value"
    c1 = encrypt_value(plaintext)
    c2 = encrypt_value(plaintext)
    assert c1 != c2  # Fernet uses random IV


def test_fernet_key_persists(tmp_path, settings):
    settings.FERNET_KEY_PATH = tmp_path / "test_fernet.key"
    key1 = get_or_create_fernet_key()
    key2 = get_or_create_fernet_key()
    assert key1 == key2
