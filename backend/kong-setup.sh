#!/bin/bash
# Kong Admin API configuration script
# Run after Kong is up: ./kong-setup.sh
#
# This configures upstreams (with health checks) so Kong can
# load-balance across replicas that Docker Compose scales.

KONG_ADMIN="http://localhost:8001"

echo "Waiting for Kong Admin API..."
until curl -s "$KONG_ADMIN/status" > /dev/null 2>&1; do
  sleep 2
done
echo "Kong is ready."

# -------------------------------------------------------
# Helper: create upstream -> service -> route
# -------------------------------------------------------
setup_service() {
  local name=$1
  local host=$2   # Docker Compose service name
  local port=$3
  local path=$4   # route path prefix

  echo ""
  echo "=== Setting up: $name ==="

  # 1. Create upstream with health checks
  curl -s -X POST "$KONG_ADMIN/upstreams" \
    --data "name=${name}.upstream" \
    --data "healthchecks.active.http_path=/health" \
    --data "healthchecks.active.healthy.interval=10" \
    --data "healthchecks.active.unhealthy.interval=5" \
    --data "healthchecks.active.unhealthy.tcp_failures=3" \
    > /dev/null

  # 2. Add target (Docker DNS resolves to all replicas)
  curl -s -X POST "$KONG_ADMIN/upstreams/${name}.upstream/targets" \
    --data "target=${host}:${port}" \
    > /dev/null

  # 3. Create service pointing to upstream
  curl -s -X POST "$KONG_ADMIN/services" \
    --data "name=${name}" \
    --data "host=${name}.upstream" \
    --data "port=${port}" \
    > /dev/null

  # 4. Create route
  curl -s -X POST "$KONG_ADMIN/services/${name}/routes" \
    --data "name=${name}.route" \
    --data "paths[]=${path}" \
    --data "strip_path=false" \
    > /dev/null

  echo "  upstream: ${name}.upstream -> ${host}:${port}"
  echo "  route:    ${path}"
}

# -------------------------------------------------------
# Register all services
# -------------------------------------------------------

# Atomic services
setup_service "drug-catalogue"     "drug_service"         5001 "/drug"
setup_service "payment-service"    "payment_service"      5004 "/payments"

# Composite services
setup_service "prescribe-medicine" "prescribe_medicine"   5007 "/prescribe"
setup_service "make-payment"       "make_payment"         5008 "/make_payment"

# -------------------------------------------------------
# Enable Prometheus plugin globally
# -------------------------------------------------------
echo ""
echo "=== Enabling Prometheus plugin ==="
curl -s -X POST "$KONG_ADMIN/plugins" \
  --data "name=prometheus" \
  --data "config.status_code_metrics=true" \
  --data "config.latency_metrics=true" \
  --data "config.bandwidth_metrics=true" \
  --data "config.upstream_health_metrics=true" \
  > /dev/null
echo "  Prometheus plugin enabled globally"

echo ""
echo "Done. Kong routes configured."
echo "  Proxy:   http://localhost:8000"
echo "  Admin:   http://localhost:8001"
echo "  Manager: http://localhost:8002"
