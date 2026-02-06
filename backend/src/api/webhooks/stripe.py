"""Webhook handler pour les événements Stripe"""
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
import stripe

from src.config import settings
from src.db.base import get_db
from src.models.organization import Organization, SubscriptionStatus
from src.services.payments.stripe_service import StripeService
from src.lib.logger import logger

router = APIRouter(prefix="/webhooks/stripe", tags=["Webhooks"])


@router.post("")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """
    Gérer les événements webhook de Stripe.
    
    Événements gérés:
    - customer.subscription.created: Abonnement créé
    - customer.subscription.updated: Abonnement mis à jour
    - customer.subscription.deleted: Abonnement annulé
    - invoice.payment_succeeded: Paiement réussi
    - invoice.payment_failed: Paiement échoué
    """
    # Récupérer le payload brut
    payload = await request.body()
    
    # Vérifier la signature du webhook
    try:
        event = StripeService.construct_webhook_event(
            payload=payload,
            sig_header=stripe_signature,
            webhook_secret=settings.stripe_webhook_secret,
        )
    except Exception as e:
        logger.error(f"Erreur de vérification du webhook Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    # Traiter l'événement selon son type
    event_type = event['type']
    event_data = event['data']['object']
    
    logger.info(f"Événement Stripe reçu: {event_type}")
    
    try:
        if event_type == 'customer.subscription.created':
            await handle_subscription_created(event_data, db)
        
        elif event_type == 'customer.subscription.updated':
            await handle_subscription_updated(event_data, db)
        
        elif event_type == 'customer.subscription.deleted':
            await handle_subscription_deleted(event_data, db)
        
        elif event_type == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event_data, db)
        
        elif event_type == 'invoice.payment_failed':
            await handle_payment_failed(event_data, db)
        
        else:
            logger.info(f"Événement non géré: {event_type}")
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'événement {event_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"status": "success"}


async def handle_subscription_created(subscription: dict, db: Session):
    """
    Gérer la création d'un abonnement.
    
    Met à jour le statut de l'organisation à ACTIVE.
    """
    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    
    # Récupérer l'organisation via les métadonnées
    metadata = subscription.get('metadata', {})
    organization_id = metadata.get('organization_id')
    
    if not organization_id:
        logger.warning(f"Pas d'organization_id dans les métadonnées de l'abonnement {subscription_id}")
        return
    
    # Mettre à jour l'organisation
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if organization:
        organization.subscription_status = SubscriptionStatus.ACTIVE
        db.commit()
        logger.info(f"Organisation {organization_id} activée suite à la création de l'abonnement")


async def handle_subscription_updated(subscription: dict, db: Session):
    """
    Gérer la mise à jour d'un abonnement.
    
    Met à jour le statut selon l'état de l'abonnement Stripe.
    """
    subscription_id = subscription.get('id')
    status = subscription.get('status')
    
    # Récupérer l'organisation via les métadonnées
    metadata = subscription.get('metadata', {})
    organization_id = metadata.get('organization_id')
    
    if not organization_id:
        logger.warning(f"Pas d'organization_id dans les métadonnées de l'abonnement {subscription_id}")
        return
    
    # Mapper les statuts Stripe vers nos statuts
    status_mapping = {
        'active': SubscriptionStatus.ACTIVE,
        'past_due': SubscriptionStatus.ACTIVE,  # Garder actif mais surveiller
        'unpaid': SubscriptionStatus.SUSPENDED,
        'canceled': SubscriptionStatus.CANCELED,
        'incomplete': SubscriptionStatus.TRIAL,
        'incomplete_expired': SubscriptionStatus.CANCELED,
        'trialing': SubscriptionStatus.TRIAL,
    }
    
    new_status = status_mapping.get(status)
    if not new_status:
        logger.warning(f"Statut Stripe inconnu: {status}")
        return
    
    # Mettre à jour l'organisation
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if organization:
        organization.subscription_status = new_status
        db.commit()
        logger.info(f"Organisation {organization_id} mise à jour: {new_status.value}")


async def handle_subscription_deleted(subscription: dict, db: Session):
    """
    Gérer l'annulation d'un abonnement.
    
    Met le statut de l'organisation à CANCELED.
    """
    subscription_id = subscription.get('id')
    
    # Récupérer l'organisation via les métadonnées
    metadata = subscription.get('metadata', {})
    organization_id = metadata.get('organization_id')
    
    if not organization_id:
        logger.warning(f"Pas d'organization_id dans les métadonnées de l'abonnement {subscription_id}")
        return
    
    # Mettre à jour l'organisation
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if organization:
        organization.subscription_status = SubscriptionStatus.CANCELED
        db.commit()
        logger.info(f"Organisation {organization_id} annulée")


async def handle_payment_succeeded(invoice: dict, db: Session):
    """
    Gérer un paiement réussi.
    
    S'assure que l'organisation est active.
    """
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    
    if not subscription_id:
        # Paiement unique, pas d'abonnement
        return
    
    # Récupérer l'abonnement pour avoir les métadonnées
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        metadata = subscription.get('metadata', {})
        organization_id = metadata.get('organization_id')
        
        if not organization_id:
            return
        
        # S'assurer que l'organisation est active
        organization = db.query(Organization).filter(Organization.id == organization_id).first()
        if organization and organization.subscription_status != SubscriptionStatus.ACTIVE:
            organization.subscription_status = SubscriptionStatus.ACTIVE
            db.commit()
            logger.info(f"Organisation {organization_id} réactivée après paiement réussi")
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'abonnement {subscription_id}: {str(e)}")


async def handle_payment_failed(invoice: dict, db: Session):
    """
    Gérer un paiement échoué.
    
    Suspend l'organisation après plusieurs échecs.
    """
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    attempt_count = invoice.get('attempt_count', 0)
    
    if not subscription_id:
        return
    
    # Récupérer l'abonnement pour avoir les métadonnées
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        metadata = subscription.get('metadata', {})
        organization_id = metadata.get('organization_id')
        
        if not organization_id:
            return
        
        # Suspendre après 3 tentatives échouées
        if attempt_count >= 3:
            organization = db.query(Organization).filter(Organization.id == organization_id).first()
            if organization:
                organization.subscription_status = SubscriptionStatus.SUSPENDED
                db.commit()
                logger.warning(f"Organisation {organization_id} suspendue après {attempt_count} échecs de paiement")
        else:
            logger.warning(f"Paiement échoué pour l'organisation {organization_id} (tentative {attempt_count}/3)")
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'abonnement {subscription_id}: {str(e)}")
