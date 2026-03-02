"""Test scan URL d'un vrai article + vérification nettoyage IA"""
import httpx
import sys

BACKEND = "http://127.0.0.1:8000/v1"

# Login
print("Login...")
r = httpx.post(f"{BACKEND}/auth/login", json={
    "email": "admin@mediawatch.ci", "password": "Admin123!",
}, timeout=30)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("OK\n")

# Scanner un vrai article de presse
test_url = "https://news.abidjan.net/articles/750454/presidentielle-2025-ouattara-ne-veut-pas-etre-candidat-dixit-adjoumani"
print(f"Scan: {test_url}")
print("(scraping + IA, ~30-60s...)")
resp = httpx.post(f"{BACKEND}/mentions/scan/url", json={"url": test_url}, headers=headers, timeout=180)
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Message: {data.get('message','')}")
print(f"AI rejected: {data.get('ai_rejected', '?')}")
print(f"Mentions: {data.get('mentions_created', 0)}")

if resp.status_code == 200 and data.get("article_id"):
    # Vérifier le contenu stocké
    import os
    from dotenv import load_dotenv
    load_dotenv()
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_SERVICE_KEY")
    sh = {"apikey": supa_key, "Authorization": f"Bearer {supa_key}"}
    ar = httpx.get(f"{supa_url}/rest/v1/articles?select=title,cleaned_content&id=eq.{data['article_id']}", headers=sh)
    art = ar.json()[0]
    cleaned = art.get("cleaned_content", "")
    print(f"\n--- Contenu nettoyé stocké ({len(cleaned)} chars) ---")
    print(cleaned[:600])
    print("...")

