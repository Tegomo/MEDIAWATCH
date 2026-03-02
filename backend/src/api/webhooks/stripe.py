"""Webhook handler pour les événements Stripe"""
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends, Header

from src.config import settings
from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.lib.logger import logger

router = APIRouter(prefix="/webhooks/stripe", tags=["Webhooks"])


@router.post("")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: SupabaseDB = Depends(get_db),
):
    """Gérer les événements webhook de Stripe."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe non configuré")

    payload = await request.body()

    try:
        import stripe
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except Exception as e:
        logger.error(f"Erreur de vérification du webhook Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event['type']
    event_data = event['data']['object']
    logger.info(f"Événement Stripe reçu: {event_type}")

    try:
        metadata = event_data.get('metadata', {})
        organization_id = metadata.get('organization_id')

        if not organization_id:
            # Try to get from subscription
            sub_id = event_data.get('subscription')
            if sub_id:
                try:
                    sub = stripe.Subscription.retrieve(sub_id)
                    organization_id = sub.get('metadata', {}).get('organization_id')
                except Exception:
                    pass

        if not organization_id:
            logger.warning(f"Pas d'organization_id pour l'événement {event_type}")
            return {"status": "skipped"}

        now = datetime.utcnow().isoformat()
        status_map = {
            'customer.subscription.created': 'ACTIVE',
            'customer.subscription.deleted': 'CANCELED',
            'invoice.payment_succeeded': 'ACTIVE',
        }

        if event_type in status_map:
            db.update("organizations", {
                "subscription_status": status_map[event_type],
                "updated_at": now,
            }, id=f"eq.{organization_id}")

        elif event_type == 'customer.subscription.updated':
            stripe_status = event_data.get('status', '')
            mapping = {
                'active': 'ACTIVE', 'past_due': 'ACTIVE',
                'unpaid': 'SUSPENDED', 'canceled': 'CANCELED',
                'incomplete': 'TRIAL', 'incomplete_expired': 'CANCELED',
                'trialing': 'TRIAL',
            }
            new_status = mapping.get(stripe_status)
            if new_status:
                db.update("organizations", {
                    "subscription_status": new_status,
                    "updated_at": now,
                }, id=f"eq.{organization_id}")

        elif event_type == 'invoice.payment_failed':
            attempt_count = event_data.get('attempt_count', 0)
            if attempt_count >= 3:
                db.update("organizations", {
                    "subscription_status": "SUSPENDED",
                    "updated_at": now,
                }, id=f"eq.{organization_id}")

    except Exception as e:
        logger.error(f"Erreur traitement événement {event_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success"}
