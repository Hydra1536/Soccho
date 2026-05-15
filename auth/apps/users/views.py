import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request as urllib_request

import jwt
from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
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
GOOGLE_STATE_SALT = "google-oauth-state"
GOOGLE_SCOPES = "openid email profile"


class PublicEndpointMixin:
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]


def _axes_protected(view_cls):
    if not getattr(settings, "AXES_ENABLED", False):
        return view_cls
    return method_decorator(axes_dispatch, name="dispatch")(view_cls)


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


def _allowed_frontend_origins() -> list[str]:
    return [origin.rstrip("/") for origin in getattr(settings, "ALLOWED_ORIGINS", []) if origin]


def _is_allowed_frontend_origin(origin: str) -> bool:
    normalized = origin.rstrip("/")
    allowed = _allowed_frontend_origins()
    return not allowed or normalized in allowed


def _default_frontend_origin() -> str:
    allowed = _allowed_frontend_origins()
    return allowed[0] if allowed else ""


def _build_public_url(request, path: str) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    scheme = request.META.get("HTTP_X_FORWARDED_PROTO") or request.scheme
    host = request.META.get("HTTP_X_FORWARDED_HOST") or request.get_host()
    return f"{scheme}://{host}{normalized_path}"


def _redirect_to_frontend(frontend_origin: str, **params):
    origin = frontend_origin.rstrip("/")
    fragment = parse.urlencode({key: value for key, value in params.items() if value})
    target = f"{origin}/"
    if fragment:
        target = f"{target}#{fragment}"
    return HttpResponseRedirect(target)


def _google_callback_url(request) -> str:
    return _build_public_url(request, "/oauth/google/callback/")


def _google_state(frontend_origin: str) -> str:
    return signing.dumps({"frontend_origin": frontend_origin.rstrip("/")}, salt=GOOGLE_STATE_SALT)


def _load_google_state(raw_state: str) -> dict:
    return signing.loads(raw_state, salt=GOOGLE_STATE_SALT, max_age=600)


def _google_username_seed(name: str) -> str:
    normalized = "".join(ch for ch in name.lower().replace(" ", "_") if ch.isalnum() or ch == "_")
    return normalized[:30] or "user"


def _unique_username(seed: str) -> str:
    base = seed[:30] or "user"
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        suffix_text = f"_{suffix}"
        candidate = f"{base[:30 - len(suffix_text)]}{suffix_text}"
        suffix += 1
    return candidate


def _load_google_payload(id_token: str = "", access_token: str = "") -> dict:
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
                raise ValueError("Google audience mismatch")
            return payload

        if access_token:
            req = urllib_request.Request(
                f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={parse.quote(access_token)}",
                headers={"Accept": "application/json"},
                method="GET",
            )
            with urllib_request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise ValueError("Google token validation failed") from exc

    raise ValueError("Missing Google token")


def _google_user_from_payload(payload: dict) -> User:
    email = payload.get("email")
    google_sub = payload.get("sub")
    name = payload.get("name") or "user"
    if not email or not google_sub:
        raise ValueError("Missing Google user data")

    user = User.objects.filter(google_sub=google_sub).first()
    if user is None:
        user = User.objects.filter(email=email).first()

    if user is None:
        user = User.objects.create(
            email=email,
            username=_unique_username(_google_username_seed(name)),
            password_hash=None,
            google_sub=google_sub,
        )
        return user

    update_fields = []
    if user.google_sub != google_sub:
        user.google_sub = google_sub
        update_fields.append("google_sub")
    if user.email != email:
        user.email = email
        update_fields.append("email")
    if update_fields:
        user.save(update_fields=update_fields)
    return user


def _exchange_google_code(code: str, redirect_uri: str) -> dict:
    data = parse.urlencode(
        {
            "code": code,
            "client_id": getattr(settings, "GOOGLE_CLIENT_ID", ""),
            "client_secret": getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    req = urllib_request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise ValueError("Google code exchange failed") from exc


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


@_axes_protected
class RegisterView(PublicEndpointMixin, APIView):
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


@_axes_protected
class LoginView(PublicEndpointMixin, APIView):
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
            payload = _load_google_payload(id_token=id_token or "", access_token=access_token or "")
            user = _google_user_from_payload(payload)
        except ValueError:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        access, refresh = _issue_tokens(user)
        return Response({"access": access, "refresh": refresh}, status=status.HTTP_200_OK)


class GoogleOAuthStartView(PublicEndpointMixin, APIView):
    def get(self, request):
        frontend_origin = (request.query_params.get("frontend_origin") or "").strip().rstrip("/")
        if not frontend_origin or not _is_allowed_frontend_origin(frontend_origin):
            fallback_origin = _default_frontend_origin()
            if fallback_origin:
                return _redirect_to_frontend(fallback_origin, google_error="Frontend origin is not allowed for Google sign-in.")
            return Response({"detail": "Frontend origin is not allowed"}, status=status.HTTP_400_BAD_REQUEST)

        if not getattr(settings, "GOOGLE_CLIENT_ID", "") or not getattr(settings, "GOOGLE_CLIENT_SECRET", ""):
            return _redirect_to_frontend(frontend_origin, google_error="Google OAuth is not configured on the server.")

        params = parse.urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": _google_callback_url(request),
                "response_type": "code",
                "scope": GOOGLE_SCOPES,
                "state": _google_state(frontend_origin),
                "access_type": "online",
                "include_granted_scopes": "true",
                "prompt": "select_account",
            }
        )
        return HttpResponseRedirect(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


class GoogleOAuthCallbackView(PublicEndpointMixin, APIView):
    def get(self, request):
        raw_state = request.query_params.get("state", "")
        try:
            state = _load_google_state(raw_state)
        except signing.BadSignature:
            frontend_origin = _default_frontend_origin()
            if frontend_origin:
                return _redirect_to_frontend(frontend_origin, google_error="Google sign-in state expired. Please try again.")
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        frontend_origin = state.get("frontend_origin", "").rstrip("/")
        if not frontend_origin or not _is_allowed_frontend_origin(frontend_origin):
            frontend_origin = _default_frontend_origin()
            if not frontend_origin:
                return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        provider_error = request.query_params.get("error")
        if provider_error:
            return _redirect_to_frontend(frontend_origin, google_error=f"Google returned {provider_error}.")

        code = request.query_params.get("code")
        if not code:
            return _redirect_to_frontend(frontend_origin, google_error="Google did not return an authorization code.")

        try:
            token_payload = _exchange_google_code(code, _google_callback_url(request))
            payload = _load_google_payload(
                id_token=token_payload.get("id_token", ""),
                access_token=token_payload.get("access_token", ""),
            )
            user = _google_user_from_payload(payload)
        except ValueError:
            return _redirect_to_frontend(frontend_origin, google_error="Google sign-in could not be completed.")

        access, refresh = _issue_tokens(user)
        return _redirect_to_frontend(frontend_origin, access_token=access, refresh_token=refresh)


@_axes_protected
class ForgotPasswordView(PublicEndpointMixin, APIView):
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


@_axes_protected
class ChangePasswordView(PublicEndpointMixin, APIView):
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
