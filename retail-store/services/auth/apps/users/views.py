"""
Auth Service — Users App Views

Endpoints
---------
POST   /api/v1/auth/register/  — create account + return tokens
POST   /api/v1/auth/login/     — obtain JWT tokens (rate-limited)
POST   /api/v1/auth/refresh/   — exchange refresh for new access token
POST   /api/v1/auth/logout/    — blacklist the refresh token
GET    /api/v1/auth/me/        — return current user profile
PATCH  /api/v1/auth/me/        — update first_name / last_name / email
POST   /api/v1/auth/verify/    — verify a JWT (for other services)
"""

import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    TokenRefreshResponseSerializer,
    TokenVerifyResponseSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
)

logger = logging.getLogger(__name__)


# ─── Registration ─────────────────────────────────────────────────────────────


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/

    Create a new user account and return JWT tokens immediately.
    No authentication required.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        summary="Register a new user",
        description="Creates a new user account and returns access + refresh tokens.",
        tags=["Auth"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("New user registered: %s", user.email)
        return Response(
            RegisterSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


# ─── Login ────────────────────────────────────────────────────────────────────


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Authenticate with email + password and receive JWT tokens.
    Rate-limited to 10 requests/minute per anonymous client.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="JWT token pair"),
            401: OpenApiResponse(description="Invalid credentials"),
        },
        summary="Login — obtain JWT tokens",
        description="Authenticate with email and password. Returns access_token and refresh_token.",
        tags=["Auth"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logger.info(
            "User logged in: %s",
            request.data.get("email", "<unknown>"),
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ─── Token Refresh ────────────────────────────────────────────────────────────


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh/

    Exchange a valid refresh token for a new access token.
    Accepts { "refresh": "<token>" } — standard simplejwt format.
    Returns { "access_token": "<new-access>" }.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: TokenRefreshResponseSerializer},
        summary="Refresh access token",
        description=(
            "Exchange a valid refresh token for a new access token. "
            "Send { \"refresh\": \"<refresh_token>\" }."
        ),
        tags=["Auth"],
    )
    def post(self, request, *args, **kwargs):
        # simplejwt expects the key "refresh" in the body
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Rename "access" → "access_token" for API consistency
            response.data["access_token"] = response.data.pop("access", None)
        return response


# ─── Logout ───────────────────────────────────────────────────────────────────


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Blacklist the provided refresh token so it can no longer be used.
    Requires a valid access token in the Authorization header.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={
            204: OpenApiResponse(description="Successfully logged out"),
            400: OpenApiResponse(description="Invalid or already-blacklisted token"),
        },
        summary="Logout — blacklist refresh token",
        description=(
            "Invalidates the supplied refresh token. "
            "Send { \"refresh_token\": \"<token>\" } in the request body."
        ),
        tags=["Auth"],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh_token"])
            token.blacklist()
            logger.info("User %s logged out — token blacklisted.", request.user.email)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ─── Current User (me) ────────────────────────────────────────────────────────


class MeView(APIView):
    """
    GET  /api/v1/auth/me/   — retrieve current user profile
    PATCH /api/v1/auth/me/  — partially update first_name / last_name / email
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        summary="Get current user profile",
        description="Returns the authenticated user's profile information.",
        tags=["Auth"],
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UpdateProfileSerializer,
        responses={200: UserProfileSerializer},
        summary="Update current user profile",
        description="Partially updates first_name, last_name, and/or email for the authenticated user.",
        tags=["Auth"],
    )
    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("User %s updated their profile.", request.user.email)
        return Response(
            UserProfileSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )


# ─── Token Verification ───────────────────────────────────────────────────────


class CustomTokenVerifyView(TokenVerifyView):
    """
    POST /api/v1/auth/verify/

    Validates a JWT token. Used by other microservices to confirm
    a token is genuine and not expired/blacklisted.
    Body: { "token": "<access_or_refresh_token>" }
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: TokenVerifyResponseSerializer,
            401: OpenApiResponse(description="Token is invalid or expired"),
        },
        summary="Verify a JWT token",
        description=(
            "Validates the supplied token. "
            "Returns 200 if valid, 401 if invalid or expired. "
            "Intended for inter-service token validation."
        ),
        tags=["Auth"],
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data = {"detail": "Token is valid."}
        return response
