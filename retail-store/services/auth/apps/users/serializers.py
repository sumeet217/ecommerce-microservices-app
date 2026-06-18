"""
Auth Service — User Serializers

Covers: registration, login (JWT), token refresh, token verify,
token blacklist (logout), user profile read, and profile update.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ─── User Profile ─────────────────────────────────────────────────────────────


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only serializer for user profile data."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "is_active", "date_joined", "last_login"]

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()


# ─── Registration ─────────────────────────────────────────────────────────────


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new user.
    Returns user data plus fresh JWT tokens.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    # Tokens returned on success (write-only on the DB side — computed)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "is_active",
            "date_joined",
            "access_token",
            "refresh_token",
        ]
        read_only_fields = ["id", "is_active", "date_joined"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def validate_email(self, value: str) -> str:
        """Ensure email is unique (case-insensitive)."""
        normalised = value.lower().strip()
        if User.objects.filter(email__iexact=normalised).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )
        return normalised

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        """Augment the response with JWT tokens."""
        data = super().to_representation(instance)
        refresh = RefreshToken.for_user(instance)
        data["access_token"] = str(refresh.access_token)
        data["refresh_token"] = str(refresh)
        return data


# ─── Login ────────────────────────────────────────────────────────────────────


class LoginSerializer(TokenObtainPairSerializer):
    """
    Custom TokenObtainPairSerializer that uses 'email' as the username field
    and returns access_token / refresh_token with consistent naming.
    """

    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        # Normalise email before calling parent validation
        attrs[self.username_field] = attrs.get(self.username_field, "").lower().strip()
        data = super().validate(attrs)

        # Rename keys to match our API contract
        data["access_token"] = data.pop("access")
        data["refresh_token"] = data.pop("refresh")
        return data


# ─── Token Refresh ────────────────────────────────────────────────────────────


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Response shape for POST /api/v1/auth/refresh/."""

    access_token = serializers.CharField()


# ─── Token Verify ─────────────────────────────────────────────────────────────


class TokenVerifyResponseSerializer(serializers.Serializer):
    """Response shape for POST /api/v1/auth/verify/."""

    detail = serializers.CharField(default="Token is valid.")


# ─── Logout ───────────────────────────────────────────────────────────────────


class LogoutSerializer(serializers.Serializer):
    """Input for POST /api/v1/auth/logout/ — expects refresh_token."""

    refresh_token = serializers.CharField(required=True)


# ─── Profile Update ───────────────────────────────────────────────────────────


class UpdateProfileSerializer(serializers.ModelSerializer):
    """PATCH /api/v1/auth/me/ — allows updating name and email."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def validate_email(self, value: str) -> str:
        """Ensure the new email is not taken by another user."""
        normalised = value.lower().strip()
        request_user = self.context["request"].user
        qs = User.objects.filter(email__iexact=normalised).exclude(pk=request_user.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )
        return normalised
