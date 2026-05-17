from django.utils import timezone as dj_timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.otp.models import OTPCode
from apps.otp.services import hash_otp
from apps.users.models import User
from apps.users.views import (
    AUTH_SERVICE_UNAVAILABLE,
    AuthStorageError,
    _change_password_cache_key,
    _get_user_by_email,
    _issue_tokens,
)

INVALID_CREDENTIALS = {"detail": "Invalid credentials"}


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        email = request.data.get("email")
        username = request.data.get("username")
        code = request.data.get("code")
        context = request.data.get("context")

        if (not email and not username) or not code or not context:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        try:
            if email:
                user = _get_user_by_email(email)
                if user is None:
                    raise User.DoesNotExist
            else:
                user = User.objects.get(username=username)
        except AuthStorageError:
            return Response(AUTH_SERVICE_UNAVAILABLE, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except User.DoesNotExist:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        otp = (
            OTPCode.objects.filter(
                user=user,
                context=context,
                code_hash=hash_otp(str(code)),
                is_used=False,
                expires_at__gt=dj_timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )
        if not otp:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        if context == OTPCode.CONTEXT_REGISTER and not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
        elif context == OTPCode.CONTEXT_CHANGE_PW:
            pending_password_hash = cache.get(_change_password_cache_key(str(user.id)))
            if not pending_password_hash:
                return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
            user.password_hash = pending_password_hash
            user.save(update_fields=["password_hash"])
            cache.delete(_change_password_cache_key(str(user.id)))

        access, refresh = _issue_tokens(user)
        return Response({"access": access, "refresh": refresh}, status=status.HTTP_200_OK)
