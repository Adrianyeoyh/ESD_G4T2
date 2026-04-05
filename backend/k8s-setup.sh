#!/bin/bash
# Kubernetes deployment script for ClinicFlow
# Prerequisites: Docker Desktop with Kubernetes enabled, images built locally
#
# Usage:
#   ./k8s-setup.sh          # Deploy everything
#   ./k8s-setup.sh teardown # Remove everything

set -e

NAMESPACE="clinicflow"

# -------------------------------------------------------
# Teardown mode
# -------------------------------------------------------
if [ "$1" = "teardown" ]; then
  echo "Tearing down ClinicFlow from Kubernetes..."
  kubectl delete -f k8s/ --ignore-not-found 2>/dev/null
  echo "Done. All resources removed."
  exit 0
fi

# -------------------------------------------------------
# Pre-flight checks
# -------------------------------------------------------
echo "=== ClinicFlow K8s Setup ==="
echo ""

if ! command -v kubectl &> /dev/null; then
  echo "ERROR: kubectl not found. Enable Kubernetes in Docker Desktop first."
  exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
  echo "ERROR: Cannot connect to Kubernetes cluster."
  echo "Enable Kubernetes in Docker Desktop > Settings > Kubernetes."
  exit 1
fi

echo "Cluster is reachable."

# -------------------------------------------------------
# Step 1: Build Docker images
# -------------------------------------------------------
echo ""
echo "=== Step 1: Building Docker images ==="
docker compose build --quiet
echo "  Images built."

# -------------------------------------------------------
# Step 2: Create namespace
# -------------------------------------------------------
echo ""
echo "=== Step 2: Creating namespace ==="
kubectl apply -f k8s/namespace.yml
echo "  Namespace '$NAMESPACE' ready."

# -------------------------------------------------------
# Step 3: Deploy secrets and infrastructure
# -------------------------------------------------------
echo ""
echo "=== Step 3: Deploying secrets & infrastructure ==="
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/rabbitmq.yml

echo "  Waiting for Postgres to be ready..."
kubectl rollout status statefulset/postgres -n $NAMESPACE --timeout=120s

echo "  Waiting for RabbitMQ to be ready..."
kubectl rollout status deployment/rabbitmq -n $NAMESPACE --timeout=180s

# -------------------------------------------------------
# Step 4: Deploy atomic services
# -------------------------------------------------------
echo ""
echo "=== Step 4: Deploying atomic services ==="
kubectl apply -f k8s/drug-service.yml
kubectl apply -f k8s/invoice-service.yml
kubectl apply -f k8s/prescription-service.yml
kubectl apply -f k8s/payment-service.yml

echo "  Waiting for services to be ready..."
kubectl rollout status deployment/drug-service -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/invoice-service -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/prescription-service -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/payment-service -n $NAMESPACE --timeout=120s

# -------------------------------------------------------
# Step 5: Deploy composite services
# -------------------------------------------------------
echo ""
echo "=== Step 5: Deploying composite services ==="
kubectl apply -f k8s/prescribe-medicine.yml
kubectl apply -f k8s/make-payment.yml

kubectl rollout status deployment/prescribe-medicine -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/make-payment -n $NAMESPACE --timeout=120s

# -------------------------------------------------------
# Step 6: Deploy Kong API Gateway
# -------------------------------------------------------
echo ""
echo "=== Step 6: Deploying Kong ==="
kubectl apply -f k8s/kong.yml

kubectl rollout status deployment/kong -n $NAMESPACE --timeout=120s

# -------------------------------------------------------
# Step 7: Deploy monitoring (Prometheus + Grafana)
# -------------------------------------------------------
echo ""
echo "=== Step 7: Deploying monitoring ==="
kubectl apply -f k8s/prometheus.yml
kubectl apply -f k8s/grafana.yml

kubectl rollout status deployment/prometheus -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/grafana -n $NAMESPACE --timeout=120s

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
echo ""
echo "========================================="
echo "  ClinicFlow deployed successfully!"
echo "========================================="
echo ""
echo "  Services:"
kubectl get svc -n $NAMESPACE --no-headers | awk '{printf "    %-25s %s\n", $1, $5}'
echo ""
echo "  Access points:"
echo "    Kong Proxy:   http://localhost:8000"
echo "    Kong Admin:   http://localhost:8001"
echo "    Prometheus:   http://localhost:9090"
echo "    Grafana:      http://localhost:3000"
echo "    RabbitMQ UI:  http://localhost:15672"
echo ""
echo "  Useful commands:"
echo "    kubectl get pods -n $NAMESPACE          # List pods"
echo "    kubectl get hpa -n $NAMESPACE           # Auto-scaler status"
echo "    kubectl logs -n $NAMESPACE -l app=<svc> # Service logs"
echo "    ./k8s-setup.sh teardown                 # Remove everything"
