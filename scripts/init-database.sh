#!/bin/bash

# Database Initialization Script
# This script initializes the PostgreSQL database with schema and sample data

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🗄️  Initializing Database"
echo "========================="

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default database URL if not set
DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:password@localhost:5432/multiagent"}

echo -e "\n${YELLOW}Database URL: ${DATABASE_URL}${NC}"

# Check if PostgreSQL is running
echo -e "\n${YELLOW}Checking PostgreSQL connection...${NC}"
if ! docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running or not accessible${NC}"
    echo "Please start PostgreSQL with: docker-compose up -d postgres"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Check if database exists
echo -e "\n${YELLOW}Checking if database exists...${NC}"
DB_EXISTS=$(docker-compose exec -T postgres psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='multiagent'")

if [ "$DB_EXISTS" != "1" ]; then
    echo -e "${YELLOW}Creating database 'multiagent'...${NC}"
    docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE multiagent;"
    echo -e "${GREEN}✓ Database created${NC}"
else
    echo -e "${GREEN}✓ Database already exists${NC}"
fi

# Check if pgvector extension is available
echo -e "\n${YELLOW}Checking pgvector extension...${NC}"
PGVECTOR_AVAILABLE=$(docker-compose exec -T postgres psql -U postgres -d multiagent -tAc "SELECT 1 FROM pg_available_extensions WHERE name='vector'" 2>/dev/null || echo "0")

if [ "$PGVECTOR_AVAILABLE" != "1" ]; then
    echo -e "${YELLOW}⚠️  pgvector extension not available${NC}"
    echo -e "${YELLOW}Schema will be loaded without vector columns${NC}"
    # Create a modified schema without vector
    cat schemas/database/001_initial_schema.sql | \
        sed 's/CREATE EXTENSION IF NOT EXISTS "vector";//g' | \
        sed 's/embedding vector(1536)/embedding TEXT/g' | \
        sed 's/USING ivfflat (embedding vector_cosine_ops)//g' > /tmp/schema_no_vector.sql
    SCHEMA_FILE="/tmp/schema_no_vector.sql"
else
    echo -e "${GREEN}✓ pgvector extension available${NC}"
    SCHEMA_FILE="schemas/database/001_initial_schema.sql"
fi

# Apply schema
echo -e "\n${YELLOW}Applying database schema...${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent < $SCHEMA_FILE 2>&1 | grep -v "NOTICE" || true

# Check if schema was applied
TABLE_COUNT=$(docker-compose exec -T postgres psql -U postgres -d multiagent -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
echo -e "${GREEN}✓ Schema applied successfully (${TABLE_COUNT} tables created)${NC}"

# List tables
echo -e "\n${YELLOW}Tables created:${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent -c "\dt"

# Insert sample data
echo -e "\n${YELLOW}Inserting sample data...${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent <<EOF
-- Sample tenant
INSERT INTO tenants (tenant_id, name, status, tier)
VALUES 
    ('demo-tenant-0000-0000-000000000001'::uuid, 'Demo Tenant', 'active', 'pro')
ON CONFLICT (tenant_id) DO NOTHING;

-- Sample agents (register as if they're running)
INSERT INTO agents (agent_id, agent_type, version, status, max_concurrent_tasks, capabilities)
VALUES 
    ('spec-agent-001', 'spec', '2.1.0', 'idle', 5, ARRAY['prd_parsing', 'spec_generation', 'schema_design', 'api_design']),
    ('planner-agent-001', 'planner', '2.1.0', 'idle', 3, ARRAY['task_decomposition', 'dependency_analysis', 'graph_optimization']),
    ('router-agent-001', 'router', '2.1.0', 'idle', 20, ARRAY['model_selection', 'cost_optimization', 'fallback_routing']),
    ('coding-backend-001', 'backend_coding', '2.1.0', 'idle', 5, ARRAY['api_development', 'database_integration', 'authentication']),
    ('review-agent-001', 'review', '2.1.0', 'idle', 10, ARRAY['security_review', 'performance_review', 'code_quality_review']),
    ('test-agent-001', 'test', '2.1.0', 'idle', 5, ARRAY['unit_testing', 'integration_testing', 'test_data_generation'])
ON CONFLICT (agent_id) DO UPDATE SET
    status = EXCLUDED.status,
    last_heartbeat = CURRENT_TIMESTAMP;

SELECT 'Inserted ' || COUNT(*) || ' sample agents' FROM agents;
EOF

echo -e "${GREEN}✓ Sample data inserted${NC}"

# Show summary
echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}✅ Database initialized successfully!${NC}"
echo -e "${GREEN}=====================================${NC}"

echo -e "\n${YELLOW}Database Statistics:${NC}"
docker-compose exec -T postgres psql -U postgres -d multiagent <<EOF
SELECT 
    'Tenants' as entity, COUNT(*) as count FROM tenants
UNION ALL
SELECT 'Agents', COUNT(*) FROM agents
UNION ALL
SELECT 'Workflows', COUNT(*) FROM workflows
UNION ALL
SELECT 'Tasks', COUNT(*) FROM tasks;
EOF

echo -e "\n${YELLOW}Access database:${NC}"
echo "  docker-compose exec postgres psql -U postgres -d multiagent"
echo ""
echo -e "${YELLOW}Test queries:${NC}"
echo "  SELECT * FROM agents;"
echo "  SELECT * FROM tenants;"
echo "  SELECT * FROM active_workflows_summary;"
echo ""

# Clean up temp file
rm -f /tmp/schema_no_vector.sql
