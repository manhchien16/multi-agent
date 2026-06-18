#!/bin/bash

# Multi-Agent Platform - API Test Script

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8000"

echo "🧪 Testing Multi-Agent Platform API"
echo "===================================="

# Test 1: Health Check
echo -e "\n${YELLOW}Test 1: Health Check${NC}"
RESPONSE=$(curl -s ${API_URL}/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

# Test 2: List Agents
echo -e "\n${YELLOW}Test 2: List Available Agents${NC}"
RESPONSE=$(curl -s ${API_URL}/v1/agents)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ List agents passed${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ List agents failed${NC}"
fi

# Test 3: Create Workflow
echo -e "\n${YELLOW}Test 3: Create Workflow${NC}"
RESPONSE=$(curl -s -X POST ${API_URL}/v1/workflows \
    -H "Content-Type: application/json" \
    -d '{
        "tenant_id": "demo-tenant",
        "title": "Simple REST API",
        "description": "Create a simple REST API for user management",
        "prd_content": "Build a REST API with:\n- User registration\n- User login\n- Get user profile\n- Update user profile",
        "tech_stack": {
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql"
        }
    }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Create workflow passed${NC}"
    echo "$RESPONSE" | python3 -m json.tool
    
    # Extract workflow_id
    WORKFLOW_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['workflow_id'])" 2>/dev/null)
    
    if [ -n "$WORKFLOW_ID" ]; then
        echo -e "\n${GREEN}Created workflow: $WORKFLOW_ID${NC}"
        
        # Test 4: Get Workflow
        echo -e "\n${YELLOW}Test 4: Get Workflow Details${NC}"
        sleep 2  # Give it time to process
        RESPONSE=$(curl -s ${API_URL}/v1/workflows/${WORKFLOW_ID})
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Get workflow passed${NC}"
            echo "$RESPONSE" | python3 -m json.tool
        fi
        
        # Test 5: Get Workflow Tasks
        echo -e "\n${YELLOW}Test 5: Get Workflow Tasks${NC}"
        sleep 2
        RESPONSE=$(curl -s ${API_URL}/v1/workflows/${WORKFLOW_ID}/tasks)
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Get workflow tasks passed${NC}"
            echo "$RESPONSE" | python3 -m json.tool
        fi
    fi
else
    echo -e "${RED}✗ Create workflow failed${NC}"
fi

echo -e "\n${GREEN}===================================="
echo "✅ API Testing Complete!"
echo -e "====================================${NC}"
