#!/bin/bash

# ============================================
# Start Traefik Reverse Proxy
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
echo -e "${CYAN}Starting Traefik Reverse Proxy${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Error: docker compose is not installed${NC}"
    exit 1
fi

# Check network configuration
echo -e "${BLUE}🌐 Checking network configuration...${NC}"
# Check if network exists from a previous manual creation or different compose project
if docker network inspect chatbot_l0027_network >/dev/null 2>&1; then
    # Check if network was created by this compose project
    PROJECT_LABEL=$(docker network inspect chatbot_l0027_network --format '{{index .Labels "com.docker.compose.project"}}' 2>/dev/null || echo "")
    NETWORK_LABEL=$(docker network inspect chatbot_l0027_network --format '{{index .Labels "com.docker.compose.network"}}' 2>/dev/null || echo "")
    
    # If network exists but with wrong labels, we need to remove it first
    if [ -n "$PROJECT_LABEL" ] && [ "$PROJECT_LABEL" != "chatbot_l0027" ]; then
        echo -e "${YELLOW}⚠️  Network exists but from different project. Removing it...${NC}"
        # Disconnect all containers
        CONTAINERS=$(docker network inspect chatbot_l0027_network --format '{{range $key, $value := .Containers}}{{$key}} {{end}}' 2>/dev/null || echo "")
        if [ -n "$CONTAINERS" ]; then
            echo "$CONTAINERS" | xargs -r -n1 docker network disconnect -f chatbot_l0027_network 2>/dev/null || true
        fi
        docker network rm chatbot_l0027_network 2>/dev/null || true
        sleep 2
        echo -e "${GREEN}✅ Network removed, will be recreated by docker compose${NC}"
    elif [ "$NETWORK_LABEL" != "chatbot_network" ]; then
        # Network exists but was created manually or has wrong label
        if [ -z "$NETWORK_LABEL" ]; then
            echo -e "${YELLOW}⚠️  Network exists but was created manually (no compose labels). Removing it...${NC}"
        else
            echo -e "${YELLOW}⚠️  Network exists but with incorrect labels. Removing it...${NC}"
        fi
        # Disconnect all containers
        CONTAINERS=$(docker network inspect chatbot_l0027_network --format '{{range $key, $value := .Containers}}{{$key}} {{end}}' 2>/dev/null || echo "")
        if [ -n "$CONTAINERS" ]; then
            echo "$CONTAINERS" | xargs -r -n1 docker network disconnect -f chatbot_l0027_network 2>/dev/null || true
        fi
        docker network rm chatbot_l0027_network 2>/dev/null || true
        sleep 2
        echo -e "${GREEN}✅ Network removed, will be recreated by docker compose${NC}"
    else
        echo -e "${GREEN}✅ Network exists and is correctly configured by docker compose${NC}"
    fi
else
    echo -e "${GREEN}✅ Network will be created by docker compose${NC}"
fi

# Start Traefik
echo ""
echo -e "${BLUE}🚀 Starting Traefik...${NC}"
docker compose -f docker-compose.traefik.yml up -d

# Wait for Traefik to be ready
echo ""
echo -e "${BLUE}⏳ Waiting for Traefik to be ready...${NC}"
sleep 5

# Check Traefik status
echo ""
echo -e "${BLUE}📊 Traefik Status:${NC}"
docker compose -f docker-compose.traefik.yml ps

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Traefik Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📍 Endpoints:${NC}"
echo "   • HTTP:  http://traefik.laufane.com:8080 (Dashboard)"
echo "   • HTTPS: https://traefik.laufane.com:8080 (Dashboard)"
echo ""
echo -e "${CYAN}📝 Useful Commands:${NC}"
echo "   • View logs:       docker compose -f docker-compose.traefik.yml logs -f"
echo "   • Stop Traefik:    docker compose -f docker-compose.traefik.yml down"
echo "   • Check status:    docker compose -f docker-compose.traefik.yml ps"
echo ""

