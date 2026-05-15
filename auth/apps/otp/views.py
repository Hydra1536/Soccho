from django.utils import timezone as dj_timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.otp.models import OTPCode
from apps.otp.services import hash_otp
from apps.users.models import User
from apps.users.views import _issue_tokens

INVALID_CREDENTIALS = {"detail": "Invalid credentials"}


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
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
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(username=username)
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

        access, refresh = _issue_tokens(user)
        return Response({"access": access, "refresh": refresh}, status=status.HTTP_200_OK)
