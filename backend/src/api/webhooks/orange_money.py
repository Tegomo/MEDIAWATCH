"""Webhook handler pour les notifications Orange Money"""
from fastapi import APIRouter, Request, HTTPException, status

from src.services.payments.orange_money_service import OrangeMoneyService
from src.lib.logger import logger

router = APIRouter(prefix="/webhooks/orange-money", tags=["Webhooks"])


@router.post("/callback")
async def orange_money_callback(request: Request):
    """
    Endpoint de callback Orange Money.
    Reçoit les notifications de paiement (succès, échec, annulation).
    """
    try:
        body = await request.body()
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Vérifier la signature si présente
    signature = request.headers.get("X-Signature", "")
    om_service = OrangeMoneyService()

    if signature and not om_service.verify_webhook_signature(body, signature):
        logger.warning("Orange Money webhook: signature invalide")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parser l'événement
    event = om_service.parse_webhook_event(data)
    logger.info(f"Orange Money webhook: {event['event_type']} order={event['order_id']}")

    # Traiter selon le type d'événement
    if event["event_type"] == "payment_succeeded":
        await _handle_payment_success(event)
    elif event["event_type"] == "payment_failed":
        await _handle_payment_failed(event)
    elif event["event_type"] == "payment_canceled":
        await _handle_payment_canceled(event)
    else:
        logger.warning(f"Orange Money webhook: événement inconnu {event['event_type']}")

    return {"status": "ok"}


async def _handle_payment_success(event: dict):
    """Traite un paiement réussi."""
    logger.info(
        f"Orange Money paiement réussi: order={event['order_id']} "
        f"amount={event['amount']} {event['currency']}"
    )
    # TODO: Activer/renouveler l'abonnement de l'organisation
    # basé sur event['order_id'] qui contient l'ID de l'organisation


async def _handle_payment_failed(event: dict):
    """Traite un paiement échoué."""
    logger.warning(f"Orange Money paiement échoué: order={event['order_id']}")


async def _handle_payment_canceled(event: dict):
    """Traite un paiement annulé."""
    logger.info(f"Orange Money paiement annulé: order={event['order_id']}")
