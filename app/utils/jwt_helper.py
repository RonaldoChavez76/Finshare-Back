import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from app.config.settings import active_config


def generate_token(user_id: str, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=active_config.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, active_config.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, active_config.JWT_SECRET_KEY, algorithms=["HS256"])


def jwt_required(f):
    """Decorador: protege rutas con JWT Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            request.current_user_id = payload["sub"]
            request.current_user_email = payload["email"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated
