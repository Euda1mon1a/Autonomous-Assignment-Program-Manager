***REMOVED***!/bin/bash
***REMOVED*** =============================================================================
***REMOVED*** Diffie-Hellman Parameters Generation Script
***REMOVED*** =============================================================================
***REMOVED*** Generates strong DH parameters for SSL/TLS.
***REMOVED*** This can take several minutes to complete.
***REMOVED***
***REMOVED*** Usage: ./generate-dhparam.sh [keysize]
***REMOVED***   keysize - DH parameter size (default: 4096)
***REMOVED*** =============================================================================

set -e

***REMOVED*** Configuration
KEYSIZE="${1:-4096}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/../ssl"
OUTPUT_FILE="${SSL_DIR}/dhparam.pem"

***REMOVED*** Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}Diffie-Hellman Parameters Generator${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "Key size: $KEYSIZE bits"
echo "Output: $OUTPUT_FILE"
echo ""

***REMOVED*** Create SSL directory if not exists
mkdir -p "$SSL_DIR"

***REMOVED*** Check if file already exists
if [ -f "$OUTPUT_FILE" ]; then
    echo -e "${YELLOW}DH parameters file already exists.${NC}"
    read -p "Do you want to regenerate? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing DH parameters."
        exit 0
    fi
fi

echo -e "${YELLOW}Generating DH parameters (this may take several minutes)...${NC}"
echo ""

***REMOVED*** Generate DH parameters
openssl dhparam -out "$OUTPUT_FILE" "$KEYSIZE"

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${GREEN}DH parameters generated successfully!${NC}"
    echo "File: $OUTPUT_FILE"

    ***REMOVED*** Set proper permissions
    chmod 644 "$OUTPUT_FILE"
else
    echo "Failed to generate DH parameters"
    exit 1
fi
