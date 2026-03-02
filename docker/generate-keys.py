"""Generate Supabase JWT keys (anon + service_role) for local Docker setup."""
import json
import hmac
import hashlib
import base64
import sys

JWT_SECRET = sys.argv[1] if len(sys.argv) > 1 else "super-secret-jwt-token-with-at-least-32-characters-long"

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def make_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    segments = [
        b64url(json.dumps(header, separators=(",", ":")).encode()),
        b64url(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(b64url(signature))
    return ".".join(segments)

# iat=2025-01-01, exp=2030-01-01
anon = make_jwt({"role": "anon", "iss": "supabase", "iat": 1735689600, "exp": 1893456000}, JWT_SECRET)
service = make_jwt({"role": "service_role", "iss": "supabase", "iat": 1735689600, "exp": 1893456000}, JWT_SECRET)

print(f"JWT_SECRET={JWT_SECRET}")
print(f"ANON_KEY={anon}")
print(f"SERVICE_ROLE_KEY={service}")
