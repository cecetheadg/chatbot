#!/bin/bash

# ============================================
# Stop Development Environment
# Chatbot L0027 - Development
# ============================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stopping Development Environment${NC}"
echo -e "${BLUE}========================================${NC}"
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

# Parse command line arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes|-v)
            REMOVE_VOLUMES=true
            shift
            ;;
        --images|-i)
            REMOVE_IMAGES=true
            shift
            ;;
        --all|-a)
            REMOVE_VOLUMES=true
            REMOVE_IMAGES=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./stop-dev.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes    Remove volumes (⚠️  WARNING: This deletes all data!)"
            echo "  -i, --images     Remove Docker images"
            echo "  -a, --all        Remove volumes and images (⚠️  WARNING: Deletes all data!)"
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

# Check if services are running
if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  No services are currently running${NC}"
    
    # Still clean up if requested
    if [ "$REMOVE_VOLUMES" = true ] || [ "$REMOVE_IMAGES" = true ]; then
        echo "But cleaning up as requested..."
    else
        exit 0
    fi
fi

# Show running services
echo -e "${BLUE}📊 Currently Running Services:${NC}"
docker compose -f docker-compose.dev.yml ps

echo ""

# Confirm if removing volumes
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}⚠️  WARNING: You are about to remove all volumes!${NC}"
    echo -e "${RED}This will delete all database data, Redis cache, and Qdrant indexes!${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/N) " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Aborted.${NC}"
        exit 1
    fi
fi

# Stop services
echo -e "${BLUE}🛑 Stopping services...${NC}"

if [ "$REMOVE_VOLUMES" = true ]; then
    docker compose -f docker-compose.dev.yml down -v
    echo -e "${GREEN}✅ Services stopped and volumes removed${NC}"
else
    docker compose -f docker-compose.dev.yml down
    echo -e "${GREEN}✅ Services stopped (volumes preserved)${NC}"
fi

# Remove images if requested
if [ "$REMOVE_IMAGES" = true ]; then
    echo ""
    echo -e "${BLUE}🗑️  Removing Docker images...${NC}"
    docker compose -f docker-compose.dev.yml down --rmi local
    echo -e "${GREEN}✅ Images removed${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Development Environment Stopped!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$REMOVE_VOLUMES" = false ]; then
    echo -e "${BLUE}ℹ️  Note: Data volumes are preserved${NC}"
    echo "To remove volumes, use: ./stop-dev.sh --volumes"
    echo ""
fi

echo -e "${BLUE}📝 To start again:${NC}"
echo "   ./start-dev.sh"
echo ""

