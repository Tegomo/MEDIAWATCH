"""Seeder pour les sources médias initiales de Côte d'Ivoire.
Exécuter: python scripts/seed_sources.py
Les sources existantes (par nom) ne seront pas dupliquées.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.db.base import SessionLocal, engine, Base
from src.models.source import Source, SourceType


INITIAL_SOURCES = [
    {
        "name": "Fraternité Matin",
        "url": "https://www.fratmat.info",
        "type": SourceType.PRESS,
        "scraper_class": "fraternite_matin",
        "prestige_score": 0.9,
    },
    {
        "name": "Abidjan.net",
        "url": "https://news.abidjan.net",
        "type": SourceType.PRESS,
        "scraper_class": "abidjan_net",
        "prestige_score": 0.8,
    },
    {
        "name": "L'Infodrome",
        "url": "https://www.linfodrome.com",
        "type": SourceType.PRESS,
        "scraper_class": "linfodrome",
        "prestige_score": 0.7,
    },
    {
        "name": "Koaci",
        "url": "https://koaci.com",
        "type": SourceType.PRESS,
        "scraper_class": "koaci",
        "prestige_score": 0.75,
    },
    {
        "name": "AIP (Agence Ivoirienne de Presse)",
        "url": "https://www.aip.ci",
        "type": SourceType.RSS,
        "scraper_class": "aip_rss",
        "prestige_score": 0.95,
    },
]


def seed_sources():
    """Insère les sources initiales si elles n'existent pas déjà."""
    print("🌱 Seeding des sources médias...")

    db: Session = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)

        created = 0
        skipped = 0

        for src_data in INITIAL_SOURCES:
            existing = db.query(Source).filter(Source.name == src_data["name"]).first()
            if existing:
                print(f"  ⏭️  {src_data['name']} — déjà existante, skip")
                skipped += 1
                continue

            source = Source(
                name=src_data["name"],
                url=src_data["url"],
                type=src_data["type"],
                scraper_class=src_data["scraper_class"],
                prestige_score=src_data["prestige_score"],
            )
            db.add(source)
            created += 1
            print(f"  ✅ {src_data['name']} — créée")

        db.commit()

        print(f"\n📊 Résultat: {created} créées, {skipped} ignorées (déjà existantes)")
        print(f"   Total sources en base: {db.query(Source).count()}")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_sources()
