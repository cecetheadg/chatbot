#!/bin/bash

# ============================================
# Production Deployment Script
# Chatbot L0027 - Optimized for 100,000+ Users
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
echo -e "${CYAN}Chatbot L0027 - Production Deployment${NC}"
echo -e "${CYAN}Optimized for 100,000+ Users${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check system resources
check_resources() {
    echo -e "${BLUE}📊 Checking system resources...${NC}"
    
    # Check RAM
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_ram" -lt 32 ]; then
        echo -e "${YELLOW}⚠️  Warning: System has ${total_ram}GB RAM, recommended: 32GB${NC}"
    else
        echo -e "${GREEN}✅ RAM: ${total_ram}GB${NC}"
    fi
    
    # Check disk space
    disk_available=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$disk_available" -lt 100 ]; then
        echo -e "${YELLOW}⚠️  Warning: ${disk_available}GB disk available, recommended: 100GB${NC}"
    else
        echo -e "${GREEN}✅ Disk: ${disk_available}GB available${NC}"
    fi
    
    # Check CPU cores
    cpu_cores=$(nproc)
    echo -e "${BLUE}ℹ️  CPU Cores: ${cpu_cores}${NC}"
    
    echo ""
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Error: Docker is not running${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
    
    # Check if Docker Compose is available
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Error: docker compose is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose is installed${NC}"
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
        if [ -f .env.example ]; then
            echo "Copying .env.example to .env..."
            cp .env.example .env
            echo -e "${RED}⚠️  Please edit .env file with your production configuration!${NC}"
            echo "Press Enter after editing .env file..."
            read
        else
            echo "Please create a .env file with your configuration."
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ Configuration file found${NC}"
    
    echo ""
}

# Parse command line arguments
SCALE_INSTANCES=4
REBUILD=false
SKIP_CHECKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --instances|-i)
            SCALE_INSTANCES="$2"
            shift 2
            ;;
        --rebuild|-b)
            REBUILD=true
            shift
            ;;
        --skip-checks|-s)
            SKIP_CHECKS=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./deploy-production.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -i, --instances N   Number of chatbot instances to scale (default: 4)"
            echo "  -b, --rebuild       Force rebuild of Docker images"
            echo "  -s, --skip-checks   Skip resource and prerequisite checks"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run checks
if [ "$SKIP_CHECKS" = false ]; then
    check_resources
    check_prerequisites
fi

# Confirm deployment
echo -e "${YELLOW}⚠️  This will deploy in PRODUCTION mode with:${NC}"
echo "   • ${SCALE_INSTANCES} chatbot instances"
echo "   • Optimized for 100,000+ users"
echo "   • High-performance configuration"
echo ""
read -p "Continue with deployment? (yes/N) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 1
fi

# Build images if needed
if [ "$REBUILD" = true ]; then
    echo -e "${BLUE}🔨 Building Docker images...${NC}"
    docker compose -f docker-compose.prod.yml build --no-cache
fi

# Stop existing services and remove network
echo -e "${BLUE}🛑 Stopping existing services...${NC}"
docker compose -f docker-compose.prod.yml --profile production down 2>/dev/null || true

# Check network (should be created by Traefik first)
echo -e "${BLUE}🌐 Checking network configuration...${NC}"
if ! docker network inspect chatbot_l0027_network >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Network 'chatbot_l0027_network' doesn't exist!${NC}"
    echo -e "${YELLOW}⚠️  Please start Traefik first: ./start-traefik.sh${NC}"
    echo ""
    read -p "Continue anyway? Traefik might create it. (y/N) " -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled. Please start Traefik first.${NC}"
        exit 1
    fi
    echo -e "${BLUE}ℹ️  Network will be created automatically...${NC}"
else
    echo -e "${GREEN}✅ Network exists (managed by Traefik)${NC}"
fi

# Start services with scaling
echo ""
echo -e "${BLUE}🚀 Starting production services...${NC}"
if [ "$SCALE_INSTANCES" -gt 1 ]; then
    echo -e "${BLUE}📈 Scaling chatbot to ${SCALE_INSTANCES} instances...${NC}"
    # Use --scale flag for docker compose (container_name removed to allow scaling)
    docker compose -f docker-compose.prod.yml --profile production up -d --scale chatbot=${SCALE_INSTANCES}
else
    docker compose -f docker-compose.prod.yml --profile production up -d
fi

# Wait for services to be ready
echo ""
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker compose -f docker-compose.prod.yml --profile production ps

# Check health
echo ""
echo -e "${BLUE}🏥 Checking service health...${NC}"
sleep 10

# Check chatbot health
if curl -f http://localhost:8000/health > /dev/null 2>&1 || curl -f https://chatbot.dfgp.fonctionpublique.gov.gn/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chatbot is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Chatbot might still be starting...${NC}"
    echo "Check logs with: docker compose -f docker-compose.prod.yml logs -f chatbot"
fi

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Production Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📊 Deployment Summary:${NC}"
echo "   • Chatbot Instances: ${SCALE_INSTANCES}"
echo "   • Workers per instance: 8"
echo "   • Total Workers: $((SCALE_INSTANCES * 8))"
echo "   • Expected Capacity: ~$((SCALE_INSTANCES * 800)) concurrent users"
echo ""
echo -e "${CYAN}📍 Endpoints:${NC}"
echo "   • Production URL: https://chatbot.dfgp.fonctionpublique.gov.gn"
echo "   • Health Check: https://chatbot.dfgp.fonctionpublique.gov.gn/health"
echo "   • API Docs: https://chatbot.dfgp.fonctionpublique.gov.gn/docs"
echo ""
echo -e "${CYAN}📝 Useful Commands:${NC}"
echo "   • View logs:       docker compose -f docker-compose.prod.yml logs -f"
echo "   • Check status:    docker compose -f docker-compose.prod.yml ps"
echo "   • Stop services:   docker compose -f docker-compose.prod.yml --profile production down"
echo "   • Monitor resources: docker stats"
echo ""
echo -e "${CYAN}🔧 Traefik Management (Separate):${NC}"
echo "   • Start Traefik:   ./start-traefik.sh"
echo "   • Stop Traefik:    ./stop-traefik.sh"
echo "   • Traefik logs:    docker compose -f docker-compose.traefik.yml logs -f"
echo ""
echo -e "${CYAN}📚 Documentation:${NC}"
echo "   • Scaling Guide: SCALING.md"
echo "   • Production Guide: PRODUCTION.md"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "   1. Monitor resource usage closely for first few days"
echo "   2. Adjust scaling based on actual traffic patterns"
echo "   3. Set up automated backups"
echo "   4. Configure monitoring and alerting"
echo ""
