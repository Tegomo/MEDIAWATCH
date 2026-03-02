"""Test du scan URL avec Jina (après paiement)"""
import httpx
import sys

BACKEND = "http://127.0.0.1:8000/v1"

# Login
print("Login admin...")
login_resp = httpx.post(f"{BACKEND}/auth/login", json={
    "email": "admin@mediawatch.ci",
    "password": "Admin123!",
}, timeout=30)
if login_resp.status_code != 200:
    print(f"FAIL: Login ({login_resp.status_code})")
    sys.exit(1)

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("OK: Token obtenu\n")

# Scan URL
test_url = "https://news.abidjan.net/videos/16139/mccann-unhappy"
print(f"Scan de: {test_url}")
print("(peut prendre 30-60s pour le scraping + nettoyage IA...)")
resp = httpx.post(
    f"{BACKEND}/mentions/scan/url",
    json={"url": test_url},
    headers=headers,
    timeout=180,
)
print(f"Status: {resp.status_code}")
print(f"Reponse: {resp.json()}")

# Vérifier les mentions
print("\nMentions en base:")
m_resp = httpx.get(f"{BACKEND}/mentions?limit=10", headers=headers, timeout=60)
if m_resp.status_code == 200:
    data = m_resp.json()
    print(f"  Total: {data.get('total', 0)}")
    for m in data.get("mentions", []):
        kw = m.get("keyword", {}).get("text", "?")
        title = m.get("article", {}).get("title", "?")[:60]
        print(f"  - [{kw}] {title}")
