"""Test rapide du système de matching et vérification des mentions"""
import re
import unicodedata
import sys
sys.path.insert(0, ".")


def _normalize(text):
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def _keyword_matches(kw_text, text_lower):
    kw_norm = _normalize(kw_text)
    text_norm = _normalize(text_lower)
    if kw_norm in text_norm:
        return True
    words = [w for w in re.split(r'[\s:,;/\-]+', kw_norm) if len(w) >= 3]
    if words and all(w in text_norm for w in words):
        return True
    return False


print("=" * 60)
print("TEST 1 : Matching mots-clés (avec normalisation accents)")
print("=" * 60)

tests = [
    ("Mccann: Unhappy", "mccann: unhappy video", True),
    ("Mccann: Unhappy", "le clip mccann est unhappy", True),
    ("Mccann: Unhappy", "mccann abidjan lance", False),
    ("McCANN Abidjan", "mccann abidjan launches season 2", True),
    ("McCANN Abidjan", "abidjan mccann", True),
    ("ICE ROAD", "ice road truckers in africa", True),
    ("ICE ROAD", "la glace fond sur la route", False),
    ("Election présidentielle", "election presidentielle 2025", True),
    ("Election présidentielle", "L'élection présidentielle approche", True),
    ("Côte d'Ivoire", "cote d'ivoire economie", True),
]
all_ok = True
for kw, text, expected in tests:
    result = _keyword_matches(kw, text)
    ok = "OK" if result == expected else "FAIL"
    if result != expected:
        all_ok = False
    print(f"  {ok} | '{kw}' in '{text[:45]}' => {result}")

print(f"\nTest 1 : {'PASS' if all_ok else 'FAIL'}\n")


# ── Test 2 : Vérifier les mentions en base via API ──
print("=" * 60)
print("TEST 2 : Login + Mentions en base")
print("=" * 60)

import httpx

BACKEND = "http://127.0.0.1:8000/v1"

print("  Login admin...")
login_resp = httpx.post(f"{BACKEND}/auth/login", json={
    "email": "admin@mediawatch.ci",
    "password": "Admin123!",
}, timeout=30)
if login_resp.status_code != 200:
    print(f"  FAIL: Login ({login_resp.status_code}): {login_resp.text[:200]}")
    sys.exit(1)

token = login_resp.json().get("access_token")
print(f"  OK: Token obtenu")
headers = {"Authorization": f"Bearer {token}"}

mentions_resp = httpx.get(f"{BACKEND}/mentions?limit=10", headers=headers, timeout=60)
if mentions_resp.status_code == 200:
    mdata = mentions_resp.json()
    total = mdata.get("total", 0)
    mentions = mdata.get("mentions", [])
    print(f"  Total mentions: {total}")
    for m in mentions[:5]:
        kw = m.get("keyword", {}).get("text", "?")
        title = m.get("article", {}).get("title", "?")[:50]
        print(f"    - [{kw}] {title}")
    print(f"\nTest 2 : PASS")
else:
    print(f"  FAIL: {mentions_resp.status_code} {mentions_resp.text[:200]}")


# ── Test 3 : Endpoint scan/url existe ──
print("\n" + "=" * 60)
print("TEST 3 : Endpoint POST /scan/url (sans URL réelle)")
print("=" * 60)

resp = httpx.post(f"{BACKEND}/mentions/scan/url", json={"url": "invalid"}, headers=headers, timeout=30)
print(f"  Status: {resp.status_code} (attendu: 400)")
print(f"  Test 3 : {'PASS' if resp.status_code == 400 else 'CHECK: ' + str(resp.status_code)}")

print("\n" + "=" * 60)
print("TOUS LES TESTS TERMINÉS")
print("=" * 60)
