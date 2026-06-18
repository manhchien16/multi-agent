#!/bin/bash

# Build Custom PostgreSQL Image with pgvector
# This is OPTIONAL - only needed if you want vector/embeddings support

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🐘 Building Custom PostgreSQL Image"
echo "===================================="

echo -e "\n${YELLOW}This builds PostgreSQL with pgvector extension for embeddings/RAG.${NC}"
echo -e "${YELLOW}This is OPTIONAL - the system works fine without it.${NC}"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Build cancelled."
    exit 0
fi

echo -e "\n${YELLOW}Building PostgreSQL image...${NC}"
echo "This may take 2-3 minutes..."

# Build the image
docker build -t multiagent-postgres:latest \
    -f docker/postgres/Dockerfile \
    docker/postgres/

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ PostgreSQL image built successfully!${NC}"
    
    # Create override file
    if [ ! -f docker-compose.override.yml ]; then
        echo -e "\n${YELLOW}Creating docker-compose.override.yml...${NC}"
        cat > docker-compose.override.yml <<EOF
version: '3.8'

services:
  postgres:
    image: multiagent-postgres:latest
EOF
        echo -e "${GREEN}✓ Override file created${NC}"
    else
        echo -e "\n${YELLOW}docker-compose.override.yml already exists${NC}"
        echo "Make sure it uses: image: multiagent-postgres:latest"
    fi
    
    echo -e "\n${GREEN}Next steps:${NC}"
    echo "1. Stop existing containers: docker-compose down"
    echo "2. Start with new image: docker-compose up -d"
    echo "3. Verify pgvector: docker-compose exec postgres psql -U postgres -d multiagent -c \"SELECT * FROM pg_extension WHERE extname='vector';\""
else
    echo -e "\n${RED}✗ Build failed${NC}"
    echo "The system will work fine with the standard PostgreSQL image."
    echo "You just won't have vector/embeddings support."
    exit 1
fi
