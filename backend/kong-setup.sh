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
  local target="${host}:${port}"

  echo ""
  echo "=== Setting up: $name ==="

  # 1. Upsert upstream with active checks effectively disabled (idempotent)
  curl -s -X PUT "$KONG_ADMIN/upstreams/${name}.upstream" \
    --data "healthchecks.active.healthy.interval=0" \
    > /dev/null

  # 2. Add target only if not present (prevents duplicate target entries)
  if ! curl -s "$KONG_ADMIN/upstreams/${name}.upstream/targets" | grep -q "\"target\":\"${target}\""; then
    curl -s -X POST "$KONG_ADMIN/upstreams/${name}.upstream/targets" \
      --data "target=${target}" \
      > /dev/null
  fi

  # 3. Upsert service pointing to upstream
  curl -s -X PUT "$KONG_ADMIN/services/${name}" \
    --data "host=${name}.upstream" \
    --data "port=${port}" \
    > /dev/null

  # 4. Upsert route
  curl -s -X PUT "$KONG_ADMIN/services/${name}/routes/${name}.route" \
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
setup_service "drug-catalogue"     "drug_catalogue_service" 5001 "/drug"
setup_service "invoice-service"    "invoice_service"        5003 "/invoice"
setup_service "payment-service"    "payment_service"        5004 "/payments"

# Composite services
setup_service "prescribe-medicine" "prescribe_medicine"     5007 "/prescribe"
setup_service "make-payment"       "make_payment"           5008 "/make_payment"

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
