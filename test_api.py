"""Script de test pour l'API MediaWatch CI"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001/v1"

def print_response(title, response):
    """Afficher une réponse de manière formatée"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_health():
    """Test du health check"""
    response = requests.get("http://127.0.0.1:8001/health")
    print_response("TEST 1: Health Check", response)
    return response.status_code == 200

def test_signup():
    """Test de l'inscription"""
    import random
    random_id = random.randint(1000, 9999)
    signup_data = {
        "email": f"testuser{random_id}@gmail.com",
        "full_name": "Test User",
        "organization_name": "Test Organization",
        "password": "TestPassword123!",
        "subscription_plan": "basic"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print_response("TEST 2: Signup", response)
    
    if response.status_code == 201:
        return response.json()
    return None

def test_login(email, password):
    """Test de la connexion"""
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response("TEST 3: Login", response)
    
    if response.status_code == 200:
        return response.json()
    return None

def test_create_keyword(access_token):
    """Test de création d'un mot-clé"""
    headers = {"Authorization": f"Bearer {access_token}"}
    keyword_data = {
        "text": "Orange Côte d'Ivoire",
        "category": "BRAND",
        "enabled": True,
        "alert_enabled": True,
        "alert_threshold": 0.3
    }
    
    response = requests.post(f"{BASE_URL}/keywords", json=keyword_data, headers=headers)
    print_response("TEST 4: Create Keyword", response)
    
    if response.status_code == 201:
        return response.json()
    return None

def test_list_keywords(access_token):
    """Test de listage des mots-clés"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/keywords", headers=headers)
    print_response("TEST 5: List Keywords", response)
    
    return response.status_code == 200

def test_update_keyword(access_token, keyword_id):
    """Test de mise à jour d'un mot-clé"""
    headers = {"Authorization": f"Bearer {access_token}"}
    update_data = {
        "enabled": False,
        "alert_threshold": 0.5
    }
    
    response = requests.patch(f"{BASE_URL}/keywords/{keyword_id}", json=update_data, headers=headers)
    print_response("TEST 6: Update Keyword", response)
    
    return response.status_code == 200

def test_delete_keyword(access_token, keyword_id):
    """Test de suppression d'un mot-clé"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.delete(f"{BASE_URL}/keywords/{keyword_id}", headers=headers)
    print_response("TEST 7: Delete Keyword", response)
    
    return response.status_code == 204

def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "🚀 " * 30)
    print("DÉMARRAGE DES TESTS API MEDIAWATCH CI")
    print("🚀 " * 30 + "\n")
    
    results = []
    
    # Test 1: Health check
    print("▶️  Test 1/7: Health Check")
    results.append(("Health Check", test_health()))
    
    # Test 2: Signup
    print("\n▶️  Test 2/7: Signup")
    signup_result = test_signup()
    if signup_result:
        results.append(("Signup", True))
        access_token = signup_result.get("access_token")
        email = signup_result.get("email")
    else:
        results.append(("Signup", False))
        print("❌ Signup failed - arrêt des tests")
        print_summary(results)
        return
    
    # Test 3: Login
    print("\n▶️  Test 3/7: Login")
    login_result = test_login(email, "TestPassword123!")
    if login_result:
        results.append(("Login", True))
        access_token = login_result.get("access_token")  # Utiliser le nouveau token
    else:
        results.append(("Login", False))
        print("❌ Login failed - arrêt des tests")
        print_summary(results)
        return
    
    # Test 4: Create Keyword
    print("\n▶️  Test 4/7: Create Keyword")
    keyword_result = test_create_keyword(access_token)
    if keyword_result:
        results.append(("Create Keyword", True))
        keyword_id = keyword_result.get("id")
    else:
        results.append(("Create Keyword", False))
        keyword_id = None
    
    # Test 5: List Keywords
    print("\n▶️  Test 5/7: List Keywords")
    results.append(("List Keywords", test_list_keywords(access_token)))
    
    # Test 6: Update Keyword
    if keyword_id:
        print("\n▶️  Test 6/7: Update Keyword")
        results.append(("Update Keyword", test_update_keyword(access_token, keyword_id)))
    else:
        results.append(("Update Keyword", False))
    
    # Test 7: Delete Keyword
    if keyword_id:
        print("\n▶️  Test 7/7: Delete Keyword")
        results.append(("Delete Keyword", test_delete_keyword(access_token, keyword_id)))
    else:
        results.append(("Delete Keyword", False))
    
    # Résumé
    print_summary(results)

def print_summary(results):
    """Afficher le résumé des tests"""
    print("\n" + "📊 " * 30)
    print("RÉSUMÉ DES TESTS")
    print("📊 " * 30 + "\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Résultat: {passed}/{total} tests réussis ({passed*100//total}%)")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 Tous les tests sont passés avec succès !")
    else:
        print(f"⚠️  {total - passed} test(s) ont échoué")

if __name__ == "__main__":
    run_all_tests()
