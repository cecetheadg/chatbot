#!/bin/bash

# ============================================
# Stop Traefik Reverse Proxy
# Chatbot L0027 - Standalone Traefik
# ============================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Stopping Traefik Reverse Proxy${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Parse command line arguments
REMOVE_VOLUMES=false
REMOVE_NETWORK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes|-v)
            REMOVE_VOLUMES=true
            shift
            ;;
        --network|-n)
            REMOVE_NETWORK=true
            shift
            ;;
        --all|-a)
            REMOVE_VOLUMES=true
            REMOVE_NETWORK=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./stop-traefik.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes    Remove Traefik volumes (logs, letsencrypt)"
            echo "  -n, --network    Remove shared network (⚠️  removes network used by chatbot services)"
            echo "  -a, --all        Remove volumes and network"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Traefik is running
if ! docker compose -f docker-compose.traefik.yml ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Traefik is not running${NC}"
    exit 0
fi

# Stop Traefik
echo -e "${BLUE}🛑 Stopping Traefik...${NC}"
if [ "$REMOVE_VOLUMES" = true ]; then
    docker compose -f docker-compose.traefik.yml down -v
    echo -e "${YELLOW}⚠️  Traefik volumes removed (logs and SSL certificates)${NC}"
else
    docker compose -f docker-compose.traefik.yml down
fi

# Remove network if requested
if [ "$REMOVE_NETWORK" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Removing shared network...${NC}"
    echo -e "${RED}⚠️  WARNING: This will affect chatbot services if they are running!${NC}"
    read -p "Continue? (yes/N) " -r
    echo
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        docker network rm chatbot_l0027_network 2>/dev/null || true
        echo -e "${GREEN}✅ Network removed${NC}"
    else
        echo -e "${YELLOW}Network removal cancelled${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Traefik Stopped${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}ℹ️  Note:${NC}"
echo "   • Traefik configuration is preserved"
echo "   • SSL certificates are preserved (unless --volumes was used)"
echo "   • Network is preserved (unless --network was used)"
echo ""

