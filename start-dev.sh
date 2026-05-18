#!/bin/bash

# ============================================
# Start Development Environment
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
echo -e "${BLUE}Starting Development Environment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "Please start Docker Desktop or Docker daemon."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Error: docker compose is not installed${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    if [ -f .env.example ]; then
        echo "Copying .env.example to .env..."
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration before continuing.${NC}"
    else
        echo "Please create a .env file with your configuration."
        exit 1
    fi
fi

# Parse command line arguments
WITH_TOOLS=false
FORCE_REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --tools|-t)
            WITH_TOOLS=true
            shift
            ;;
        --build|-b)
            FORCE_REBUILD=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./start-dev.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -t, --tools    Start with admin tools (pgAdmin, Redis Commander)"
            echo "  -b, --build    Force rebuild of Docker images"
            echo "  -h, --help     Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if services are already running
if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Some services are already running${NC}"
    echo "Use ./stop-dev.sh to stop them first, or:"
    echo "  docker compose -f docker-compose.dev.yml down"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build images if needed
if [ "$FORCE_REBUILD" = true ]; then
    echo -e "${BLUE}🔨 Building Docker images...${NC}"
    docker compose -f docker-compose.dev.yml build
fi

# Start services
echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"

if [ "$WITH_TOOLS" = true ]; then
    echo -e "${GREEN}Starting with admin tools...${NC}"
    docker compose -f docker-compose.dev.yml --profile tools up -d
else
    docker compose -f docker-compose.dev.yml up -d
fi

# Wait for services to be healthy
echo ""
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker compose -f docker-compose.dev.yml ps

# Wait a bit more and check health
echo ""
echo -e "${BLUE}🔍 Checking health...${NC}"
sleep 3

# Check if chatbot is responding
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chatbot is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Chatbot might still be starting...${NC}"
    echo "Check logs with: docker compose -f docker-compose.dev.yml logs -f chatbot"
fi

# Display URLs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Development Environment Started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📍 Available Endpoints:${NC}"
echo "   • Chatbot API:        http://localhost:8000"
echo "   • API Docs (Swagger): http://localhost:8000/docs"
echo "   • API Docs (ReDoc):   http://localhost:8000/redoc"
echo "   • Health Check:       http://localhost:8000/health"
echo ""

if [ "$WITH_TOOLS" = true ]; then
    echo -e "${BLUE}🔧 Admin Tools:${NC}"
    echo "   • pgAdmin:          http://localhost:5050"
    echo "     Email: admin@chatbot.local"
    echo "     Password: admin123"
    echo "   • Redis Commander:  http://localhost:8081"
    echo ""
fi

echo -e "${BLUE}💾 Database Access:${NC}"
echo "   • PostgreSQL:         localhost:5432"
echo "   • Redis:              localhost:6379"
echo "   • Qdrant:             http://localhost:6333"
echo ""

echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "   • View logs:          docker compose -f docker-compose.dev.yml logs -f"
echo "   • Stop services:      ./stop-dev.sh"
echo "   • Restart services:   ./stop-dev.sh && ./start-dev.sh"
echo "   • Status:             docker compose -f docker-compose.dev.yml ps"
echo ""

