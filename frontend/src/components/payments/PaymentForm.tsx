import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js'

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      '::placeholder': {
        color: '#aab7c4',
      },
    },
    invalid: {
      color: '#9e2146',
    },
  },
}

export default function PaymentForm() {
  const stripe = useStripe()
  const elements = useElements()

  if (!stripe || !elements) {
    return (
      <div className="space-y-4">
        <div className="rounded-md border p-4">
          <p className="text-sm text-muted-foreground">
            Paiement Stripe - Mode test
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Le paiement sera configuré après la création du compte.
            Vous bénéficiez de 14 jours d'essai gratuit.
          </p>
        </div>
        <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-700">
          Période d'essai gratuite de 14 jours. Aucune carte requise pour commencer.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border p-4">
        <CardElement options={CARD_ELEMENT_OPTIONS} />
      </div>
      <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-700">
        Période d'essai gratuite de 14 jours. Vous ne serez pas débité immédiatement.
      </div>
    </div>
  )
}
