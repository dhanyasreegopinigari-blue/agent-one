import jwt
from jwt import PyJWKClient

from app.config import get_settings
from app.errors import AppError

_jwks: PyJWKClient | None = None


def verify_token(token: str) -> dict:
    s = get_settings()
    try:
        if s.supabase_jwt_secret:
            return jwt.decode(
                token,
                s.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["exp", "sub"]},
            )
        if not s.supabase_url:
            raise AppError(500, "INTERNAL", "Auth is not configured")
        global _jwks
        if _jwks is None:
            _jwks = PyJWKClient(
                f"{s.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json",
                cache_keys=True,
                lifespan=3600,
            )
        key = _jwks.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=f"{s.supabase_url.rstrip('/')}/auth/v1",
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise AppError(401, "UNAUTHENTICATED", "Invalid or expired token")
