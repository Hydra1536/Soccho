from django.urls import include, path

from apps.otp.views import VerifyOTPView
from apps.users.views import GoogleOAuthCallbackView, GoogleOAuthStartView, GoogleOAuthView

urlpatterns = [
    path("api/auth/", include("apps.users.urls")),
    path("api/auth/otp/verify/", VerifyOTPView.as_view(), name="verify-otp"),
    path("oauth/google/start/", GoogleOAuthStartView.as_view(), name="google-oauth-start"),
    path("oauth/google/callback/", GoogleOAuthCallbackView.as_view(), name="google-oauth-callback"),
    path("oauth/", GoogleOAuthView.as_view(), name="google-oauth"),
]
