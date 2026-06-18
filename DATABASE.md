# 🗄️ Database Guide

Hướng dẫn làm việc với PostgreSQL database trong Multi-Agent Platform.

---

## 📊 Database Schema Overview

### Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tenants` | Multi-tenancy | tenant_id, name, tier, resource_limits |
| `workflows` | Workflow execution | workflow_id, status, total_tasks, cost_consumed_usd |
| `tasks` | Individual tasks | task_id, workflow_id, category, status, assigned_agent_type |
| `agents` | Agent registry | agent_id, agent_type, status, current_task_count |
| `specifications` | Technical specs | spec_id, workflow_id, content, user_stories |
| `evaluations` | Quality scoring | eval_id, task_id, overall_score, passed |
| `approvals` | Human approvals | approval_id, workflow_id, status, required_approvers |
| `model_usage` | LLM tracking | model_id, provider, total_tokens, cost_usd |
| `audit_logs` | Audit trail | actor_id, action, resource_type, outcome |
| `cost_tracking` | Cost analytics | tenant_id, period_start, total_cost_usd |

### Views

- `active_workflows_summary` - Live workflow status with progress
- `agent_performance_summary` - Agent metrics and health
- `tenant_cost_summary` - Cost breakdown by tenant

---

## 🚀 Quick Start

### 1. Initialize Database

```bash
# Automatic (includes in start-dev.sh)
./scripts/start-dev.sh

# Manual
./scripts/init-database.sh
```

### 2. Verify Setup

```bash
# Check tables
./scripts/db-query.sh tables

# Check sample data
./scripts/db-query.sh agents
./scripts/db-query.sh tenants
```

### 3. Reset Database (if needed)

```bash
# WARNING: Deletes all data!
./scripts/reset-database.sh
```

---

## 🔍 Querying Database

### Using Scripts

```bash
# Presets
./scripts/db-query.sh agents
./scripts/db-query.sh workflows
./scripts/db-query.sh tasks
./scripts/db-query.sh active
./scripts/db-query.sh stats

# Custom query
./scripts/db-query.sh "SELECT * FROM workflows WHERE status = 'in_progress';"

# Interactive shell
./scripts/db-query.sh shell
```

### Manual psql

```bash
# Connect
docker-compose exec postgres psql -U postgres -d multiagent

# Or from host (if you have psql)
psql postgresql://postgres:password@localhost:5432/multiagent
```

---

## 📝 Common Queries

### Workflow Management

```sql
-- List all workflows
SELECT workflow_id, name, status, total_tasks, completed_tasks, cost_consumed_usd
FROM workflows
ORDER BY created_at DESC
LIMIT 20;

-- Get workflow details
SELECT * FROM workflows WHERE workflow_id = 'your-workflow-id';

-- Active workflows with progress
SELECT * FROM active_workflows_summary;

-- Workflow tasks
SELECT task_id, category, status, assigned_agent_type, cost_usd
FROM tasks
WHERE workflow_id = 'your-workflow-id'
ORDER BY created_at;
```

### Agent Monitoring

```sql
-- All agents status
SELECT * FROM agent_performance_summary;

-- Busy agents
SELECT agent_id, agent_type, current_task_count, max_concurrent_tasks
FROM agents
WHERE status = 'busy';

-- Agent performance
SELECT agent_id, agent_type, total_tasks_completed, total_tasks_failed,
       ROUND((total_tasks_completed::DECIMAL / NULLIF(total_tasks_completed + total_tasks_failed, 0)) * 100, 2) as success_rate
FROM agents
WHERE total_tasks_completed > 0
ORDER BY success_rate DESC;
```

### Cost Analysis

```sql
-- Total cost by tenant
SELECT * FROM tenant_cost_summary;

-- Cost by workflow
SELECT workflow_id, name, cost_consumed_usd, tokens_consumed
FROM workflows
ORDER BY cost_consumed_usd DESC
LIMIT 10;

-- Cost by model
SELECT model_id, provider, 
       COUNT(*) as usage_count,
       SUM(total_tokens) as total_tokens,
       SUM(cost_usd) as total_cost,
       AVG(cost_usd) as avg_cost
FROM model_usage
GROUP BY model_id, provider
ORDER BY total_cost DESC;

-- Daily cost
SELECT DATE(created_at) as date,
       SUM(cost_usd) as daily_cost,
       SUM(total_tokens) as daily_tokens
FROM model_usage
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;
```

### Task Analytics

```sql
-- Tasks by status
SELECT status, COUNT(*) as count
FROM tasks
GROUP BY status;

-- Tasks by category
SELECT category, 
       COUNT(*) as total,
       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM tasks
GROUP BY category;

-- Average task duration by category
SELECT category,
       COUNT(*) as task_count,
       AVG(duration_ms) / 1000 as avg_duration_seconds,
       AVG(cost_usd) as avg_cost
FROM tasks
WHERE duration_ms IS NOT NULL
GROUP BY category;
```

### Quality & Evaluation

```sql
-- Evaluations summary
SELECT output_type,
       COUNT(*) as total_evals,
       AVG(overall_score) as avg_score,
       SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed_count
FROM evaluations
GROUP BY output_type;

-- Failed evaluations
SELECT e.eval_id, e.task_id, e.output_type, e.overall_score,
       e.critical_issues_count, e.feedback
FROM evaluations e
WHERE e.passed = false
ORDER BY e.critical_issues_count DESC;
```

### Audit & Security

```sql
-- Recent actions
SELECT timestamp, actor_id, action, resource_type, outcome
FROM audit_logs
ORDER BY timestamp DESC
LIMIT 50;

-- Policy violations
SELECT timestamp, agent_id, policy_name, severity, description
FROM policy_violations
ORDER BY timestamp DESC
LIMIT 20;

-- Failed actions
SELECT timestamp, actor_id, action, resource_type, details
FROM audit_logs
WHERE outcome = 'failure'
ORDER BY timestamp DESC;
```

---

## 🛠️ Database Maintenance

### Backup

```bash
# Full backup
docker-compose exec -T postgres pg_dump -U postgres multiagent > backup_$(date +%Y%m%d).sql

# Backup specific tables
docker-compose exec -T postgres pg_dump -U postgres multiagent \
    --table=workflows --table=tasks > backup_workflows_$(date +%Y%m%d).sql
```

### Restore

```bash
# From backup file
docker-compose exec -T postgres psql -U postgres multiagent < backup_20260618.sql

# Or drop and restore
docker-compose exec -T postgres psql -U postgres <<EOF
DROP DATABASE IF EXISTS multiagent;
CREATE DATABASE multiagent;
EOF

cat backup_20260618.sql | docker-compose exec -T postgres psql -U postgres multiagent
```

### Cleanup

```sql
-- Delete old completed workflows (>30 days)
DELETE FROM workflows 
WHERE status = 'completed' 
AND completed_at < NOW() - INTERVAL '30 days';

-- Delete old audit logs (>90 days)
DELETE FROM audit_logs 
WHERE timestamp < NOW() - INTERVAL '90 days';

-- Vacuum database
VACUUM ANALYZE;
```

---

## 📊 Database Schema Details

### Extensions Used

- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `vector` - pgvector for embeddings (optional)
- `pg_trgm` - Fuzzy text search

### Custom Types

```sql
-- Enums
workflow_status: pending, in_progress, completed, failed, cancelled, paused
task_status: pending, queued, assigned, in_progress, completed, failed, cancelled, retrying
agent_type: orchestrator, spec, planner, router, backend_coding, frontend_coding, ...
task_category: specification, planning, backend_coding, review, testing, ...
severity_level: critical, high, medium, low, info
```

### Indexes

All tables have appropriate indexes on:
- Primary keys (UUID)
- Foreign keys
- Status columns
- Timestamp columns (for time-based queries)
- Cost columns (for analytics)

---

## 🔧 Development Tips

### Enable Query Logging

```bash
# Edit postgresql.conf or set via SQL
docker-compose exec postgres psql -U postgres -c "ALTER SYSTEM SET log_statement = 'all';"
docker-compose restart postgres

# View logs
docker-compose logs -f postgres | grep "LOG:  statement"
```

### Analyze Query Performance

```sql
-- Enable timing
\timing on

-- Explain query
EXPLAIN ANALYZE
SELECT * FROM workflows WHERE status = 'in_progress';

-- Show slow queries (requires pg_stat_statements extension)
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Monitor Database Size

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('multiagent'));

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index sizes
SELECT tablename, indexname,
       pg_size_pretty(pg_relation_size(indexname::regclass)) AS size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

---

## 🐛 Troubleshooting

### Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres

# Check port
lsof -i :5432
```

### Reset Everything

```bash
# Stop services
docker-compose down

# Remove volumes (DELETES ALL DATA!)
docker volume rm multiagent_postgres_data

# Start fresh
docker-compose up -d
./scripts/init-database.sh
```

### Check Database Status

```sql
-- Active connections
SELECT pid, usename, application_name, client_addr, state
FROM pg_stat_activity
WHERE datname = 'multiagent';

-- Database stats
SELECT * FROM pg_stat_database WHERE datname = 'multiagent';

-- Table stats
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

---

## 📚 Resources

- PostgreSQL Docs: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector
- Schema file: [`schemas/database/001_initial_schema.sql`](schemas/database/001_initial_schema.sql)

---

**Last Updated**: 2026-06-18
