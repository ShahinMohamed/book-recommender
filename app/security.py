import hmac
import secrets

from fastapi import HTTPException, Request, status


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return str(token)


def require_csrf(request: Request, submitted_token: str | None) -> None:
    expected = request.session.get("csrf_token")
    if not expected or not submitted_token or not hmac.compare_digest(str(expected), submitted_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
