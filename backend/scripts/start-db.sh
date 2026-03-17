#!/bin/bash

# docker run --name esd-postgres \
#   -e POSTGRES_USER=clinic \
#   -e POSTGRES_PASSWORD=clinic \
#   -e POSTGRES_DB=esd_db \
#   -p 5432:5432 \
#   -v esd_pgdata:/var/lib/postgresql/data \
#   -v "$(pwd)/backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql" \
#   -d postgres:16


set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

docker run --name esd-postgres \
  -e POSTGRES_USER=clinic \
  -e POSTGRES_PASSWORD=clinic \
  -e POSTGRES_DB=esd_db \
  -p 5432:5432 \
  -v esd_pgdata:/var/lib/postgresql/data \
  -v "$BACKEND_DIR/db:/docker-entrypoint-initdb.d:ro" \
  -d postgres:16