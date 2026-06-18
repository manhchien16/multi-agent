#!/bin/bash

# Test PostgreSQL Setup
# Quick verification that PostgreSQL is working correctly

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🧪 Testing PostgreSQL Setup"
echo "==========================="

# Test 1: Container running
echo -e "\n${YELLOW}Test 1: Container Status${NC}"
if docker-compose ps postgres | grep -q "Up"; then
    echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL container is not running${NC}"
    exit 1
fi

# Test 2: Health check
echo -e "\n${YELLOW}Test 2: Health Check${NC}"
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not ready${NC}"
    exit 1
fi

# Test 3: Database exists
echo -e "\n${YELLOW}Test 3: Database Exists${NC}"
DB_EXISTS=$(docker-compose exec -T postgres psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='multiagent'" 2>/dev/null)
if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Database 'multiagent' exists${NC}"
else
    echo -e "${RED}✗ Database 'multiagent' does not exist${NC}"
    exit 1
fi

# Test 4: Extensions
echo -e "\n${YELLOW}Test 4: Extensions${NC}"
echo "Checking installed extensions..."
docker-compose exec -T postgres psql -U postgres -d multiagent -tA -c "SELECT extname FROM pg_extension ORDER BY extname;" | while read ext; do
    echo -e "  ${GREEN}✓${NC} $ext"
done

# Test 5: Tables
echo -e "\n${YELLOW}Test 5: Tables${NC}"
TABLE_COUNT=$(docker-compose exec -T postgres psql -U postgres -d multiagent -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null)
if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found ${TABLE_COUNT} tables${NC}"
else
    echo -e "${YELLOW}⚠ No tables found. Run: ./scripts/init-database.sh${NC}"
fi

# Test 6: Connection from host
echo -e "\n${YELLOW}Test 6: Connection from Host${NC}"
if command -v psql > /dev/null 2>&1; then
    if psql postgresql://postgres:password@localhost:5432/multiagent -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Can connect from host${NC}"
    else
        echo -e "${YELLOW}⚠ Cannot connect from host (psql installed but connection failed)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ psql not installed on host (this is OK)${NC}"
fi

# Test 7: Write test
echo -e "\n${YELLOW}Test 7: Write/Read Test${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent <<EOF > /dev/null 2>&1
CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, data TEXT);
INSERT INTO test_table (data) VALUES ('test');
SELECT * FROM test_table;
DROP TABLE test_table;
EOF
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Can write and read data${NC}"
else
    echo -e "${RED}✗ Cannot write/read data${NC}"
    exit 1
fi

# Test 8: Performance
echo -e "\n${YELLOW}Test 8: Performance${NC}"
START=$(date +%s%N)
docker-compose exec -T postgres psql -U postgres -d multiagent -c "SELECT 1" > /dev/null 2>&1
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
echo -e "Query latency: ${DURATION}ms"
if [ "$DURATION" -lt 100 ]; then
    echo -e "${GREEN}✓ Performance is good (<100ms)${NC}"
else
    echo -e "${YELLOW}⚠ Performance could be better (>${DURATION}ms)${NC}"
fi

# Summary
echo -e "\n${GREEN}=============================${NC}"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo -e "${GREEN}=============================${NC}"

# Show info
echo -e "\n${YELLOW}PostgreSQL Info:${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent <<EOF
SELECT version();
SELECT pg_size_pretty(pg_database_size('multiagent')) as database_size;
EOF

echo -e "\n${YELLOW}Quick Stats:${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent -tA -c \
  "SELECT 'Tables' as metric, COUNT(*) as count FROM information_schema.tables WHERE table_schema='public'
   UNION ALL
   SELECT 'Extensions', COUNT(*) FROM pg_extension
   UNION ALL
   SELECT 'Connections', COUNT(*) FROM pg_stat_activity;" | \
   column -t -s '|'
