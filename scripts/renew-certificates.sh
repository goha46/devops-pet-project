#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR=/home/goha46

docker run --rm \
  -v "$DEPLOY_DIR/nginx/acme:/var/www/certbot" \
  -v "$DEPLOY_DIR/nginx/letsencrypt:/etc/letsencrypt" \
  certbot/certbot renew --non-interactive

docker compose -f "$DEPLOY_DIR/compose.deploy.yml" exec -T nginx nginx -t
docker compose -f "$DEPLOY_DIR/compose.deploy.yml" exec -T nginx nginx -s reload
