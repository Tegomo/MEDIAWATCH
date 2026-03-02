"""Script pour charger des données de test dans la base de données"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.db.base import SessionLocal, engine, Base
from src.models.organization import Organization, SubscriptionPlan, SubscriptionStatus
from src.models.user import User, UserRole
from src.models.keyword import Keyword, KeywordCategory
from src.models.source import Source, SourceType


def seed_database():
    """Charge des données de test"""
    print("🌱 Chargement des données de test...")

    db: Session = SessionLocal()

    try:
        # Créer les tables si elles n'existent pas
        Base.metadata.create_all(bind=engine)

        # 1. Créer 2 organisations
        org1 = Organization(
            id=uuid4(),
            name="Agence Com CI",
            subscription_plan=SubscriptionPlan.PRO,
            subscription_status=SubscriptionStatus.ACTIVE,
            keyword_limit=50,
            user_limit=5,
        )
        org2 = Organization(
            id=uuid4(),
            name="Orange Côte d'Ivoire",
            subscription_plan=SubscriptionPlan.ENTERPRISE,
            subscription_status=SubscriptionStatus.ACTIVE,
            keyword_limit=999,
            user_limit=999,
        )
        db.add_all([org1, org2])
        db.commit()
        print(f"✅ Organisations créées: {org1.name}, {org2.name}")

        # 2. Créer 3 utilisateurs (1 admin, 2 clients)
        admin_user = User(
            id=uuid4(),
            email="admin@mediawatch.ci",
            full_name="Admin MediaWatch",
            role=UserRole.ADMIN,
            organization_id=org1.id,
            supabase_user_id=uuid4(),
        )
        client1 = User(
            id=uuid4(),
            email="client1@agence.ci",
            full_name="Jean Kouassi",
            role=UserRole.CLIENT,
            organization_id=org1.id,
            supabase_user_id=uuid4(),
        )
        client2 = User(
            id=uuid4(),
            email="client2@orange.ci",
            full_name="Marie Koné",
            role=UserRole.CLIENT,
            organization_id=org2.id,
            supabase_user_id=uuid4(),
        )
        db.add_all([admin_user, client1, client2])
        db.commit()
        print(f"✅ Utilisateurs créés: {admin_user.email}, {client1.email}, {client2.email}")

        # 3. Créer 5 sources médias
        sources = [
            Source(
                id=uuid4(),
                name="Fraternité Matin",
                url="https://www.fratmat.info",
                type=SourceType.PRESS,
                scraper_class="fraternite_matin",
                prestige_score=0.9,
            ),
            Source(
                id=uuid4(),
                name="Abidjan.net",
                url="https://news.abidjan.net",
                type=SourceType.PRESS,
                scraper_class="abidjan_net",
                prestige_score=0.8,
            ),
            Source(
                id=uuid4(),
                name="L'Infodrome",
                url="https://www.linfodrome.com",
                type=SourceType.PRESS,
                scraper_class="linfodrome",
                prestige_score=0.7,
            ),
            Source(
                id=uuid4(),
                name="Koaci",
                url="https://koaci.com",
                type=SourceType.PRESS,
                scraper_class="koaci",
                prestige_score=0.75,
            ),
            Source(
                id=uuid4(),
                name="AIP (Agence Ivoirienne de Presse)",
                url="https://www.aip.ci",
                type=SourceType.RSS,
                scraper_class="aip_rss",
                prestige_score=0.95,
            ),
        ]
        db.add_all(sources)
        db.commit()
        print(f"✅ Sources créées: {len(sources)} sources")

        # 4. Créer 10 mots-clés pour org1
        keywords_org1 = [
            Keyword(
                id=uuid4(),
                text="Orange CI",
                normalized_text="orange ci",
                category=KeywordCategory.BRAND,
                organization_id=org1.id,
            ),
            Keyword(
                id=uuid4(),
                text="MTN Côte d'Ivoire",
                normalized_text="mtn cote d'ivoire",
                category=KeywordCategory.COMPETITOR,
                organization_id=org1.id,
            ),
            Keyword(
                id=uuid4(),
                text="Moov Africa",
                normalized_text="moov africa",
                category=KeywordCategory.COMPETITOR,
                organization_id=org1.id,
            ),
            Keyword(
                id=uuid4(),
                text="Alassane Ouattara",
                normalized_text="alassane ouattara",
                category=KeywordCategory.PERSON,
                organization_id=org1.id,
            ),
            Keyword(
                id=uuid4(),
                text="Abidjan",
                normalized_text="abidjan",
                category=KeywordCategory.CUSTOM,
                organization_id=org1.id,
            ),
        ]

        # 5 mots-clés pour org2
        keywords_org2 = [
            Keyword(
                id=uuid4(),
                text="Orange Money",
                normalized_text="orange money",
                category=KeywordCategory.PRODUCT,
                organization_id=org2.id,
            ),
            Keyword(
                id=uuid4(),
                text="5G Côte d'Ivoire",
                normalized_text="5g cote d'ivoire",
                category=KeywordCategory.CUSTOM,
                organization_id=org2.id,
            ),
            Keyword(
                id=uuid4(),
                text="Télécommunications",
                normalized_text="telecommunications",
                category=KeywordCategory.CUSTOM,
                organization_id=org2.id,
            ),
            Keyword(
                id=uuid4(),
                text="Internet mobile",
                normalized_text="internet mobile",
                category=KeywordCategory.PRODUCT,
                organization_id=org2.id,
            ),
            Keyword(
                id=uuid4(),
                text="Fibre optique",
                normalized_text="fibre optique",
                category=KeywordCategory.PRODUCT,
                organization_id=org2.id,
            ),
        ]

        db.add_all(keywords_org1 + keywords_org2)
        db.commit()
        print(f"✅ Mots-clés créés: {len(keywords_org1 + keywords_org2)} keywords")

        print("\n✅ Données de test chargées avec succès!")
        print("\n📊 Résumé:")
        print(f"   - 2 organisations")
        print(f"   - 3 utilisateurs (1 admin, 2 clients)")
        print(f"   - 5 sources médias")
        print(f"   - 10 mots-clés")
        print("\n🔐 Comptes de test:")
        print(f"   Admin: {admin_user.email}")
        print(f"   Client 1: {client1.email}")
        print(f"   Client 2: {client2.email}")
        print("\n⚠️  Note: Ces utilisateurs doivent être créés dans Supabase Auth séparément")

    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
