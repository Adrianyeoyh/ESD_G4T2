#!/bin/bash

docker stop esd-postgres || true
docker rm esd-postgres || true