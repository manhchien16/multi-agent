# 🎯 Multi-Agent Platform - Cheat Sheet

Quick reference cho các lệnh thường dùng.

---

## 🚀 Setup & Start

```bash
# 1. Setup lần đầu
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Sửa .env: thêm OPENAI_API_KEY hoặc ANTHROPIC_API_KEY

# 2. Start infrastructure
./scripts/start-dev.sh
# hoặc: docker-compose up -d

# 3. Start orchestrator
cd orchestrator && python -m src.main

# 4. Test
curl http://localhost:8000/health
```

---

## 🛑 Stop

```bash
./scripts/stop-dev.sh
# hoặc: docker-compose down
```

---

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### List Agents
```bash
curl http://localhost:8000/v1/agents
```

### Create Workflow
```bash
curl -X POST http://localhost:8000/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "demo",
    "title": "My API",
    "description": "Build a REST API",
    "prd_content": "User management with CRUD",
    "tech_stack": {"language": "python", "framework": "fastapi"}
  }'
```

### Get Workflow
```bash
curl http://localhost:8000/v1/workflows/{workflow_id}
```

### List Workflows
```bash
curl http://localhost:8000/v1/workflows
```

### Get Workflow Tasks
```bash
curl http://localhost:8000/v1/workflows/{workflow_id}/tasks
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart service
docker-compose restart postgres

# Remove everything (including data)
docker-compose down -v
```

---

## 🗄️ Database Commands

```bash
# Initialize database (first time)
./scripts/init-database.sh

# Test PostgreSQL setup
./scripts/test-postgres.sh

# Reset database (DELETE ALL DATA!)
./scripts/reset-database.sh

# Quick queries
./scripts/db-query.sh agents       # List agents
./scripts/db-query.sh workflows    # List workflows
./scripts/db-query.sh tasks        # List tasks
./scripts/db-query.sh active       # Active workflows
./scripts/db-query.sh stats        # Statistics
./scripts/db-query.sh tables       # List tables

# Custom query
./scripts/db-query.sh "SELECT * FROM workflows LIMIT 5;"

# Open psql shell
./scripts/db-query.sh shell

# Manual psql access
docker-compose exec postgres psql -U postgres -d multiagent
```

### Useful SQL Queries

```sql
-- View all agents
SELECT agent_id, agent_type, status, current_task_count FROM agents;

-- View recent workflows
SELECT workflow_id, name, status, progress_percent FROM active_workflows_summary;

-- View tasks by workflow
SELECT task_id, category, status, cost_usd 
FROM tasks 
WHERE workflow_id = 'your-workflow-id';

-- Cost summary
SELECT 
    SUM(cost_consumed_usd) as total_cost,
    COUNT(*) as workflow_count,
    AVG(cost_consumed_usd) as avg_cost
FROM workflows;
```

---

## 🔧 Development

```bash
# Activate virtual env
source venv/bin/activate

# Deactivate
deactivate

# Install new package
pip install package-name
pip freeze > requirements.txt

# Run linters
black orchestrator/
flake8 orchestrator/
mypy orchestrator/
```

---

## 🧪 Testing

```bash
# Run API tests
./scripts/test-api.sh

# Manual tests
curl http://localhost:8000/docs  # Swagger UI
curl http://localhost:8000/redoc # ReDoc
```

---

## 📊 Monitoring

```bash
# Watch workflow progress
watch -n 2 "curl -s http://localhost:8000/v1/workflows/{id} | python3 -m json.tool"

# View Docker logs
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f nats
```

---

## 🔍 Debug

```bash
# Check ports
lsof -i :8000
lsof -i :5432
lsof -i :6379
lsof -i :4222

# Check Docker
docker info
docker ps
docker stats

# Database
docker-compose exec postgres psql -U postgres -d multiagent
\dt              # List tables
\q               # Quit

# Redis
docker-compose exec redis redis-cli
PING            # Test connection
KEYS *          # List all keys
quit            # Exit
```

---

## 🌐 URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Orchestrator API | http://localhost:8000 | - |
| Swagger UI | http://localhost:8000/docs | - |
| ReDoc | http://localhost:8000/redoc | - |
| NATS Monitor | http://localhost:8222 | - |
| pgAdmin | http://localhost:5050 | admin@multi-agent.com / admin |
| Redis Commander | http://localhost:8081 | - |

---

## 💡 Quick Tips

```bash
# Pretty print JSON
curl http://localhost:8000/v1/agents | python3 -m json.tool

# Save response to file
curl http://localhost:8000/v1/agents > agents.json

# Extract workflow_id
WORKFLOW_ID=$(curl -s -X POST http://localhost:8000/v1/workflows ... | python3 -c "import sys, json; print(json.load(sys.stdin)['workflow_id'])")

# Watch logs with color
docker-compose logs -f --tail=100 | grep -E "ERROR|WARNING|INFO"
```

---

## 🚨 Common Issues

### Port already in use
```bash
lsof -i :8000
kill -9 <PID>
```

### Docker not running
```bash
open -a Docker
# Wait for Docker to start
```

### Import errors
```bash
pip install -r requirements.txt --force-reinstall
```

### Database connection error
```bash
docker-compose restart postgres
docker-compose exec postgres pg_isready -U postgres
```

---

## 📁 Important Files

```
.env                        # Configuration (API keys)
docker-compose.yml          # Infrastructure services
requirements.txt            # Python dependencies
orchestrator/src/main.py    # Orchestrator entry point
agents/*/src/agent.py       # Agent implementations
```

---

## 🎯 Example Workflows

### Simple API
```json
{
  "title": "User API",
  "prd_content": "CRUD for users",
  "tech_stack": {"language": "python", "framework": "fastapi"}
}
```

### Complex System
```json
{
  "title": "E-commerce Platform",
  "prd_content": "Product catalog, shopping cart, checkout, orders",
  "tech_stack": {
    "language": "python",
    "framework": "fastapi",
    "database": "postgresql",
    "cache": "redis"
  },
  "constraints": {
    "max_parallel_tasks": 10,
    "budget": 5.0
  }
}
```

---

**Last Updated**: 2026-06-18
