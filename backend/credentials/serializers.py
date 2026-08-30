from rest_framework import serializers
from credentials.models import Credential


class CredentialSerializer(serializers.ModelSerializer):
    secret = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Credential
        fields = ["id", "name", "credential_type", "username", "ssh_key_file", "secret", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        secret = validated_data.pop("secret", "")
        credential = Credential.objects.create(**validated_data)
        if secret:
            credential.set_secret(secret)
            credential.save()
        return credential

    def update(self, instance, validated_data):
        secret = validated_data.pop("secret", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if secret:
            instance.set_secret(secret)
        instance.save()
        return instance
