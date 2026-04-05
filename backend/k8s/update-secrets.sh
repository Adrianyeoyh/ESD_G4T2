#!/bin/bash
# Updates K8s secrets from backend/.env.docker
# Usage: ./k8s/update-secrets.sh

set -e
NAMESPACE="clinicflow"
ENV_FILE="$(dirname "$0")/../.env.docker"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found. Copy from .env.docker.example and fill in values."
  exit 1
fi

# Source only KEY=VALUE lines (skip comments and Unicode)
eval "$(grep -E '^[A-Z_]+=.+' "$ENV_FILE" | sed 's/\r$//')"

echo "Updating K8s secrets from .env.docker..."

# Stripe credentials
kubectl create secret generic stripe-credentials \
  --from-literal=STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY}" \
  --from-literal=STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET}" \
  -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Twilio credentials
kubectl create secret generic twilio-credentials \
  --from-literal=TWILIO_ACCOUNT_SID="${TWILIO_ACCOUNT_SID}" \
  --from-literal=TWILIO_AUTH_TOKEN="${TWILIO_AUTH_TOKEN}" \
  --from-literal=TWILIO_PHONE_NUMBER="${TWILIO_PHONE_NUMBER}" \
  -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Internal API key
kubectl create secret generic internal-api-key \
  --from-literal=INTERNAL_API_KEY="${INTERNAL_API_KEY}" \
  -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets updated. Restarting services that use them..."

kubectl rollout restart deployment/payment-service -n "$NAMESPACE"
kubectl rollout restart deployment/make-payment -n "$NAMESPACE"
kubectl rollout restart deployment/notification-service -n "$NAMESPACE"

echo "Done. Wait for pods to restart:"
echo "  kubectl get pods -n $NAMESPACE -w"
