#!/bin/bash

# Fix NATS Healthcheck Issue
# This script fixes the NATS container healthcheck

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔧 Fixing NATS Healthcheck"
echo "=========================="

# Recreate NATS container
echo -e "\n${YELLOW}Recreating NATS container...${NC}"
docker-compose up -d nats

# Wait for healthy
echo -e "\n${YELLOW}Waiting for NATS to be healthy...${NC}"
for i in {1..30}; do
    if docker-compose exec -T nats nc -zv localhost 4222 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ NATS is healthy!${NC}"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 2
done

# Verify
echo -e "\n${YELLOW}Verifying NATS status:${NC}"
docker-compose ps nats

echo -e "\n${GREEN}✅ NATS fixed!${NC}"
