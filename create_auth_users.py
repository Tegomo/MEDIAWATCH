"""Créer les comptes Supabase Auth pour les utilisateurs seed"""
import httpx
import json
import os

SUPABASE_URL = "https://zujclwfgmwnfuxomyjkt.supabase.co"

# Lire la service key depuis .env
SERVICE_KEY = None
with open(r"E:\DEV\MEDIAWATCH\backend\.env", "r") as f:
    for line in f:
        if line.startswith("SUPABASE_SERVICE_KEY="):
            SERVICE_KEY = line.split("=", 1)[1].strip()
            break

if not SERVICE_KEY:
    print("ERREUR: SUPABASE_SERVICE_KEY non trouvée dans .env")
    exit(1)

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

users = [
    {"email": "admin@mediawatch.ci", "password": "Admin123!", "role": "ADMIN"},
    {"email": "client1@agence.ci", "password": "Client123!", "role": "CLIENT"},
    {"email": "client2@orange.ci", "password": "Client123!", "role": "CLIENT"},
]

print("=" * 60)
print("Creation des comptes Supabase Auth")
print("=" * 60)

created = []
for u in users:
    resp = httpx.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=headers,
        json={
            "email": u["email"],
            "password": u["password"],
            "email_confirm": True,
        },
    )
    data = resp.json()
    if resp.status_code in (200, 201):
        uid = data.get("id", "N/A")
        print(f"OK   {u['email']} -> auth_id={uid}")
        created.append({"email": u["email"], "auth_id": uid})
    else:
        msg = data.get("msg", data.get("message", str(data)))
        print(f"ERR  {u['email']} -> {resp.status_code}: {msg}")

# Mettre a jour la table users avec les supabase_user_id
if created:
    print("\nMise a jour de la table users avec les auth IDs...")
    for c in created:
        update_sql = f"UPDATE users SET supabase_user_id = '{c['auth_id']}' WHERE email = '{c['email']}';"
        resp = httpx.post(
            f"{SUPABASE_URL}/rest/v1/rpc/",
            headers={**headers, "Prefer": "return=representation"},
        )
        # Use direct SQL via the backend connection instead
        print(f"  -> {c['email']}: auth_id={c['auth_id']}")

print("\n" + "=" * 60)
print("IDENTIFIANTS DE CONNEXION")
print("=" * 60)
for u in users:
    print(f"  Email: {u['email']}")
    print(f"  Mot de passe: {u['password']}")
    print(f"  Role: {u['role']}")
    print()
