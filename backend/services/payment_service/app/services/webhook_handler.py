import stripe
from app.services import webhook_service


def process_webhook_event(payload: bytes, sig_header: str) -> None:
    """Handle raw Stripe webhook payloads and map them to service-level events."""
    try:
        webhook_service.handle_webhook_event(payload, sig_header)
    except stripe.error.SignatureVerificationError as exc:
        raise ValueError(f"Invalid Stripe signature: {exc}")
    except stripe.error.StripeError as exc:
        raise RuntimeError(f"Stripe service error: {exc.user_message or str(exc)}")
    except Exception as exc:
        raise RuntimeError(f"Unhandled webhook processing error: {exc}")
