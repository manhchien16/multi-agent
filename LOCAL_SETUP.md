# 🏃 Local Setup - Chạy thử trong 5 phút

Hướng dẫn setup và chạy thử Multi-Agent Platform trên máy local của bạn.

---

## ✅ Yêu cầu

- **Python 3.11+** (check: `python3 --version`)
- **Docker Desktop** đang chạy (check: `docker ps`)
- **Git** (check: `git --version`)
- **8GB RAM** trở lên

---

## 🚀 Bước 1: Chuẩn bị môi trường

```bash
# Di chuyển vào thư mục project
cd /Users/vumanhchien/Documents/multi_agent

# Tạo virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Thời gian**: ~2 phút

---

## 🔑 Bước 2: Cấu hình API Keys

```bash
# Copy file .env mẫu
cp .env.example .env

# Sửa file .env và thêm API keys
nano .env
```

**Tối thiểu cần 1 trong 2:**
```env
OPENAI_API_KEY=sk-proj-your-key-here
# HOẶC
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Lưu file**: `Ctrl + O`, `Enter`, `Ctrl + X`

### Lấy API Keys:
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys

---

## 🐳 Bước 3: Start Infrastructure

```bash
# Chạy script tự động (recommended)
./scripts/start-dev.sh
```

Script sẽ:
- ✅ Start PostgreSQL (port 5432)
- ✅ Start Redis (port 6379)
- ✅ Start NATS (port 4222)
- ✅ Đợi tất cả services healthy
- ✅ Initialize database với schema và sample data

**Thời gian**: ~1 phút

### Hoặc chạy manual:

```bash
docker-compose up -d

# Chờ services ready
sleep 10

# Initialize database
./scripts/init-database.sh
```

### Kiểm tra services:

```bash
docker-compose ps
```

Kết quả mong đợi:
```
NAME                  STATUS
multiagent-postgres   Up (healthy)
multiagent-redis      Up (healthy)
multiagent-nats       Up (healthy)
```

---

## 🎯 Bước 4: Start Orchestrator

Mở terminal mới:

```bash
# Activate virtual environment
cd /Users/vumanhchien/Documents/multi_agent
source venv/bin/activate

# Start orchestrator
cd orchestrator
python -m src.main
```

Kết quả mong đợi:
```
INFO:     Starting Multi-Agent Orchestrator
INFO:     Services initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Giữ terminal này chạy!**

---

## 🧪 Bước 5: Test API

Mở terminal mới:

```bash
# Test health check
curl http://localhost:8000/health

# Kết quả:
{
  "status": "healthy",
  "service": "orchestrator",
  "version": "2.1.0",
  "timestamp": "2026-06-18T..."
}
```

### Chạy full test suite:

```bash
cd /Users/vumanhchien/Documents/multi_agent
./scripts/test-api.sh
```

---

## 🤖 Bước 6: Start Agents (Optional)

Nếu muốn chạy agents thực sự (không chỉ simulation), start từng agent:

### Terminal 1: Spec Agent
```bash
cd /Users/vumanhchien/Documents/multi_agent
source venv/bin/activate
cd agents/spec_agent
python -m src.agent
```

### Terminal 2: Planner Agent
```bash
cd /Users/vumanhchien/Documents/multi_agent
source venv/bin/activate
cd agents/planner_agent
python -m src.agent
```

### Terminal 3: Model Router
```bash
cd /Users/vumanhchien/Documents/multi_agent
source venv/bin/activate
cd agents/model_router
python -m src.agent
```

**Lưu ý**: Mỗi agent cần 1 terminal riêng. Nếu không muốn mở nhiều terminal, có thể dùng `tmux` hoặc chỉ chạy orchestrator (nó sẽ simulate agents).

---

## 📊 Bước 7: Tạo Workflow

```bash
curl -X POST http://localhost:8000/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant",
    "title": "User Management API",
    "description": "Build a REST API for user management",
    "prd_content": "Create a user management system with:\n- User registration with email and password\n- User login with JWT authentication\n- Get user profile\n- Update user profile\n- Delete user account",
    "tech_stack": {
      "language": "python",
      "framework": "fastapi",
      "database": "postgresql"
    },
    "constraints": {
      "max_parallel_tasks": 5,
      "budget": 1.0
    }
  }'
```

**Kết quả**:
```json
{
  "workflow_id": "abc-123-def-456",
  "tenant_id": "test-tenant",
  "title": "User Management API",
  "status": "created",
  "current_stage": "specification",
  "progress_percent": 0
}
```

---

## 👀 Bước 8: Theo dõi Workflow

```bash
# Lấy workflow_id từ response ở trên
WORKFLOW_ID="abc-123-def-456"

# Xem status
curl http://localhost:8000/v1/workflows/$WORKFLOW_ID

# Xem tasks
curl http://localhost:8000/v1/workflows/$WORKFLOW_ID/tasks

# List tất cả workflows
curl http://localhost:8000/v1/workflows
```

### Watch workflow progress:

```bash
# Auto-refresh mỗi 2 giây
watch -n 2 "curl -s http://localhost:8000/v1/workflows/$WORKFLOW_ID | python3 -m json.tool"
```

---

## 🌐 Bước 9: Xem API Documentation

Mở browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Tại đây bạn có thể:
- Xem tất cả endpoints
- Test API trực tiếp trên browser
- Xem request/response schemas

---

## 🛠️ Optional Tools

### pgAdmin (Database UI)

```bash
# Start pgAdmin
docker-compose --profile tools up -d pgadmin

# Mở browser: http://localhost:5050
# Login: admin@multi-agent.com / admin
```

### Redis Commander (Redis UI)

```bash
# Start Redis Commander
docker-compose --profile tools up -d redis-commander

# Mở browser: http://localhost:8081
```

---

## 🔍 Debug & Logs

### Xem logs của services:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f nats
```

### Xem logs của orchestrator:
Xem trực tiếp trong terminal đang chạy orchestrator.

---

## 🛑 Dừng hệ thống

```bash
# Stop infrastructure (giữ data)
./scripts/stop-dev.sh

# Hoặc manual
docker-compose down

# Stop và xóa hết data
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Port đã được sử dụng?

```bash
# Check port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Docker không chạy?

```bash
# Check Docker status
docker info

# Restart Docker Desktop
```

### Import errors?

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Virtual environment issues?

```bash
# Xóa và tạo lại
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📈 Next Steps

### 1. Thử các workflows khác:

**Frontend Component:**
```json
{
  "title": "User Dashboard",
  "description": "Build a React user dashboard",
  "tech_stack": {
    "language": "typescript",
    "framework": "react"
  }
}
```

**Database Schema:**
```json
{
  "title": "E-commerce Database",
  "description": "Design database for e-commerce",
  "tech_stack": {
    "database": "postgresql"
  }
}
```

### 2. Customize Model Router:

Edit `agents/model_router/src/agent.py` để thêm/bớt models.

### 3. Xem cost tracking:

```bash
# Tích hợp Langfuse để xem chi phí
# Thêm LANGFUSE_* keys vào .env
```

---

## 💡 Tips

1. **Use tmux** để manage multiple terminals:
```bash
brew install tmux
tmux new -s multiagent
# Ctrl+B, C để tạo window mới
# Ctrl+B, N để switch windows
```

2. **Auto-restart orchestrator** khi code thay đổi:
```bash
# Orchestrator đã có --reload mode
# Hoặc dùng watchdog
pip install watchdog
watchmedo auto-restart -d orchestrator -p '*.py' -- python -m src.main
```

3. **View JSON đẹp hơn**:
```bash
curl http://localhost:8000/v1/agents | jq
```

---

## 🎉 Hoàn thành!

Bây giờ bạn có:
- ✅ Infrastructure chạy local (PostgreSQL, Redis, NATS)
- ✅ Orchestrator API (port 8000)
- ✅ Test workflow đã chạy thành công
- ✅ API documentation (Swagger UI)

**Hệ thống đã sẵn sàng để phát triển và test!** 🚀

---

## 📞 Cần giúp?

- **Xem logs chi tiết**: Tất cả logs in ra terminal
- **Xem code**: Mở các file `.py` trong VSCode/IDE
- **Debug**: Thêm `import pdb; pdb.set_trace()` vào code
- **Questions**: Xem `ARCHITECTURE.md`, `README.md`

---

**Chúc code vui! 🎊**
