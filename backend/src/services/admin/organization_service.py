"""Service admin pour la gestion des organisations"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.organization import Organization, SubscriptionStatus, SubscriptionPlan
from src.models.user import User
from src.models.keyword import Keyword
from src.models.mention import Mention
from src.lib.logger import logger


class OrganizationAdminService:
    """Service pour la gestion admin des comptes organisations"""

    def __init__(self, db: Session):
        self.db = db

    def list_organizations(
        self,
        plan: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """Liste toutes les organisations avec leurs statistiques."""
        query = self.db.query(Organization).order_by(Organization.created_at.desc())

        if plan:
            try:
                plan_enum = SubscriptionPlan(plan)
                query = query.filter(Organization.subscription_plan == plan_enum)
            except ValueError:
                pass

        if status:
            try:
                status_enum = SubscriptionStatus(status)
                query = query.filter(Organization.subscription_status == status_enum)
            except ValueError:
                pass

        orgs = query.all()
        result = []

        for org in orgs:
            user_count = (
                self.db.query(func.count(User.id))
                .filter(User.organization_id == org.id)
                .scalar()
            )
            keyword_count = (
                self.db.query(func.count(Keyword.id))
                .filter(Keyword.organization_id == org.id)
                .scalar()
            )
            mention_count = (
                self.db.query(func.count(Mention.id))
                .join(Keyword, Mention.keyword_id == Keyword.id)
                .filter(Keyword.organization_id == org.id)
                .scalar()
            )

            result.append({
                "id": str(org.id),
                "name": org.name,
                "subscription_plan": org.subscription_plan.value,
                "subscription_status": org.subscription_status.value,
                "keyword_limit": org.keyword_limit,
                "user_limit": org.user_limit,
                "user_count": user_count,
                "keyword_count": keyword_count,
                "mention_count": mention_count,
                "created_at": org.created_at.isoformat(),
                "updated_at": org.updated_at.isoformat() if org.updated_at else None,
            })

        return result

    def get_organization(self, org_id: UUID) -> Optional[dict]:
        """Détails complets d'une organisation."""
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return None

        user_count = (
            self.db.query(func.count(User.id))
            .filter(User.organization_id == org.id)
            .scalar()
        )
        keyword_count = (
            self.db.query(func.count(Keyword.id))
            .filter(Keyword.organization_id == org.id)
            .scalar()
        )
        mention_count = (
            self.db.query(func.count(Mention.id))
            .join(Keyword, Mention.keyword_id == Keyword.id)
            .filter(Keyword.organization_id == org.id)
            .scalar()
        )

        result = {
            "id": str(org.id),
            "name": org.name,
            "subscription_plan": org.subscription_plan.value,
            "subscription_status": org.subscription_status.value,
            "keyword_limit": org.keyword_limit,
            "user_limit": org.user_limit,
            "user_count": user_count,
            "keyword_count": keyword_count,
            "mention_count": mention_count,
            "created_at": org.created_at.isoformat(),
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }

        # Ajouter les utilisateurs
        users = (
            self.db.query(User)
            .filter(User.organization_id == org_id)
            .all()
        )
        result["users"] = [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]

        return result

    def suspend_organization(self, org_id: UUID) -> dict:
        """Suspend une organisation."""
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"success": False, "error": "Organisation non trouvée"}

        if org.subscription_status == SubscriptionStatus.SUSPENDED:
            return {"success": False, "error": "Organisation déjà suspendue"}

        org.subscription_status = SubscriptionStatus.SUSPENDED
        org.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Organisation {org.name} suspendue")

        # T114 - Notifier par email
        self._notify_suspension(org, suspended=True)

        return {"success": True, "message": f"Organisation {org.name} suspendue"}

    def reactivate_organization(self, org_id: UUID) -> dict:
        """Réactive une organisation suspendue."""
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"success": False, "error": "Organisation non trouvée"}

        if org.subscription_status != SubscriptionStatus.SUSPENDED:
            return {"success": False, "error": "Organisation non suspendue"}

        org.subscription_status = SubscriptionStatus.ACTIVE
        org.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Organisation {org.name} réactivée")

        self._notify_suspension(org, suspended=False)

        return {"success": True, "message": f"Organisation {org.name} réactivée"}

    def update_limits(self, org_id: UUID, keyword_limit: Optional[int] = None, user_limit: Optional[int] = None) -> dict:
        """Met à jour les limites d'une organisation."""
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"success": False, "error": "Organisation non trouvée"}

        if keyword_limit is not None:
            org.keyword_limit = keyword_limit
        if user_limit is not None:
            org.user_limit = user_limit
        org.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Limites mises à jour pour {org.name}: keywords={org.keyword_limit}, users={org.user_limit}")
        return {
            "success": True,
            "message": f"Limites mises à jour pour {org.name}",
            "keyword_limit": org.keyword_limit,
            "user_limit": org.user_limit,
        }

    def create_organization(
        self,
        name: str,
        subscription_plan: str = "basic",
        subscription_status: str = "trial",
        keyword_limit: int = 10,
        user_limit: int = 1,
    ) -> dict:
        """Crée une nouvelle organisation."""
        try:
            plan_enum = SubscriptionPlan(subscription_plan)
        except ValueError:
            return {"success": False, "error": f"Plan invalide: {subscription_plan}"}

        try:
            status_enum = SubscriptionStatus(subscription_status)
        except ValueError:
            return {"success": False, "error": f"Statut invalide: {subscription_status}"}

        org = Organization(
            name=name,
            subscription_plan=plan_enum,
            subscription_status=status_enum,
            keyword_limit=keyword_limit,
            user_limit=user_limit,
        )
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)

        logger.info(f"Organisation créée: {org.name} (plan={subscription_plan})")
        return {
            "success": True,
            "message": f"Organisation {org.name} créée",
            "id": str(org.id),
        }

    def update_organization(
        self,
        org_id: UUID,
        name: Optional[str] = None,
        subscription_plan: Optional[str] = None,
        subscription_status: Optional[str] = None,
        keyword_limit: Optional[int] = None,
        user_limit: Optional[int] = None,
    ) -> dict:
        """Met à jour une organisation (nom, plan, statut, limites)."""
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"success": False, "error": "Organisation non trouvée"}

        if name is not None:
            org.name = name

        if subscription_plan is not None:
            try:
                org.subscription_plan = SubscriptionPlan(subscription_plan)
            except ValueError:
                return {"success": False, "error": f"Plan invalide: {subscription_plan}"}

        if subscription_status is not None:
            try:
                org.subscription_status = SubscriptionStatus(subscription_status)
            except ValueError:
                return {"success": False, "error": f"Statut invalide: {subscription_status}"}

        if keyword_limit is not None:
            org.keyword_limit = keyword_limit
        if user_limit is not None:
            org.user_limit = user_limit

        org.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Organisation mise à jour: {org.name}")
        return {
            "success": True,
            "message": f"Organisation {org.name} mise à jour",
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "subscription_plan": org.subscription_plan.value,
                "subscription_status": org.subscription_status.value,
                "keyword_limit": org.keyword_limit,
                "user_limit": org.user_limit,
            },
        }

    def delete_organization(self, org_id: UUID) -> dict:
        """Supprime une organisation et toutes ses données associées."""
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"success": False, "error": "Organisation non trouvée"}

        org_name = org.name
        self.db.delete(org)
        self.db.commit()

        logger.info(f"Organisation supprimée: {org_name}")
        return {"success": True, "message": f"Organisation {org_name} supprimée"}

    def _notify_suspension(self, org: Organization, suspended: bool):
        """Envoie un email de notification de suspension/réactivation."""
        try:
            users = self.db.query(User).filter(User.organization_id == org.id).all()
            from src.services.alerts.alert_service import AlertService
            alert_service = AlertService(self.db)

            action = "suspendu" if suspended else "réactivé"
            subject = f"Votre compte MediaWatch a été {action}"
            html = f"""
            <h2>Compte {action}</h2>
            <p>Votre compte organisation <strong>{org.name}</strong> a été {action}.</p>
            {"<p>Veuillez contacter le support pour plus d'informations.</p>" if suspended else "<p>Vous pouvez à nouveau accéder à la plateforme.</p>"}
            """

            for user in users:
                try:
                    alert_service._send_email(to_email=user.email, subject=subject, html_content=html)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Notification suspension échouée: {str(e)}")
