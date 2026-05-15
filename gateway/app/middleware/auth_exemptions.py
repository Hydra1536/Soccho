UNPROTECTED_PREFIXES = (
    "/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/auth/forgot-password",
    "/api/auth/otp/verify",
    "/oauth",
    "/oauth/",
)


def is_unprotected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in UNPROTECTED_PREFIXES)


def should_skip_auth(method: str, path: str) -> bool:
    # CORS preflight requests must bypass auth checks.
    if (method or "").upper() == "OPTIONS":
        return True
    return is_unprotected(path)
