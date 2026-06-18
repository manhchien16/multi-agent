# 🐳 Docker Setup Guide

Hướng dẫn chi tiết về Docker infrastructure cho Multi-Agent Platform.

---

## 📦 Services Overview

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| PostgreSQL | postgres:15-alpine | 5432 | Primary database |
| Redis | redis:7-alpine | 6379 | Cache & sessions |
| NATS | nats:2.10-alpine | 4222, 8222 | Event bus |
| pgAdmin | dpage/pgadmin4 | 5050 | DB management (optional) |
| Redis Commander | rediscommander | 8081 | Redis UI (optional) |

---

## 🚀 Quick Start

### Standard Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### With Custom PostgreSQL (Optional - for pgvector support)

```bash
# Build custom image
./scripts/build-postgres.sh

# Start services
docker-compose up -d
```

---

## 🐘 PostgreSQL Configuration

### Standard Image (Default)
- **Image**: `postgres:15-alpine`
- **Features**: All standard PostgreSQL features
- **Size**: ~230MB
- **Startup**: Fast (~5 seconds)

### Custom Image (Optional)
- **Image**: `multiagent-postgres:latest` (build locally)
- **Features**: PostgreSQL + pgvector extension
- **Size**: ~280MB
- **Startup**: Fast (~5 seconds)
- **Build**: Required once, takes 2-3 minutes

---

## 📊 PostgreSQL Features

### Included Extensions

#### Standard (Always Available)
- ✅ `uuid-ossp` - UUID generation
- ✅ `pgcrypto` - Cryptographic functions
- ✅ `pg_trgm` - Fuzzy text search
- ✅ `pg_stat_statements` - Query performance

#### Custom Build Only
- 🔧 `pgvector` - Vector embeddings (for RAG/semantic search)

### Configuration

**Default Settings** (in `docker-compose.yml`):
```yaml
POSTGRES_DB: multiagent
POSTGRES_USER: postgres
POSTGRES_PASSWORD: password
Max Connections: 100
```

**Custom Config** (optional):
```bash
# Uncomment in docker-compose.override.yml
volumes:
  - ./config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

### Performance Tuning

Edit `config/postgresql.conf`:
```conf
shared_buffers = 256MB          # Adjust based on RAM
effective_cache_size = 1GB      # 50-75% of RAM
work_mem = 16MB                 # Per operation
max_connections = 100           # Concurrent connections
```

---

## 🔧 Advanced Setup

### Build Custom PostgreSQL

**When to use:**
- Need pgvector for embeddings/RAG
- Want to pre-install additional extensions
- Need custom compilation flags

**How to build:**
```bash
./scripts/build-postgres.sh
```

This creates:
- Custom image: `multiagent-postgres:latest`
- Override file: `docker-compose.override.yml`

**Verify pgvector:**
```bash
docker-compose exec postgres psql -U postgres -d multiagent \
  -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Use Custom Configuration

1. **Create override file:**
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

2. **Edit and uncomment custom config section:**
```yaml
postgres:
  volumes:
    - ./config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
  command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

3. **Restart:**
```bash
docker-compose down
docker-compose up -d
```

---

## 🛠️ Management

### Database Operations

```bash
# Connect to psql
docker-compose exec postgres psql -U postgres -d multiagent

# Backup database
docker-compose exec -T postgres pg_dump -U postgres multiagent > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U postgres multiagent

# Check database size
docker-compose exec postgres psql -U postgres -c "\l+"

# Check table sizes
docker-compose exec postgres psql -U postgres -d multiagent -c "\dt+"
```

### Container Management

```bash
# View logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs nats

# Follow logs
docker-compose logs -f --tail=100 postgres

# Restart specific service
docker-compose restart postgres

# Rebuild service
docker-compose up -d --build postgres

# Remove and recreate
docker-compose rm -f postgres
docker-compose up -d postgres
```

### Data Management

```bash
# View volumes
docker volume ls | grep multiagent

# Backup volume
docker run --rm \
  -v multiagent_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm \
  -v multiagent_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /data

# Remove all volumes (DANGER!)
docker-compose down -v
```

---

## 🔍 Troubleshooting

### PostgreSQL won't start

```bash
# Check logs
docker-compose logs postgres

# Common issues:
# 1. Port 5432 already in use
lsof -i :5432
# Kill process: kill -9 <PID>

# 2. Corrupted data volume
docker-compose down
docker volume rm multiagent_postgres_data
docker-compose up -d

# 3. Permission issues
docker-compose exec postgres chown -R postgres:postgres /var/lib/postgresql/data
docker-compose restart postgres
```

### Connection refused

```bash
# 1. Check if running
docker-compose ps postgres

# 2. Check network
docker network ls | grep multiagent
docker network inspect multiagent-network

# 3. Test from container
docker-compose exec postgres pg_isready -U postgres

# 4. Test from host
psql postgresql://postgres:password@localhost:5432/multiagent
```

### Slow queries

```bash
# Enable query logging
docker-compose exec postgres psql -U postgres -c \
  "ALTER SYSTEM SET log_statement = 'all';"
docker-compose restart postgres

# View slow queries
docker-compose logs postgres | grep "duration:"

# Analyze query
docker-compose exec postgres psql -U postgres -d multiagent
# Then: EXPLAIN ANALYZE <your query>;
```

### Out of space

```bash
# Check volume size
docker system df -v

# Clean up
docker system prune -a --volumes

# Check database size
docker-compose exec postgres psql -U postgres -d multiagent -c \
  "SELECT pg_size_pretty(pg_database_size('multiagent'));"
```

---

## 🔒 Security

### Production Considerations

**DO NOT use in production:**
```yaml
POSTGRES_PASSWORD: password  # ❌ Change this!
POSTGRES_HOST_AUTH_METHOD: trust  # ❌ Remove this!
```

**Production setup:**
```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      # Remove HOST_AUTH_METHOD
    secrets:
      - postgres_password

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### SSL/TLS Setup

```yaml
postgres:
  volumes:
    - ./certs/server.crt:/var/lib/postgresql/server.crt:ro
    - ./certs/server.key:/var/lib/postgresql/server.key:ro
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/var/lib/postgresql/server.crt
    -c ssl_key_file=/var/lib/postgresql/server.key
```

### Network Isolation

```yaml
# Don't expose ports in production
postgres:
  # ports:
  #   - "5432:5432"  # Remove this
  networks:
    - backend  # Internal network only
```

---

## 📊 Monitoring

### Health Checks

```bash
# Check health status
docker-compose ps

# Manual health check
docker-compose exec postgres pg_isready -U postgres -d multiagent

# Health check from another container
docker-compose exec redis sh -c \
  "nc -zv postgres 5432"
```

### Performance Monitoring

```bash
# Active connections
docker-compose exec postgres psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Database stats
docker-compose exec postgres psql -U postgres -c \
  "SELECT * FROM pg_stat_database WHERE datname = 'multiagent';"

# Slow queries (requires pg_stat_statements)
docker-compose exec postgres psql -U postgres -d multiagent -c \
  "SELECT query, calls, mean_exec_time 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;"
```

### Resource Usage

```bash
# Container stats
docker stats multiagent-postgres

# CPU and memory
docker-compose exec postgres top

# Disk usage
docker-compose exec postgres df -h
```

---

## 🛠️ Development Tools

### pgAdmin (Web UI)

```bash
# Start pgAdmin
docker-compose --profile tools up -d pgadmin

# Access: http://localhost:5050
# Email: admin@multi-agent.com
# Password: admin

# Add server in pgAdmin:
# Host: postgres
# Port: 5432
# Database: multiagent
# Username: postgres
# Password: password
```

### Command Line Tools

```bash
# psql interactive
docker-compose exec postgres psql -U postgres -d multiagent

# Quick queries
./scripts/db-query.sh agents
./scripts/db-query.sh workflows
./scripts/db-query.sh stats

# SQL file execution
docker-compose exec -T postgres psql -U postgres -d multiagent < query.sql
```

---

## 📁 File Structure

```
multi_agent/
├── docker-compose.yml              # Main compose file
├── docker-compose.override.yml     # Local overrides (gitignored)
├── config/
│   └── postgresql.conf             # Custom PG config
├── docker/
│   └── postgres/
│       ├── Dockerfile              # Custom PG image
│       └── init-scripts/           # Init SQL scripts
└── scripts/
    ├── build-postgres.sh           # Build custom image
    ├── init-database.sh            # Initialize DB
    └── db-query.sh                 # Query helper
```

---

## 🎯 Common Tasks

### Reset Everything

```bash
# Stop and remove everything
docker-compose down -v

# Start fresh
docker-compose up -d
./scripts/init-database.sh
```

### Change Password

```bash
# Stop services
docker-compose down

# Edit docker-compose.yml
# Change POSTGRES_PASSWORD

# Remove volume to force re-init
docker volume rm multiagent_postgres_data

# Start again
docker-compose up -d
```

### Upgrade PostgreSQL

```bash
# Backup first!
./scripts/db-query.sh shell
# pg_dumpall > /tmp/backup.sql

# Change version in docker-compose.yml
# FROM: postgres:15-alpine
# TO:   postgres:16-alpine

# Recreate
docker-compose down
docker volume rm multiagent_postgres_data
docker-compose up -d

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U postgres
```

---

## 💡 Tips & Tricks

### Fast Restart
```bash
# Restart without recreating
docker-compose restart postgres

# Reload config without restart
docker-compose exec postgres pg_ctl reload
```

### Debug Mode
```bash
# Enable all logging
docker-compose exec postgres psql -U postgres -c \
  "ALTER SYSTEM SET log_statement = 'all';"
docker-compose restart postgres
```

### Performance Testing
```bash
# pgbench (built into PostgreSQL)
docker-compose exec postgres pgbench -i -s 10 multiagent
docker-compose exec postgres pgbench -c 10 -t 1000 multiagent
```

---

**Status**: ✅ Complete
**Default**: Standard PostgreSQL (no build required)
**Optional**: Custom build for pgvector support
**Docs**: See [DATABASE.md](DATABASE.md) for schema details

---

**Last Updated**: 2026-06-18
