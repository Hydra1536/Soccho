import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request as urllib_request

import jwt
from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.otp.models import OTPCode
from apps.otp.services import generate_otp
from apps.users.models import RefreshToken, User
from apps.users.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
)

INVALID_CREDENTIALS = {"detail": "Invalid credentials"}


class PublicEndpointMixin:
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]


def _hash_token(token: str) -> str:
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()


def _issue_tokens(user: User):
    now = datetime.now(timezone.utc)
    access_payload = {
        "sub": str(user.id),
        "username": user.username,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    refresh_payload = {
        "sub": str(user.id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=12)).timestamp()),
    }

    access = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refresh = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")
    RefreshToken.objects.create(user=user, token_hash=_hash_token(refresh), is_revoked=False)
    return access, refresh


def _send_otp_email(email: str, code: str, context: str):
    data = parse.urlencode(
        {
            "email": email,
            "subject": "Soccho OTP Code",
            "message": f"Your OTP for {context} is {code}. It expires in 10 minutes.",
        }
    ).encode("utf-8")
    req = urllib_request.Request(
        "https://formsubmit.co/ajax/7e14a0b017fee24874d1075e4e04f8b0",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as resp:
            if resp.status >= 400:
                raise ValueError("email send failed")
    except (error.URLError, ValueError):
        raise ValueError("email send failed")


class RegisterView(PublicEndpointMixin, APIView):
    @axes_dispatch
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user, created = User.objects.get_or_create(
                username=serializer.validated_data["username"],
                defaults={
                    "email": serializer.validated_data["email"],
                    "password_hash": serializer.get_password_hash(),
                },
            )
            if not created:
                return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
        except IntegrityError:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            otp_code = generate_otp(user, OTPCode.CONTEXT_REGISTER)
            _send_otp_email(serializer.validated_data["email"], otp_code, OTPCode.CONTEXT_REGISTER)
        except Exception:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class LoginView(PublicEndpointMixin, APIView):
    @axes_dispatch
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(email=serializer.validated_data["email"])
        except User.DoesNotExist:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        if not user.password_hash or not check_password(serializer.validated_data["password"], user.password_hash):
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        access, refresh = _issue_tokens(user)
        return Response({"access": access, "refresh": refresh}, status=status.HTTP_200_OK)


class RefreshView(PublicEndpointMixin, APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError
        except jwt.PyJWTError:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        token_hash = _hash_token(refresh)
        try:
            stored = RefreshToken.objects.select_related("user").get(token_hash=token_hash, is_revoked=False)
        except RefreshToken.DoesNotExist:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        stored.is_revoked = True
        stored.save(update_fields=["is_revoked"])

        access, new_refresh = _issue_tokens(stored.user)
        return Response({"access": access, "refresh": new_refresh}, status=status.HTTP_200_OK)


class LogoutView(PublicEndpointMixin, APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        token_hash = _hash_token(refresh)
        updated = RefreshToken.objects.filter(token_hash=token_hash, is_revoked=False).update(is_revoked=True)
        if updated == 0:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleOAuthView(PublicEndpointMixin, APIView):
    def post(self, request):
        id_token = request.data.get("id_token")
        access_token = request.data.get("access_token")
        if not id_token and not access_token:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            if id_token:
                req = urllib_request.Request(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={parse.quote(id_token)}",
                    headers={"Accept": "application/json"},
                    method="GET",
                )
                with urllib_request.urlopen(req, timeout=10) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))

                expected_aud = getattr(settings, "GOOGLE_CLIENT_ID", "")
                if expected_aud and payload.get("aud") != expected_aud:
                    return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
            else:
                req = urllib_request.Request(
                    f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={parse.quote(access_token)}",
                    headers={"Accept": "application/json"},
                    method="GET",
                )
                with urllib_request.urlopen(req, timeout=10) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        email = payload.get("email")
        name = payload.get("name") or "user"
        google_sub = payload.get("sub")
        if not email or not google_sub:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        username = "".join(ch for ch in name.lower().replace(" ", "_") if ch.isalnum() or ch == "_")[:30] or "user"
        user, _ = User.objects.get_or_create(
            google_sub=google_sub,
            defaults={"email": email, "username": username, "password_hash": None},
        )

        if user.username != username and len(username) <= 30:
            user.username = username
            user.email = email
            user.save(update_fields=["username", "email"])

        access, refresh = _issue_tokens(user)
        return Response({"access": access, "refresh": refresh}, status=status.HTTP_200_OK)


class ForgotPasswordView(PublicEndpointMixin, APIView):
    @axes_dispatch
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(email=serializer.validated_data["email"])
            otp_code = generate_otp(user, OTPCode.CONTEXT_FORGOT)
            _send_otp_email(serializer.validated_data["email"], otp_code, OTPCode.CONTEXT_FORGOT)
        except Exception:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class ChangePasswordView(PublicEndpointMixin, APIView):
    @axes_dispatch
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(email=serializer.validated_data["email"])
        except User.DoesNotExist:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        if not user.password_hash or not check_password(serializer.validated_data["old_password"], user.password_hash):
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        user.password_hash = make_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password_hash"])
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
