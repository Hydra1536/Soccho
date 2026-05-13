import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.otp.models import OTPCode


def _otp_digest(value: str) -> str:
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_otp(user, context: str) -> str:
    code = f"{secrets.randbelow(1000000):06d}"
    OTPCode.objects.create(
        user=user,
        code_hash=_otp_digest(code),
        context=context,
        expires_at=timezone.now() + timedelta(minutes=10),
        is_used=False,
    )
    return code


def hash_otp(code: str) -> str:
    return _otp_digest(code)
