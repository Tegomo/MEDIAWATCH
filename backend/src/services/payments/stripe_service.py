"""Service de paiement Stripe pour MediaWatch CI"""
from typing import Optional, Dict, Any
from datetime import datetime
import stripe

from src.config import settings
from src.models.organization import SubscriptionPlan

# Configuration Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service pour gérer les paiements Stripe"""
    
    # Prix mensuels par plan (en centimes)
    PLAN_PRICES = {
        SubscriptionPlan.BASIC: 2500,      # 25€/mois
        SubscriptionPlan.PRO: 9900,        # 99€/mois
        SubscriptionPlan.ENTERPRISE: 29900,  # 299€/mois
    }
    
    @staticmethod
    def create_customer(email: str, name: str, metadata: Optional[Dict[str, str]] = None) -> stripe.Customer:
        """
        Créer un client Stripe.
        
        Args:
            email: Email du client
            name: Nom du client
            metadata: Métadonnées additionnelles
            
        Returns:
            Customer Stripe créé
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de la création du client: {str(e)}")
    
    @staticmethod
    def attach_payment_method(
        customer_id: str,
        payment_method_id: str
    ) -> stripe.PaymentMethod:
        """
        Attacher un moyen de paiement à un client.
        
        Args:
            customer_id: ID du client Stripe
            payment_method_id: ID du moyen de paiement
            
        Returns:
            PaymentMethod attaché
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            # Définir comme moyen de paiement par défaut
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id,
                },
            )
            
            return payment_method
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de l'attachement du moyen de paiement: {str(e)}")
    
    @staticmethod
    def create_subscription(
        customer_id: str,
        plan: SubscriptionPlan,
        trial_days: int = 14,
        metadata: Optional[Dict[str, str]] = None
    ) -> stripe.Subscription:
        """
        Créer un abonnement Stripe.
        
        Args:
            customer_id: ID du client Stripe
            plan: Plan d'abonnement
            trial_days: Nombre de jours de période d'essai
            metadata: Métadonnées additionnelles
            
        Returns:
            Subscription Stripe créée
        """
        try:
            # Créer ou récupérer le prix pour ce plan
            price = StripeService._get_or_create_price(plan)
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price.id}],
                trial_period_days=trial_days,
                metadata=metadata or {},
                payment_behavior='default_incomplete',
                payment_settings={
                    'save_default_payment_method': 'on_subscription'
                },
                expand=['latest_invoice.payment_intent'],
            )
            
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de la création de l'abonnement: {str(e)}")
    
    @staticmethod
    def cancel_subscription(subscription_id: str, immediately: bool = False) -> stripe.Subscription:
        """
        Annuler un abonnement.
        
        Args:
            subscription_id: ID de l'abonnement
            immediately: Si True, annule immédiatement. Sinon, à la fin de la période
            
        Returns:
            Subscription annulée
        """
        try:
            if immediately:
                subscription = stripe.Subscription.cancel(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de l'annulation de l'abonnement: {str(e)}")
    
    @staticmethod
    def change_subscription_plan(
        subscription_id: str,
        new_plan: SubscriptionPlan
    ) -> stripe.Subscription:
        """
        Changer le plan d'un abonnement existant.
        
        Args:
            subscription_id: ID de l'abonnement
            new_plan: Nouveau plan
            
        Returns:
            Subscription modifiée
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            new_price = StripeService._get_or_create_price(new_plan)
            
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price.id,
                }],
                proration_behavior='create_prorations',
            )
            
            return updated_subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors du changement de plan: {str(e)}")
    
    @staticmethod
    def create_payment_intent(
        amount: int,
        currency: str = "eur",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> stripe.PaymentIntent:
        """
        Créer un PaymentIntent pour un paiement unique.
        
        Args:
            amount: Montant en centimes
            currency: Devise (eur par défaut)
            customer_id: ID du client Stripe (optionnel)
            metadata: Métadonnées additionnelles
            
        Returns:
            PaymentIntent créé
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de la création du PaymentIntent: {str(e)}")
    
    @staticmethod
    def _get_or_create_price(plan: SubscriptionPlan) -> stripe.Price:
        """
        Récupérer ou créer un prix Stripe pour un plan.
        
        Args:
            plan: Plan d'abonnement
            
        Returns:
            Price Stripe
        """
        try:
            # Chercher un prix existant
            prices = stripe.Price.list(
                active=True,
                lookup_keys=[f"mediawatch_{plan.value}"],
                limit=1,
            )
            
            if prices.data:
                return prices.data[0]
            
            # Créer le prix s'il n'existe pas
            product = StripeService._get_or_create_product()
            price = stripe.Price.create(
                product=product.id,
                unit_amount=StripeService.PLAN_PRICES[plan],
                currency='eur',
                recurring={'interval': 'month'},
                lookup_key=f"mediawatch_{plan.value}",
                metadata={'plan': plan.value},
            )
            
            return price
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de la récupération/création du prix: {str(e)}")
    
    @staticmethod
    def _get_or_create_product() -> stripe.Product:
        """
        Récupérer ou créer le produit MediaWatch CI dans Stripe.
        
        Returns:
            Product Stripe
        """
        try:
            # Chercher le produit existant
            products = stripe.Product.list(
                active=True,
                limit=1,
            )
            
            for product in products.data:
                if product.name == "MediaWatch CI":
                    return product
            
            # Créer le produit s'il n'existe pas
            product = stripe.Product.create(
                name="MediaWatch CI",
                description="Plateforme de veille médiatique pour la Côte d'Ivoire",
                metadata={'app': 'mediawatch-ci'},
            )
            
            return product
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe lors de la récupération/création du produit: {str(e)}")
    
    @staticmethod
    def construct_webhook_event(
        payload: bytes,
        sig_header: str,
        webhook_secret: str
    ) -> stripe.Event:
        """
        Construire et vérifier un événement webhook Stripe.
        
        Args:
            payload: Corps de la requête (bytes)
            sig_header: Header Stripe-Signature
            webhook_secret: Secret du webhook
            
        Returns:
            Event Stripe vérifié
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError:
            raise Exception("Payload invalide")
        except stripe.error.SignatureVerificationError:
            raise Exception("Signature invalide")
