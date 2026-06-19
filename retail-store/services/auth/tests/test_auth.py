"""
Auth Service — Test Suite

Tests cover:
- User registration (happy path, duplicate email, password mismatch, weak password)
- Login (valid, invalid credentials, inactive user)
- Token refresh (valid token, invalid token)
- Token blacklisting on logout
- Protected endpoint access (with/without token)
- Profile retrieval and update
- Token verification endpoint
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import InactiveUserFactory, UserFactory

# ─── URL constants ─────────────────────────────────────────────────────────────
REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/auth/me/"
VERIFY_URL = "/api/v1/auth/verify/"
HEALTH_URL = "/health/"


# =============================================================================
# Health Check
# =============================================================================


@pytest.mark.django_db
class TestHealthCheck:
    """Liveness probe — no auth required."""

    def test_health_returns_ok(self, api_client):
        response = api_client.get(HEALTH_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        assert response.data["service"] == "auth-service"


# =============================================================================
# Registration
# =============================================================================


@pytest.mark.django_db
class TestRegistration:
    """POST /api/v1/auth/register/"""

    def test_register_success(self, api_client, user_data):
        """Valid registration returns 201 with user data and JWT tokens."""
        response = api_client.post(REGISTER_URL, user_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert "access_token" in data
        assert "refresh_token" in data
        # Password must NOT appear in the response
        assert "password" not in data

    def test_register_duplicate_email(self, api_client, user_data, db):
        """Registering with an existing email returns 400."""
        # First registration
        api_client.post(REGISTER_URL, user_data, format="json")
        # Duplicate
        response = api_client.post(REGISTER_URL, user_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_duplicate_email_case_insensitive(self, api_client, user_data, db):
        """Email uniqueness check is case-insensitive."""
        api_client.post(REGISTER_URL, user_data, format="json")

        upper_data = {**user_data, "email": user_data["email"].upper()}
        response = api_client.post(REGISTER_URL, upper_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client, user_data):
        """Mismatched passwords return a validation error."""
        user_data["password_confirm"] = "DifferentPassword!"
        response = api_client.post(REGISTER_URL, user_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_register_missing_email(self, api_client, user_data):
        """Registration without email returns 400."""
        user_data.pop("email")
        response = api_client.post(REGISTER_URL, user_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_invalid_email_format(self, api_client, user_data):
        """Invalid email format is rejected."""
        user_data["email"] = "not-an-email"
        response = api_client.post(REGISTER_URL, user_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client, user_data):
        """Common/weak password is rejected by Django's validators."""
        user_data["password"] = "password"
        user_data["password_confirm"] = "password"
        response = api_client.post(REGISTER_URL, user_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_required_fields(self, api_client):
        """Registration with no body returns 400."""
        response = api_client.post(REGISTER_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Login
# =============================================================================


@pytest.mark.django_db
class TestLogin:
    """POST /api/v1/auth/login/"""

    def test_login_success(self, api_client, registered_user):
        """Valid credentials return access_token and refresh_token."""
        response = api_client.post(
            LOGIN_URL,
            {"email": registered_user.email, "password": "StrongPass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_login_invalid_password(self, api_client, registered_user):
        """Wrong password returns 401."""
        response = api_client.post(
            LOGIN_URL,
            {"email": registered_user.email, "password": "WrongPassword!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        """Login with unknown email returns 401."""
        response = api_client.post(
            LOGIN_URL,
            {"email": "ghost@example.com", "password": "AnyPassword123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, api_client, db):
        """Inactive users cannot log in — returns 401."""
        user = InactiveUserFactory()
        response = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": "StrongPass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields(self, api_client):
        """Login with empty body returns 400."""
        response = api_client.post(LOGIN_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_email_case_insensitive(self, api_client, registered_user):
        """Email matching is case-insensitive on login."""
        response = api_client.post(
            LOGIN_URL,
            {
                "email": registered_user.email.upper(),
                "password": "StrongPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Token Refresh
# =============================================================================


@pytest.mark.django_db
class TestTokenRefresh:
    """POST /api/v1/auth/refresh/"""

    def test_refresh_returns_new_access_token(self, api_client, registered_user):
        """Valid refresh token produces a new access token."""
        refresh = RefreshToken.for_user(registered_user)
        response = api_client.post(
            REFRESH_URL,
            {"refresh": str(refresh)},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data

    def test_refresh_invalid_token(self, api_client):
        """Invalid refresh token returns 401."""
        response = api_client.post(
            REFRESH_URL,
            {"refresh": "this-is-not-a-valid-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_missing_token(self, api_client):
        """Missing refresh token returns 400."""
        response = api_client.post(REFRESH_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Logout / Token Blacklisting
# =============================================================================


@pytest.mark.django_db
class TestLogout:
    """POST /api/v1/auth/logout/"""

    def test_logout_success(self, api_client, auth_client):
        """Authenticated user can blacklist their refresh token."""
        client, user = auth_client
        refresh = RefreshToken.for_user(user)

        response = client.post(
            LOGOUT_URL,
            {"refresh_token": str(refresh)},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_blacklisted_token_cannot_be_refreshed(self, api_client, auth_client):
        """After logout, the same refresh token cannot obtain new access tokens."""
        client, user = auth_client
        refresh = RefreshToken.for_user(user)
        refresh_str = str(refresh)

        # Logout
        client.post(LOGOUT_URL, {"refresh_token": refresh_str}, format="json")

        # Attempt to refresh — should fail
        response = api_client.post(
            REFRESH_URL, {"refresh": refresh_str}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_requires_authentication(self, api_client, registered_user):
        """Unauthenticated logout attempt returns 401."""
        refresh = RefreshToken.for_user(registered_user)
        response = api_client.post(
            LOGOUT_URL,
            {"refresh_token": str(refresh)},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_invalid_token(self, auth_client):
        """Providing an invalid refresh token returns 400."""
        client, _ = auth_client
        response = client.post(
            LOGOUT_URL,
            {"refresh_token": "not-a-valid-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_missing_token(self, auth_client):
        """Missing refresh_token field returns 400."""
        client, _ = auth_client
        response = client.post(LOGOUT_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Current User Profile (GET /me/)
# =============================================================================


@pytest.mark.django_db
class TestGetCurrentUser:
    """GET /api/v1/auth/me/"""

    def test_get_me_authenticated(self, auth_client):
        """Authenticated user can retrieve their profile."""
        client, user = auth_client
        response = client.get(ME_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert "id" in response.data
        assert "date_joined" in response.data
        # Sensitive fields must not be present
        assert "password" not in response.data

    def test_get_me_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get(ME_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_invalid_token(self, api_client):
        """Invalid/expired token returns 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = api_client.get(ME_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Profile Update (PATCH /me/)
# =============================================================================


@pytest.mark.django_db
class TestUpdateProfile:
    """PATCH /api/v1/auth/me/"""

    def test_update_first_name(self, auth_client):
        """Authenticated user can update their first name."""
        client, user = auth_client
        response = client.patch(
            ME_URL, {"first_name": "UpdatedName"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "UpdatedName"

    def test_update_email(self, auth_client):
        """Authenticated user can update to a new unique email."""
        client, user = auth_client
        response = client.patch(
            ME_URL, {"email": "new-unique@example.com"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "new-unique@example.com"

    def test_update_email_to_existing_email(self, auth_client, db):
        """Cannot update email to one already used by another user."""
        client, user = auth_client
        other = UserFactory(email="taken@example.com")

        response = client.patch(
            ME_URL, {"email": "taken@example.com"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_same_email_allowed(self, auth_client):
        """User can 'update' to their own email without error."""
        client, user = auth_client
        response = client.patch(
            ME_URL, {"email": user.email}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_update_profile_unauthenticated(self, api_client):
        """Unauthenticated PATCH returns 401."""
        response = api_client.patch(
            ME_URL, {"first_name": "Hacker"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Token Verification
# =============================================================================


@pytest.mark.django_db
class TestTokenVerify:
    """POST /api/v1/auth/verify/"""

    def test_verify_valid_access_token(self, api_client, registered_user):
        """Valid access token returns 200."""
        refresh = RefreshToken.for_user(registered_user)
        access = str(refresh.access_token)

        response = api_client.post(VERIFY_URL, {"token": access}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Token is valid."

    def test_verify_invalid_token(self, api_client):
        """Invalid token returns 401."""
        response = api_client.post(
            VERIFY_URL, {"token": "completely-invalid-token"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_missing_token(self, api_client):
        """Missing token field returns 400."""
        response = api_client.post(VERIFY_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_no_auth_required(self, api_client, registered_user):
        """Token verification is publicly accessible (no auth header needed)."""
        refresh = RefreshToken.for_user(registered_user)
        access = str(refresh.access_token)

        # No credentials set on client
        response = api_client.post(VERIFY_URL, {"token": access}, format="json")

        assert response.status_code == status.HTTP_200_OK
