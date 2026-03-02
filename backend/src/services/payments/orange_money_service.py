"""Service de paiement Orange Money pour la Côte d'Ivoire"""
import hashlib
import hmac
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx

from src.config import settings
from src.lib.logger import logger


class OrangeMoneyError(Exception):
    """Erreur spécifique Orange Money"""
    pass


class OrangeMoneyService:
    """
    Intégration API Orange Money CI.
    Gère l'initiation de paiements, la vérification de statut,
    et le traitement des callbacks webhook.
    """

    def __init__(self):
        self.api_key = settings.orange_money_api_key
        self.merchant_key = settings.orange_money_merchant_key
        self.api_url = settings.orange_money_api_url or "https://api.orange.com/orange-money-webpay/dev/v1"
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        """Vérifie si Orange Money est configuré."""
        return bool(self.api_key and self.merchant_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Retourne un client HTTP configuré."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def initiate_payment(
        self,
        amount: int,
        currency: str = "XOF",
        order_id: str = "",
        description: str = "Abonnement MediaWatch CI",
        customer_phone: Optional[str] = None,
        return_url: str = "",
        cancel_url: str = "",
        notification_url: str = "",
    ) -> dict:
        """
        Initie un paiement Orange Money.
        Retourne l'URL de paiement et l'identifiant de transaction.
        """
        if not self.is_configured:
            raise OrangeMoneyError("Orange Money non configuré")

        payload = {
            "merchant_key": self.merchant_key,
            "currency": currency,
            "order_id": order_id,
            "amount": amount,
            "return_url": return_url,
            "cancel_url": cancel_url,
            "notif_url": notification_url,
            "lang": "fr",
        }

        if customer_phone:
            payload["reference"] = customer_phone

        try:
            client = await self._get_client()
            response = await client.post("/webpayment", json=payload)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Orange Money payment initiated: order={order_id}, amount={amount} {currency}")

            return {
                "payment_url": data.get("payment_url", ""),
                "payment_token": data.get("pay_token", ""),
                "transaction_id": data.get("txnid", order_id),
                "status": "pending",
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Orange Money API error: {e.response.status_code} - {e.response.text}")
            raise OrangeMoneyError(f"Erreur API Orange Money: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Orange Money error: {str(e)}")
            raise OrangeMoneyError(f"Erreur Orange Money: {str(e)}")

    async def check_payment_status(self, payment_token: str, order_id: str) -> dict:
        """Vérifie le statut d'un paiement Orange Money."""
        if not self.is_configured:
            raise OrangeMoneyError("Orange Money non configuré")

        try:
            client = await self._get_client()
            response = await client.post(
                f"/transactionstatus",
                json={
                    "order_id": order_id,
                    "pay_token": payment_token,
                },
            )
            response.raise_for_status()
            data = response.json()

            status_map = {
                "SUCCESS": "succeeded",
                "FAILED": "failed",
                "PENDING": "pending",
                "CANCELLED": "canceled",
                "EXPIRED": "expired",
            }

            om_status = data.get("status", "PENDING")
            return {
                "status": status_map.get(om_status, "pending"),
                "raw_status": om_status,
                "transaction_id": data.get("txnid", ""),
                "amount": data.get("amount"),
                "currency": data.get("currency", "XOF"),
            }

        except Exception as e:
            logger.error(f"Orange Money status check error: {str(e)}")
            return {"status": "pending", "error": str(e)}

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Vérifie la signature d'un webhook Orange Money."""
        if not self.merchant_key:
            return False
        expected = hmac.new(
            self.merchant_key.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_webhook_event(self, data: dict) -> dict:
        """Parse un événement webhook Orange Money."""
        status_map = {
            "SUCCESS": "payment_succeeded",
            "FAILED": "payment_failed",
            "CANCELLED": "payment_canceled",
        }

        om_status = data.get("status", "")
        return {
            "event_type": status_map.get(om_status, "unknown"),
            "order_id": data.get("order_id", ""),
            "transaction_id": data.get("txnid", ""),
            "amount": data.get("amount"),
            "currency": data.get("currency", "XOF"),
            "status": om_status,
            "raw_data": data,
        }

    async def close(self):
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
