import stripe
from decimal import Decimal, ROUND_HALF_UP
from app.config.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY


def create_payment_intent(
    amount: Decimal,
    currency: str,
    description: str,
    metadata: dict | None = None,
    payment_method: str | None = None,
    confirm: bool = False,
) -> stripe.PaymentIntent:
    """Create a Stripe PaymentIntent.

    Amount is in major currency units (e.g. SGD dollars).
    Converted to the smallest unit (cents) using Decimal arithmetic to avoid
    floating-point precision errors in financial calculations.

    metadata: includes invoice_id and attempt_number for reconciliation.
    """
    if not stripe.api_key:
        raise ValueError("Stripe API key is not configured")

    amount_cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
    payload = {
        "amount": amount_cents,
        "currency": currency.lower(),
        "description": description,
        "payment_method_types": ["card"],
        "metadata": metadata or {},
        "confirm": confirm,
    }
    if payment_method:
        payload["payment_method"] = payment_method
    return stripe.PaymentIntent.create(
        **payload,
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
