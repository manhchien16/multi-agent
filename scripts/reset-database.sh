#!/bin/bash

# Database Reset Script
# WARNING: This will DELETE ALL DATA and recreate the database

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}⚠️  DATABASE RESET WARNING ⚠️${NC}"
echo -e "${RED}This will DELETE ALL DATA in the database!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
echo

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

echo -e "${YELLOW}Resetting database...${NC}"

# Drop and recreate database
docker-compose exec -T postgres psql -U postgres <<EOF
DROP DATABASE IF EXISTS multiagent;
CREATE DATABASE multiagent;
EOF

echo -e "${GREEN}✓ Database dropped and recreated${NC}"

# Run init script
echo -e "\n${YELLOW}Initializing database with fresh schema...${NC}"
./scripts/init-database.sh

echo -e "\n${GREEN}✅ Database reset complete!${NC}"
