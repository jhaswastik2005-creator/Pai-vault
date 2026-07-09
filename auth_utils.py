import os
import datetime
import jwt
from fastapi import Request

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-this-in-production")
COOKIE_NAME = "pai_session"
ALGORITHM = "HS256"

def create_token(user_id: str, email: str, role: str) -> str:
    """
    Generate a signed JWT token containing user context
    """
    payload = {
        "id": user_id,
        "email": email.lower().strip(),
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> dict | None:
    """
    Decode and verify a signed JWT token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_current_user_session(request: Request) -> dict | None:
    """
    Helper to extract and decode session cookie from FastAPI requests
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return decode_token(token)
