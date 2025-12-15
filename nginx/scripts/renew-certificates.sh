***REMOVED***!/bin/bash
***REMOVED*** =============================================================================
***REMOVED*** Let's Encrypt Certificate Renewal Script
***REMOVED*** =============================================================================
***REMOVED*** This script renews SSL certificates and reloads nginx.
***REMOVED*** Set up as a cron job to run daily or twice daily.
***REMOVED***
***REMOVED*** Cron example (run twice daily at 3:30 AM and 3:30 PM):
***REMOVED***   30 3,15 * * * /path/to/renew-certificates.sh >> /var/log/certbot-renew.log 2>&1
***REMOVED*** =============================================================================

set -e

***REMOVED*** Paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NGINX_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$NGINX_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

***REMOVED*** Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' ***REMOVED*** No Color

echo "============================================="
echo "Certificate Renewal - $(date)"
echo "============================================="

***REMOVED*** Change to project root for docker compose
cd "$PROJECT_ROOT"

***REMOVED*** Attempt renewal
echo "Attempting certificate renewal..."
docker compose -f "$COMPOSE_FILE" run --rm certbot renew --quiet

***REMOVED*** Check renewal result
RENEWAL_STATUS=$?

if [ $RENEWAL_STATUS -eq 0 ]; then
    echo -e "${GREEN}Certificate renewal check completed successfully${NC}"

    ***REMOVED*** Reload nginx to apply any renewed certificates
    echo "Reloading nginx..."
    docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Nginx reloaded successfully${NC}"
    else
        echo -e "${RED}Warning: Failed to reload nginx${NC}"
        ***REMOVED*** Don't exit with error - nginx might not be running yet
    fi
else
    echo -e "${RED}Certificate renewal failed with status: $RENEWAL_STATUS${NC}"
    exit 1
fi

echo "Renewal process completed at $(date)"
