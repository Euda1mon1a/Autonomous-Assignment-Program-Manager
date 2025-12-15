#!/bin/bash
# =============================================================================
# Let's Encrypt SSL Certificate Initialization Script
# =============================================================================
# This script initializes SSL certificates using Let's Encrypt/Certbot.
# Run this script once during initial deployment to obtain certificates.
#
# Usage: ./init-letsencrypt.sh [domain] [email] [staging]
#
# Arguments:
#   domain  - Your domain name (default: residency-scheduler.example.com)
#   email   - Email for Let's Encrypt notifications
#   staging - Set to 1 for staging certificates (testing)
# =============================================================================

set -e

# Configuration
DOMAIN="${1:-residency-scheduler.example.com}"
EMAIL="${2:-admin@example.com}"
STAGING="${3:-0}"

# Paths
NGINX_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_PATH="${NGINX_DIR}/certbot"
COMPOSE_FILE="${NGINX_DIR}/../docker-compose.yml"

# RSA key size
RSA_KEY_SIZE=4096

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}Let's Encrypt Certificate Initialization${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Staging: $STAGING"
echo ""

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}Note: You may need sudo permissions for Docker commands${NC}"
fi

# Create directories
echo -e "${YELLOW}Creating certificate directories...${NC}"
mkdir -p "$DATA_PATH/conf"
mkdir -p "$DATA_PATH/www"

# Check if certificates already exist
if [ -d "$DATA_PATH/conf/live/$DOMAIN" ]; then
    echo -e "${YELLOW}Existing certificate found for $DOMAIN${NC}"
    read -p "Do you want to replace it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificate."
        exit 0
    fi
fi

# Download recommended TLS parameters if not present
if [ ! -f "$DATA_PATH/conf/options-ssl-nginx.conf" ]; then
    echo -e "${YELLOW}Downloading recommended TLS parameters...${NC}"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf"
fi

if [ ! -f "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    echo -e "${YELLOW}Downloading DH parameters...${NC}"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem"
fi

# Create dummy certificate for nginx to start
echo -e "${YELLOW}Creating dummy certificate for initial nginx startup...${NC}"
DUMMY_PATH="$DATA_PATH/conf/live/$DOMAIN"
mkdir -p "$DUMMY_PATH"

openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE -days 1 \
    -keyout "$DUMMY_PATH/privkey.pem" \
    -out "$DUMMY_PATH/fullchain.pem" \
    -subj "/CN=localhost" 2>/dev/null

# Create chain.pem for OCSP stapling
cp "$DUMMY_PATH/fullchain.pem" "$DUMMY_PATH/chain.pem"

echo -e "${GREEN}Dummy certificate created${NC}"

# Start nginx with dummy certificate
echo -e "${YELLOW}Starting nginx with dummy certificate...${NC}"
docker compose -f "$COMPOSE_FILE" up --force-recreate -d nginx

# Wait for nginx to be ready
echo -e "${YELLOW}Waiting for nginx to start...${NC}"
sleep 5

# Delete dummy certificate
echo -e "${YELLOW}Removing dummy certificate...${NC}"
rm -rf "$DUMMY_PATH"

# Request real certificate
echo -e "${YELLOW}Requesting Let's Encrypt certificate...${NC}"

# Set staging flag if testing
STAGING_FLAG=""
if [ "$STAGING" != "0" ]; then
    STAGING_FLAG="--staging"
    echo -e "${YELLOW}Using staging environment (certificates will not be trusted)${NC}"
fi

# Run certbot
docker compose -f "$COMPOSE_FILE" run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    $STAGING_FLAG \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN"

# Check if certificate was obtained
if [ -f "$DATA_PATH/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${GREEN}Certificate obtained successfully!${NC}"
    echo -e "${GREEN}=============================================${NC}"

    # Reload nginx to use new certificate
    echo -e "${YELLOW}Reloading nginx with new certificate...${NC}"
    docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

    echo -e "${GREEN}Setup complete!${NC}"
    echo ""
    echo "Certificate location: $DATA_PATH/conf/live/$DOMAIN/"
    echo ""
    echo -e "${YELLOW}Important: Set up automatic renewal with:${NC}"
    echo "  ./renew-certificates.sh"
    echo ""
    echo "Or add a cron job:"
    echo "  0 0 * * * $(pwd)/renew-certificates.sh >> /var/log/certbot-renew.log 2>&1"
else
    echo -e "${RED}Certificate generation failed!${NC}"
    echo "Check the certbot logs for details."
    exit 1
fi
