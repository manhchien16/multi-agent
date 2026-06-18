#!/bin/bash

# Multi-Agent Platform - Development Startup Script
# This script starts all services for local development

set -e

echo "🚀 Starting Multi-Agent Platform (Development Mode)"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit .env file and add your API keys!${NC}"
    echo -e "${YELLOW}   Required: OPENAI_API_KEY or ANTHROPIC_API_KEY${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Start infrastructure services
echo -e "\n${GREEN}📦 Starting infrastructure services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "\n${GREEN}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check PostgreSQL
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Check Redis
echo -e "${YELLOW}Checking Redis...${NC}"
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 2
done
echo -e "${GREEN}✓ Redis is ready${NC}"

# Check NATS
echo -e "${YELLOW}Checking NATS...${NC}"
until docker-compose exec -T nats nc -zv localhost 4222 > /dev/null 2>&1; do
    echo "  Waiting for NATS..."
    sleep 2
done
echo -e "${GREEN}✓ NATS is ready${NC}"

echo -e "\n${GREEN}✅ All infrastructure services are ready!${NC}"

# Initialize database
echo -e "\n${GREEN}🗄️  Initializing database...${NC}"
./scripts/init-database.sh

# Show service URLs
echo -e "\n${GREEN}📊 Service URLs:${NC}"
echo "  PostgreSQL:    localhost:5432"
echo "  Redis:         localhost:6379"
echo "  NATS:          localhost:4222"
echo "  NATS Monitor:  http://localhost:8222"
echo ""
echo -e "${YELLOW}Optional tools (start with: docker-compose --profile tools up -d):${NC}"
echo "  pgAdmin:       http://localhost:5050 (admin@multi-agent.com / admin)"
echo "  Redis Commander: http://localhost:8081"

echo -e "\n${GREEN}🎯 Next steps:${NC}"
echo "  1. Activate Python virtual environment:"
echo "     ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "  2. Start the Orchestrator:"
echo "     ${YELLOW}cd orchestrator && python -m src.main${NC}"
echo ""
echo "  3. In new terminals, start agents:"
echo "     ${YELLOW}cd agents/spec_agent && python -m src.agent${NC}"
echo ""
echo "  4. Test the API:"
echo "     ${YELLOW}curl http://localhost:8000/health${NC}"
echo ""
echo -e "${GREEN}📖 See QUICKSTART.md for full instructions${NC}"
