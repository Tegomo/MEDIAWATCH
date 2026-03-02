"""
Create test users in local Supabase (GoTrue + DB).
Run after docker compose up:
  python seed-users.py
"""
import httpx
import uuid
import sys
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000")
SERVICE_KEY = os.getenv("SERVICE_ROLE_KEY", "")

if not SERVICE_KEY:
    # Try to read from .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("SERVICE_ROLE_KEY="):
                SERVICE_KEY = line.strip().split("=", 1)[1]

if not SERVICE_KEY:
    print("ERROR: SERVICE_ROLE_KEY not set. Set it in .env or as env var.")
    sys.exit(1)

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

USERS = [
    {
        "email": "admin@mediawatch.ci",
        "password": "Admin123!",
        "full_name": "Admin MediaWatch",
        "role": "ADMIN",
        "org_name": "MediaWatch CI",
        "plan": "ENTERPRISE",
        "keyword_limit": 999,
        "user_limit": 999,
    },
    {
        "email": "client1@agence.ci",
        "password": "Client123!",
        "full_name": "Jean Kouassi",
        "role": "CLIENT",
        "org_name": None,  # Same org as admin
    },
    {
        "email": "client2@orange.ci",
        "password": "Client123!",
        "full_name": "Marie Koné",
        "role": "CLIENT",
        "org_name": "Orange CI",
        "plan": "PRO",
        "keyword_limit": 50,
        "user_limit": 5,
    },
]


def create_auth_user(email: str, password: str) -> str:
    """Create user in GoTrue and return supabase_user_id."""
    resp = httpx.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
        },
        headers=HEADERS,
        timeout=30,
    )
    if resp.status_code == 422 and "already been registered" in resp.text:
        # User exists, find their ID
        list_resp = httpx.get(f"{SUPABASE_URL}/auth/v1/admin/users", headers=HEADERS, timeout=30)
        for u in list_resp.json().get("users", []):
            if u["email"] == email:
                print(f"  (exists) {email} -> {u['id']}")
                return u["id"]
    resp.raise_for_status()
    uid = resp.json()["id"]
    print(f"  Created auth user: {email} -> {uid}")
    return uid


def db_insert(table: str, data: dict):
    """Insert into DB via PostgREST."""
    resp = httpx.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        json=data,
        headers={**HEADERS, "Prefer": "return=representation"},
        timeout=30,
    )
    if resp.status_code == 409:
        print(f"  (exists) {table}: {data.get('email') or data.get('name') or data.get('id')}")
        return None
    resp.raise_for_status()
    return resp.json()[0] if resp.json() else None


def db_select_one(table: str, **filters):
    """Select one from DB."""
    params = {"select": "*", "limit": "1"}
    for k, v in filters.items():
        params[k] = f"eq.{v}"
    resp = httpx.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        params=params,
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


def main():
    print("Seeding users into local Supabase...\n")

    org1_id = None  # MediaWatch CI org (shared by admin + client1)
    now = "2025-01-01T00:00:00Z"

    for user_def in USERS:
        email = user_def["email"]
        print(f"User: {email}")

        # 1. Create GoTrue auth user
        supa_uid = create_auth_user(email, user_def["password"])

        # 2. Create or reuse organization
        if user_def.get("org_name"):
            org = db_select_one("organizations", name=user_def["org_name"])
            if not org:
                org_id = str(uuid.uuid4())
                org = db_insert("organizations", {
                    "id": org_id,
                    "name": user_def["org_name"],
                    "subscription_plan": user_def.get("plan", "BASIC"),
                    "subscription_status": "ACTIVE",
                    "keyword_limit": user_def.get("keyword_limit", 10),
                    "user_limit": user_def.get("user_limit", 1),
                    "created_at": now,
                    "updated_at": now,
                })
                print(f"  Created org: {user_def['org_name']} -> {org_id}")
            else:
                org_id = org["id"]
                print(f"  (exists) org: {user_def['org_name']}")

            if user_def["org_name"] == "MediaWatch CI":
                org1_id = org_id
        else:
            org_id = org1_id
            print(f"  Using org: MediaWatch CI -> {org_id}")

        # 3. Create DB user
        existing = db_select_one("users", email=email)
        if not existing:
            db_insert("users", {
                "id": str(uuid.uuid4()),
                "email": email,
                "full_name": user_def["full_name"],
                "role": user_def["role"],
                "organization_id": org_id,
                "supabase_user_id": supa_uid,
                "created_at": now,
                "updated_at": now,
            })
            print(f"  Created DB user: {email}")
        else:
            print(f"  (exists) DB user: {email}")

        print()

    # 4. Seed keywords for org1
    if org1_id:
        print("Seeding keywords for MediaWatch CI...")
        keywords = [
            ("McCANN Abidjan", "mccann abidjan", "BRAND"),
            ("Mccann: Unhappy", "mccann unhappy", "BRAND"),
            ("Orange CI", "orange ci", "BRAND"),
            ("Election présidentielle", "election presidentielle", "CUSTOM"),
        ]
        for text, norm, cat in keywords:
            existing = db_select_one("keywords", text=text, organization_id=org1_id)
            if not existing:
                db_insert("keywords", {
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "normalized_text": norm,
                    "category": cat,
                    "enabled": True,
                    "alert_enabled": True,
                    "alert_threshold": 0.3,
                    "organization_id": org1_id,
                    "total_mentions_count": 0,
                    "created_at": now,
                    "updated_at": now,
                })
                print(f"  Created keyword: {text}")
            else:
                print(f"  (exists) keyword: {text}")

    print("\nDone! Login credentials:")
    print("  admin@mediawatch.ci / Admin123!")
    print("  client1@agence.ci  / Client123!")
    print("  client2@orange.ci  / Client123!")


if __name__ == "__main__":
    main()
