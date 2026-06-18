# 🚀 Quick Start Guide

This guide will get you up and running with the Multi-Agent Platform in under 10 minutes.

---

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- 8GB+ RAM

---

## Step 1: Clone & Setup

```bash
# Clone repository
git clone https://github.com/your-org/multi-agent-platform.git
cd multi-agent-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required environment variables:

```env
# LLM API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/multiagent

# Redis
REDIS_URL=redis://localhost:6379

# NATS
NATS_URL=nats://localhost:4222

# Langfuse (Observability)
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Security
SECRET_KEY=your-super-secret-key-change-this
```

---

## Step 3: Start Infrastructure

```bash
# Start PostgreSQL, Redis, NATS using Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                STATUS
postgres            Up
redis               Up
nats                Up
```

---

## Step 4: Database Setup

```bash
# Run database migrations
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt"
```

---

## Step 5: Start Orchestrator

```bash
# Start the orchestrator service
cd orchestrator
python -m src.main
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal open. Open a new terminal for the next step.

---

## Step 6: Start Agents

In a new terminal:

```bash
# Activate virtual environment
source venv/bin/activate

# Start Specification Agent
cd agents/spec_agent
python -m src.agent
```

In another new terminal:

```bash
# Start Planner Agent
cd agents/planner_agent
python -m src.agent
```

Repeat for other agents (model_router, coding_agent, review_agent, test_agent).

**Tip:** Use tmux or screen for managing multiple agent processes.

---

## Step 7: Test the System

### Check Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "orchestrator",
  "version": "2.1.0"
}
```

### List Agents

```bash
curl http://localhost:8000/v1/agents
```

### Create a Workflow

```bash
curl -X POST http://localhost:8000/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "demo-tenant",
    "title": "User Management API",
    "description": "Build a REST API for user management with CRUD operations",
    "prd_content": "Create a user management system with:\n- User registration\n- User authentication\n- Profile management\n- Role-based access control",
    "tech_stack": {
      "language": "python",
      "framework": "fastapi",
      "database": "postgresql"
    }
  }'
```

Response:
```json
{
  "workflow_id": "uuid-here",
  "tenant_id": "demo-tenant",
  "title": "User Management API",
  "status": "created",
  "current_stage": "specification",
  "progress_percent": 0
}
```

### Monitor Workflow

```bash
# Get workflow status
curl http://localhost:8000/v1/workflows/{workflow_id}

# Get workflow tasks
curl http://localhost:8000/v1/workflows/{workflow_id}/tasks
```

---

## Step 8: View Results

### API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Langfuse Dashboard

1. Go to https://cloud.langfuse.com
2. View traces, costs, and performance metrics
3. Analyze LLM calls and agent behavior

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Request                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Orchestrator API   │
              │   (Port 8000)        │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐     ┌─────────┐    ┌─────────┐
    │  Spec  │────▶│ Planner │───▶│ Coding  │
    │ Agent  │     │  Agent  │    │ Agents  │
    └────────┘     └─────────┘    └────┬────┘
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                    ┌────────┐    ┌────────┐    ┌────────┐
                    │ Review │    │  Test  │    │Approval│
                    │ Agent  │    │ Agent  │    │ Agent  │
                    └────────┘    └────────┘    └────────┘
```

---

## Example Workflow Execution

### 1. Specification Agent
- Input: PRD/Requirements
- Output: Technical specification with API contracts, database schemas

### 2. Planner Agent
- Input: Technical specification
- Output: Task graph with dependencies

### 3. Model Router
- Input: Task requirements
- Output: Optimal LLM selection (cost vs quality)

### 4. Coding Agents
- Input: Task specification
- Output: Production-ready code

### 5. Review Agent
- Input: Generated code
- Output: Security, performance, quality review

### 6. Test Agent
- Input: Code to test
- Output: Comprehensive test suite

---

## Troubleshooting

### Agents not connecting?

Check NATS is running:
```bash
docker-compose logs nats
```

### Database connection error?

Verify PostgreSQL is running and accessible:
```bash
psql $DATABASE_URL -c "SELECT 1;"
```

### LLM API errors?

Check your API keys in `.env` file:
```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### Port already in use?

Change port in `orchestrator/src/main.py`:
```python
uvicorn.run("main:app", port=8001)  # Changed from 8000
```

---

## Next Steps

### Production Deployment

See [DEPLOYMENT.md](docs/operations/DEPLOYMENT.md) for:
- Kubernetes deployment
- Terraform infrastructure
- CI/CD pipeline
- Monitoring setup

### Development

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation

### Advanced Features

- **Custom Agents**: Build your own specialized agents
- **Policy Configuration**: Define OPA policies for governance
- **Cost Optimization**: Configure model routing strategies
- **Observability**: Deep dive into Langfuse analytics

---

## Demo Video

Watch a 5-minute walkthrough: [YouTube Link]

---

## Support

- 📧 Email: support@multi-agent.com
- 💬 Discord: [Join our community]
- 📚 Docs: [docs.multi-agent.com]
- 🐛 Issues: [GitHub Issues]

---

## What's Next?

✅ You're now running a multi-agent software engineering platform!

Try creating different types of workflows:
- REST APIs
- GraphQL services
- Database migrations
- Frontend components
- DevOps scripts
- Documentation

The platform will coordinate specialized agents to deliver production-ready code automatically.

Happy coding! 🚀
