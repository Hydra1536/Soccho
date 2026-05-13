from django.db import models


class OTPCode(models.Model):
    CONTEXT_REGISTER = "register"
    CONTEXT_FORGOT = "forgot"
    CONTEXT_CHANGE_PW = "change_pw"

    CONTEXT_CHOICES = (
        (CONTEXT_REGISTER, "Register"),
        (CONTEXT_FORGOT, "Forgot password"),
        (CONTEXT_CHANGE_PW, "Change password"),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="otp_codes")
    code_hash = models.CharField(max_length=128)
    context = models.CharField(max_length=20, choices=CONTEXT_CHOICES)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_codes"
