"""Update .env with correctly generated JWT keys."""
import json, hmac, hashlib, base64, re

JWT_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def make_jwt(payload, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    segs = [b64url(json.dumps(header, separators=(",", ":")).encode()), b64url(json.dumps(payload, separators=(",", ":")).encode())]
    sig = hmac.new(secret.encode(), ".".join(segs).encode(), hashlib.sha256).digest()
    segs.append(b64url(sig))
    return ".".join(segs)

anon = make_jwt({"role": "anon", "iss": "supabase", "iat": 1735689600, "exp": 1893456000}, JWT_SECRET)
service = make_jwt({"role": "service_role", "iss": "supabase", "iat": 1735689600, "exp": 1893456000}, JWT_SECRET)

# Read .env, replace keys using regex to match any existing value
with open(".env", "r") as f:
    content = f.read()

content = re.sub(r"^ANON_KEY=.*$", f"ANON_KEY={anon}", content, flags=re.MULTILINE)
content = re.sub(r"^SERVICE_ROLE_KEY=.*$", f"SERVICE_ROLE_KEY={service}", content, flags=re.MULTILINE)

with open(".env", "w") as f:
    f.write(content)

print(f"ANON_KEY={anon}")
print(f"SERVICE_ROLE_KEY={service}")
print("Updated .env")
