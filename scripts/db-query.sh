#!/bin/bash

# Quick Database Query Script
# Usage: ./scripts/db-query.sh [query or preset]

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./scripts/db-query.sh \"SELECT * FROM agents;\""
    echo ""
    echo -e "${YELLOW}Presets:${NC}"
    echo "  ./scripts/db-query.sh agents          # List all agents"
    echo "  ./scripts/db-query.sh workflows       # List all workflows"
    echo "  ./scripts/db-query.sh tasks           # List all tasks"
    echo "  ./scripts/db-query.sh tenants         # List all tenants"
    echo "  ./scripts/db-query.sh active          # Show active workflows"
    echo "  ./scripts/db-query.sh stats           # Show statistics"
    echo "  ./scripts/db-query.sh tables          # List all tables"
    echo "  ./scripts/db-query.sh shell           # Open psql shell"
    exit 0
fi

# Preset queries
case "$1" in
    agents)
        QUERY="SELECT agent_id, agent_type, status, current_task_count, max_concurrent_tasks, total_tasks_completed FROM agents;"
        ;;
    workflows)
        QUERY="SELECT workflow_id, name, status, total_tasks, completed_tasks, cost_consumed_usd, created_at FROM workflows ORDER BY created_at DESC LIMIT 20;"
        ;;
    tasks)
        QUERY="SELECT task_id, workflow_id, category, status, assigned_agent_type, cost_usd, created_at FROM tasks ORDER BY created_at DESC LIMIT 20;"
        ;;
    tenants)
        QUERY="SELECT tenant_id, name, tier, status FROM tenants;"
        ;;
    active)
        QUERY="SELECT * FROM active_workflows_summary;"
        ;;
    stats)
        QUERY="SELECT 'Tenants' as entity, COUNT(*) as count FROM tenants
               UNION ALL SELECT 'Agents', COUNT(*) FROM agents
               UNION ALL SELECT 'Workflows', COUNT(*) FROM workflows
               UNION ALL SELECT 'Tasks', COUNT(*) FROM tasks
               UNION ALL SELECT 'Active Workflows', COUNT(*) FROM workflows WHERE status IN ('pending', 'in_progress');"
        ;;
    tables)
        QUERY="\dt"
        ;;
    shell)
        echo -e "${GREEN}Opening psql shell...${NC}"
        echo -e "${YELLOW}Type \q to exit${NC}"
        docker-compose exec postgres psql -U postgres -d multiagent
        exit 0
        ;;
    *)
        QUERY="$1"
        ;;
esac

echo -e "${YELLOW}Executing query:${NC}"
echo "$QUERY"
echo ""

docker-compose exec -T postgres psql -U postgres -d multiagent -c "$QUERY"
