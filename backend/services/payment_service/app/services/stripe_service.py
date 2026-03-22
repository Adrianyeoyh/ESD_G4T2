import stripe
from app.config.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY


def create_payment_intent(amount_sgd: float, currency: str, description: str) -> stripe.PaymentIntent:
    """Create a Stripe PaymentIntent. Amount is in SGD (dollars); converted to cents internally."""
    amount_cents = int(round(amount_sgd * 100))
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency.lower(),
        description=description,
        payment_method_types=["card"],
    )


def cancel_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    """Cancel an existing Stripe PaymentIntent."""
    return stripe.PaymentIntent.cancel(payment_intent_id)


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify Stripe webhook signature and return the parsed event.

    Raises:
        stripe.error.SignatureVerificationError: if the signature is invalid.
        ValueError: if the payload cannot be parsed.
    """
    return stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
