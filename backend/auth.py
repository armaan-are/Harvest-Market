import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import get_db

JWT_SECRET = "SECRET123"  # Mirror existing Express secret
ACCESS_TOKEN_EXPIRE_HOURS = 3

security_scheme = HTTPBearer()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: bytes) -> str:
    signature = hmac.new(JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(*, user_id: int, role: str) -> str:
    """
    Minimal HS256 JWT implementation using only the standard library.
    Payload matches the Express backend: { userId, role, exp }.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload: Dict[str, Any] = {
        "userId": user_id,
        "role": role,
        "exp": int(expire.timestamp()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature_b64 = _sign(signing_input)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
        )

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = _sign(signing_input)

    if not hmac.compare_digest(expected_sig, signature_b64):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature"
        )

    try:
        payload_json = _b64url_decode(payload_b64)
        payload = json.loads(payload_json.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    exp = payload.get("exp")
    if exp is None or int(time.time()) > int(exp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )

    return payload


def hash_password(password: str) -> str:
    """SHA256 hash (stdlib only)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify against stored SHA256 hash."""
    if not password_hash:
        return False
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == password_hash


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db=Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid auth header format",
        )

    token = credentials.credentials
    payload = _decode_token(token)

    user_id = payload.get("userId")
    role = payload.get("role")
    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # Verify user still exists
    cursor = db.execute(
        "SELECT id, email, role FROM users WHERE id = ?", (user_id,)
    )
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return {"userId": row["id"], "role": row["role"], "email": row["email"]}

