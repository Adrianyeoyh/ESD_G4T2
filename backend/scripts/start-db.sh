#!/bin/bash

docker run --name esd-postgres \
  -e POSTGRES_USER=clinic \
  -e POSTGRES_PASSWORD=clinic \
  -e POSTGRES_DB=esd_db \
  -p 5432:5432 \
  -v esd_pgdata:/var/lib/postgresql/data \
  -v "$(pwd)/backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql" \
  -d postgres:16