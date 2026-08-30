from django.db import models
from credentials.encryption import encrypt_value, decrypt_value


class Credential(models.Model):
    CREDENTIAL_TYPES = [
        ("password", "Username & Password"),
        ("ssh_key", "SSH Key"),
        ("token", "Token"),
    ]

    name = models.CharField(max_length=255, unique=True)
    credential_type = models.CharField(max_length=20, choices=CREDENTIAL_TYPES)
    username = models.CharField(max_length=255, blank=True, default="")
    encrypted_secret = models.TextField(blank=True, default="")
    ssh_key_file = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_secret(self, plaintext: str) -> None:
        self.encrypted_secret = encrypt_value(plaintext)

    def get_secret(self) -> str:
        if not self.encrypted_secret:
            return ""
        return decrypt_value(self.encrypted_secret)

    def __str__(self) -> str:
        return f"{self.name} ({self.credential_type})"
