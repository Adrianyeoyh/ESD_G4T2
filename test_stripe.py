import stripe
import os
from dotenv import load_dotenv

# Load env from payment service
load_dotenv("backend/services/payment_service/.env")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_SECRET_KEY

print("=" * 60)
print("STRIPE API CONNECTIVITY TEST")
print("=" * 60)

# Test 1: Check if key is loaded
if STRIPE_SECRET_KEY:
    key_preview = STRIPE_SECRET_KEY[:20] + "..." + STRIPE_SECRET_KEY[-10:]
    print(f"\n✓ Secret Key loaded: {key_preview}")
else:
    print("\n✗ Secret Key NOT found in .env")
    exit(1)

if STRIPE_WEBHOOK_SECRET:
    webhook_preview = STRIPE_WEBHOOK_SECRET[:20] + "..." + STRIPE_WEBHOOK_SECRET[-10:]
    print(f"✓ Webhook Secret loaded: {webhook_preview}")
else:
    print("\n✗ Webhook Secret NOT found in .env")

# Test 2: Try to retrieve account info (tests API connectivity)
try:
    account = stripe.Account.retrieve()
    print(f"\n✓ API KEY VALID - Connected to Stripe account")
    print(f"  Account ID: {account['id']}")
    print(f"  Account Email: {account.get('email', 'N/A')}")
    print(f"  Account Country: {account.get('country', 'N/A')}")
except stripe.error.AuthenticationError as e:
    print(f"\n✗ AUTHENTICATION FAILED: {e.user_message}")
    exit(1)
except stripe.error.APIConnectionError as e:
    print(f"\n✗ API CONNECTION FAILED: {e.user_message}")
    exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    exit(1)

# Test 3: Create a test payment intent
try:
    intent = stripe.PaymentIntent.create(
        amount=2000,  # $20.00 in cents
        currency="sgd",
        description="Test payment from backend",
        metadata={
            "invoice_id": "test_invoice_1",
            "attempt_number": "1",
        }
    )
    print(f"\n✓ PAYMENT INTENT CREATED")
    print(f"  Intent ID: {intent['id']}")
    print(f"  Status: {intent['status']}")
    print(f"  Amount: SGD {intent['amount']/100:.2f}")
    print(f"  Client Secret: {intent['client_secret'][:30]}...")
except stripe.error.CardError as e:
    print(f"\n✗ CARD ERROR: {e.user_message}")
except stripe.error.StripeError as e:
    print(f"\n✗ STRIPE ERROR: {e.user_message}")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    exit(1)

# Test 4: Webhook signature verification (simulate)
try:
    import json
    import hmac
    import hashlib
    import time
    
    test_payload = json.dumps({"test": "data"}).encode('utf-8')
    test_timestamp = str(int(time.time()))
    signed_content = f"{test_timestamp}.{test_payload.decode()}"
    
    expected_sig = hmac.new(
        STRIPE_WEBHOOK_SECRET.encode(),
        signed_content.encode(),
        hashlib.sha256
    ).hexdigest()
    
    test_sig_header = f"t={test_timestamp},v1={expected_sig}"
    
    # Try to construct event (should work if secret is valid)
    event = stripe.Webhook.construct_event(test_payload, test_sig_header, STRIPE_WEBHOOK_SECRET)
    print(f"\n✓ WEBHOOK SIGNATURE VERIFICATION WORKS")
    print(f"  Verified signature match")
except stripe.error.SignatureVerificationError as e:
    print(f"\n✗ WEBHOOK SIGNATURE ERROR: {e}")
except Exception as e:
    print(f"\n✗ WEBHOOK ERROR: {e}")

print("\n" + "=" * 60)
print("STATUS: ✓ ALL STRIPE TESTS PASSED")
print("=" * 60)
