#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:?domain required}"
EMAIL="${2:?email required}"
DIR="$HOME/faserkraft-website-api/deploy/nginx"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

if ! command -v nginx >/dev/null || ! command -v certbot >/dev/null; then
  $SUDO apt-get update
  $SUDO apt-get install -y nginx certbot
fi

$SUDO mkdir -p /var/www/certbot
$SUDO rm -f /etc/nginx/sites-enabled/default

apply() {
  $SUDO cp "$1" /etc/nginx/sites-available/faserkraft-api
  $SUDO ln -sf /etc/nginx/sites-available/faserkraft-api /etc/nginx/sites-enabled/faserkraft-api
  $SUDO nginx -t
  $SUDO systemctl reload nginx
}

if ! $SUDO test -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
  apply "$DIR/bootstrap.conf"
  $SUDO certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" \
    --agree-tos -m "$EMAIL" --no-eff-email --non-interactive \
    --deploy-hook "systemctl reload nginx"
fi

apply "$DIR/faserkraft.conf"