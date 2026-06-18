# ✅ Database Initialization - Complete!

Tôi đã setup đầy đủ database initialization cho bạn.

---

## 📦 Files Created

### Scripts
1. ✅ `scripts/init-database.sh` - Initialize database with schema
2. ✅ `scripts/reset-database.sh` - Reset database (delete all data)
3. ✅ `scripts/db-query.sh` - Quick database queries

### Documentation
4. ✅ `DATABASE.md` - Complete database guide
5. ✅ Updated `LOCAL_SETUP.md` - Added database steps
6. ✅ Updated `CHEAT_SHEET.md` - Added database commands
7. ✅ Updated `start-dev.sh` - Auto-initialize database

### Database Schema
8. ✅ `schemas/database/001_initial_schema.sql` - Already exists (complete schema)

---

## 🗄️ Database Features

### Tables Created (20+ tables)
- ✅ **tenants** - Multi-tenancy
- ✅ **workflows** - Workflow execution
- ✅ **tasks** - Task management
- ✅ **agents** - Agent registry
- ✅ **specifications** - Technical specs
- ✅ **evaluations** - Quality scoring
- ✅ **approvals** - Human-in-the-loop
- ✅ **model_usage** - LLM tracking
- ✅ **audit_logs** - Compliance
- ✅ **cost_tracking** - Cost analytics
- ✅ **agent_performance** - Performance metrics
- ✅ **codebase_embeddings** - RAG support
- ✅ **lessons_learned** - Learning system
- ✅ **policy_violations** - Security
- And more...

### Views
- ✅ **active_workflows_summary** - Live workflow status
- ✅ **agent_performance_summary** - Agent metrics
- ✅ **tenant_cost_summary** - Cost breakdown

### Sample Data
- ✅ System tenant
- ✅ Demo tenant
- ✅ 6 sample agents (spec, planner, router, coding, review, test)

---

## 🚀 Quick Commands

### Initialize Database
```bash
# Automatic (part of start-dev.sh)
./scripts/start-dev.sh

# Manual
./scripts/init-database.sh
```

### Query Database
```bash
# Presets
./scripts/db-query.sh agents
./scripts/db-query.sh workflows
./scripts/db-query.sh tasks
./scripts/db-query.sh stats

# Custom
./scripts/db-query.sh "SELECT * FROM agents;"

# Shell
./scripts/db-query.sh shell
```

### Reset Database
```bash
# WARNING: Deletes all data!
./scripts/reset-database.sh
```

---

## 📊 What Gets Created

### 1. Extensions
- `uuid-ossp` - UUID generation
- `pgcrypto` - Encryption
- `vector` - Embeddings (optional, for RAG)
- `pg_trgm` - Fuzzy search

### 2. Custom Types (Enums)
```sql
workflow_status: pending, in_progress, completed, failed, cancelled, paused
task_status: pending, queued, assigned, in_progress, completed, failed, ...
agent_type: orchestrator, spec, planner, router, backend_coding, ...
task_category: specification, planning, backend_coding, review, testing, ...
severity_level: critical, high, medium, low, info
```

### 3. Triggers
- Auto-update `updated_at` timestamps
- Auto-calculate workflow progress
- Maintain aggregate counts

### 4. Indexes
- All primary/foreign keys
- Status columns
- Timestamp columns
- Cost columns
- Performance-critical queries

---

## ✅ Verification

After running `./scripts/start-dev.sh`, verify:

```bash
# 1. Check tables created
./scripts/db-query.sh tables
# Should show 20+ tables

# 2. Check sample agents
./scripts/db-query.sh agents
# Should show 6 agents

# 3. Check statistics
./scripts/db-query.sh stats
# Should show:
# - 2 tenants (system + demo)
# - 6 agents
# - 0 workflows (initially)
# - 0 tasks (initially)
```

---

## 🎯 Database Schema Highlights

### Multi-Tenancy Support
```sql
-- Each tenant has resource limits
{
  "max_concurrent_workflows": 10,
  "max_agents_per_workflow": 20,
  "max_cost_per_month_usd": 1000,
  "max_tokens_per_day": 10000000,
  "storage_limit_gb": 100
}
```

### Complete Audit Trail
```sql
-- Every action logged
audit_logs: actor_id, action, resource_type, outcome, timestamp
policy_violations: policy_name, severity, description, action_taken
```

### Cost Tracking
```sql
-- Track costs at multiple levels
- Per task: tasks.cost_usd
- Per workflow: workflows.cost_consumed_usd
- Per model: model_usage.cost_usd
- Per tenant: cost_tracking aggregate
```

### Performance Monitoring
```sql
-- Agent performance tracking
agent_performance: success_rate, avg_duration_ms, avg_cost_usd

-- Task analytics
tasks: duration_ms, retry_count, estimated_duration_ms
```

---

## 🔍 Common Queries

### Check Active Workflows
```sql
SELECT * FROM active_workflows_summary;
```

### Agent Status
```sql
SELECT agent_id, agent_type, status, current_task_count 
FROM agents;
```

### Cost Summary
```sql
SELECT 
    SUM(cost_consumed_usd) as total_cost,
    COUNT(*) as workflow_count
FROM workflows;
```

### Recent Activity
```sql
SELECT timestamp, actor_id, action, outcome 
FROM audit_logs 
ORDER BY timestamp DESC 
LIMIT 20;
```

---

## 🛠️ Maintenance

### Backup
```bash
docker-compose exec -T postgres pg_dump -U postgres multiagent > backup.sql
```

### Restore
```bash
cat backup.sql | docker-compose exec -T postgres psql -U postgres multiagent
```

### Reset (Fresh Start)
```bash
./scripts/reset-database.sh
```

---

## 📚 Documentation

Full database documentation available in:
- **[DATABASE.md](DATABASE.md)** - Complete guide
  - Schema overview
  - Common queries
  - Maintenance procedures
  - Troubleshooting

---

## 🎉 Success Indicators

✅ Database initialized when:
- `./scripts/init-database.sh` runs without errors
- `./scripts/db-query.sh tables` shows 20+ tables
- `./scripts/db-query.sh agents` shows 6 sample agents
- `./scripts/db-query.sh stats` shows correct counts

✅ Ready to use when:
- Orchestrator connects to database
- Workflows can be created via API
- Tasks are stored in database
- Agents register themselves

---

## 🚀 Next Steps

1. **Start system**: `./scripts/start-dev.sh`
2. **Verify database**: `./scripts/db-query.sh stats`
3. **Create workflow**: Use API at http://localhost:8000/docs
4. **Monitor**: `./scripts/db-query.sh workflows`

---

## 💡 Pro Tips

### Watch Database Activity
```bash
# Auto-refresh stats every 2 seconds
watch -n 2 "./scripts/db-query.sh stats"

# Watch active workflows
watch -n 5 "./scripts/db-query.sh active"
```

### Query from Code
```python
import asyncpg

conn = await asyncpg.connect(
    "postgresql://postgres:password@localhost:5432/multiagent"
)

# Query
rows = await conn.fetch("SELECT * FROM agents")
for row in rows:
    print(dict(row))
```

### Export Data
```bash
# Export workflows to CSV
./scripts/db-query.sh "COPY workflows TO '/tmp/workflows.csv' CSV HEADER;"

# Or via psql
docker-compose exec postgres psql -U postgres -d multiagent \
  -c "\COPY workflows TO '/tmp/workflows.csv' CSV HEADER"
```

---

**Status**: ✅ Complete and Ready
**Auto-runs**: Yes (part of `start-dev.sh`)
**Manual run**: `./scripts/init-database.sh`
**Documentation**: [`DATABASE.md`](DATABASE.md)

---

**Last Updated**: 2026-06-18
