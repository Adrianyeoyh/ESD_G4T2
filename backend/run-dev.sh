#!/bin/bash
# Development mode: exposes all service ports to host for direct access + Swagger docs.
#
# Production (Kong only):  docker compose up -d
# Development (all ports): ./run-dev.sh
# Development + rebuild:   ./run-dev.sh --build
#
# Swagger docs available at:
#   Drug Catalogue:    http://localhost:5001/docs
#   Invoice:           http://localhost:5003/docs
#   Payment:           http://localhost:5004/docs
#   Prescription:      http://localhost:5005/docs
#   Prescribe Medicine: http://localhost:5007  (Flask, no /docs)
#   Make Payment:       http://localhost:5008  (Flask, no /docs)
#
# Kong gateway still available at http://localhost:8000

exec docker compose -f docker-compose.yml -f docker-compose.dev.yml up "$@"
