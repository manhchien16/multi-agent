# Multi-Agent Software Engineering Platform

A production-grade platform for orchestrating hundreds of concurrent AI software engineering agents. This system handles the complete software development lifecycle from requirements to deployment with enterprise-grade governance, security, and observability.

---

## 🎯 Platform Overview

This platform enables autonomous software development at scale by coordinating specialized AI agents that can:

- **Understand Requirements**: Parse PRDs, design docs, and existing codebases
- **Generate Specifications**: Create detailed technical specifications and architecture proposals
- **Plan Implementation**: Break down work into optimized task graphs with dependency management
- **Write Code**: Generate high-quality code across multiple languages and frameworks
- **Review Code**: Perform security, performance, and architecture reviews
- **Test Code**: Create and execute comprehensive test suites
- **Evaluate Quality**: Score outputs across multiple dimensions
- **Deploy**: Automate deployment with human-in-the-loop approval for critical operations

### Key Capabilities

✅ **Production-Ready**: Designed for hundreds of concurrent agents  
✅ **Intelligent Model Routing**: Automatically selects optimal LLMs based on task requirements  
✅ **Comprehensive Governance**: Policy-driven controls with Open Policy Agent  
✅ **Advanced Guardrails**: NVIDIA NeMo for prompt injection and PII detection  
✅ **Full Observability**: Distributed tracing, metrics, and cost tracking with Langfuse  
✅ **Sandboxed Execution**: Docker + gVisor for secure code execution  
✅ **Multi-Tenancy**: Complete resource isolation and per-tenant quotas  
✅ **Event-Driven**: Asynchronous agent coordination via NATS

---

## 📊 Architecture

### System Components

```
┌─────────────────┐
│   API Gateway   │ ← REST API, Authentication, Rate Limiting
├─────────────────┤
│  Orchestrator   │ ← Temporal.io workflows, State management
├─────────────────┤
│ Governance      │ ← OPA policies, NeMo guardrails
├─────────────────┤
│ Agents Layer    │ ← 9 specialized agent types
├─────────────────┤
│ Infrastructure  │ ← NATS, PostgreSQL, Redis, Sandbox
└─────────────────┘
```

### Agent Topology

1. **Orchestrator Agent** - Workflow coordination and state management
2. **Specification Agent** - Convert PRDs to technical specifications
3. **Planner Agent** - Task graph generation and optimization
4. **Model Router Agent** - LLM selection and routing
5. **Coding Agents** (4 variants) - Backend, frontend, DevOps, database
6. **Review Agent** - Security, performance, and architecture review
7. **Test Agent** - Test generation and execution
8. **Evaluation Agent** - Multi-dimensional quality scoring
9. **Approval Agent** - Human-in-the-loop approvals

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📁 Project Structure

```
multi_agent/
├── agents/                    # Agent implementations
│   ├── shared/               # Base agent class
│   ├── spec_agent/           # Specification generation
│   ├── planner_agent/        # Task planning
│   ├── model_router/         # LLM routing
│   ├── coding_agent/         # Code generation
│   └── ...                   # Review, test, eval, approval
├── orchestrator/             # Workflow orchestration
│   ├── workflows/            # Temporal workflow definitions
│   ├── activities/           # Temporal activities
│   └── api/                  # REST API endpoints
├── infrastructure/           # Infrastructure as Code
│   ├── terraform/            # Terraform modules
│   ├── helm/                 # Helm charts
│   └── kubernetes/           # K8s manifests
├── services/                 # Supporting services
│   ├── api_gateway/          # Kong API Gateway config
│   ├── policy_engine/        # OPA policy service
│   ├── guardrails_service/   # NeMo Guardrails
│   ├── memory_service/       # Memory management
│   └── sandbox_service/      # Sandbox orchestration
├── policies/                 # OPA policy definitions
│   ├── agent_policies/       # Agent behavior policies
│   ├── resource_policies/    # Resource access policies
│   └── cost_policies/        # Cost management policies
├── schemas/                  # Data schemas
│   ├── api/                  # OpenAPI specifications
│   ├── events/               # Event schemas (JSON Schema)
│   ├── database/             # SQL migrations
│   └── data_models/          # Pydantic/TypeScript models
├── docs/                     # Documentation
│   ├── architecture/         # Architecture docs
│   ├── diagrams/             # Mermaid diagrams
│   └── operations/           # Runbooks
└── tests/                    # Test suites
    ├── integration/          # Integration tests
    ├── e2e/                  # End-to-end tests
    └── performance/          # Load tests
```

See [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) for complete structure.

---

## 🚀 Getting Started

### Prerequisites

- **Kubernetes 1.27+** (GKE, EKS, or AKS)
- **Terraform 1.5+**
- **Helm 3.12+**
- **Docker 24+**
- **PostgreSQL 15+**
- **Redis 7+**
- **NATS 2.10+**

### Quick Start (Development)

```bash
# Clone repository
git clone https://github.com/your-org/multi-agent-platform.git
cd multi-agent-platform

# Set up local development environment
./scripts/setup/init-dev.sh

# Start infrastructure services
docker-compose up -d

# Apply database migrations
./scripts/database/migrate.sh

# Start orchestrator
cd orchestrator && python -m src.main

# Start agents
cd agents/spec_agent && python -m src.agent
```

### Production Deployment

```bash
# Set up GCP project and credentials
export GCP_PROJECT="your-project-id"
gcloud auth application-default login

# Deploy infrastructure
cd infrastructure/terraform/environments/production
terraform init
terraform plan
terraform apply

# Deploy services via Helm
cd infrastructure/helm
helm install multi-agent-platform ./charts/agents \
  --namespace multi-agent-platform \
  --create-namespace \
  --values values-production.yaml

# Verify deployment
kubectl get pods -n multi-agent-platform
```

---

## 📐 Key Design Decisions

### 1. Event-Driven Architecture

**Decision**: Use NATS with JetStream for event bus  
**Rationale**: Sub-millisecond latency, native persistence, better than Kafka for real-time agent coordination

### 2. Workflow Orchestration

**Decision**: Use Temporal.io  
**Rationale**: Battle-tested durability, automatic retries, visual workflow inspection, better than custom orchestration

### 3. Sandbox Security

**Decision**: Docker + gVisor  
**Rationale**: gVisor adds syscall-level isolation beyond Docker, preventing container escapes

### 4. Model Routing

**Decision**: Dynamic model selection per task  
**Rationale**: Cost optimization while maintaining quality - use cheaper models (DeepSeek, Qwen) for simple tasks, premium models (Claude, GPT-4) for complex work

### 5. Policy Engine

**Decision**: Open Policy Agent (OPA)  
**Rationale**: Declarative policies in Rego, centralized governance, can evolve without code changes

### 6. Observability

**Decision**: Langfuse + Prometheus + Jaeger  
**Rationale**: Langfuse for LLM-specific observability (prompts, costs, evaluations), Prometheus for infrastructure metrics, Jaeger for distributed tracing

---

## 🛡️ Security Architecture

### Multi-Layer Security

1. **Perimeter**: WAF, DDoS protection, TLS 1.3
2. **Authentication**: OAuth 2.0 / OIDC with JWT
3. **Authorization**: RBAC + OPA policies
4. **Guardrails**: NVIDIA NeMo for prompt injection, PII detection
5. **Execution**: Sandboxed containers with gVisor
6. **Data**: AES-256 encryption at rest, mTLS in transit
7. **Secrets**: HashiCorp Vault with auto-rotation
8. **Monitoring**: SIEM, IDS, audit logging

See [Security Design](ARCHITECTURE.md#14-security-design) for details.

---

## 📊 Database Schema

### Core Tables

- **tenants** - Multi-tenancy configuration
- **workflows** - Workflow state and history
- **tasks** - Task definitions and results
- **agents** - Agent registry and status
- **specifications** - Technical specifications
- **evaluations** - Quality assessments
- **agent_performance** - Performance metrics
- **cost_tracking** - LLM usage costs
- **audit_logs** - Compliance audit trail
- **policy_violations** - Security violations

See [Database Schema](schemas/database/001_initial_schema.sql) for full DDL.

---

## 📡 API Reference

### Core Endpoints

#### Workflows

```
POST   /v1/workflows          - Create workflow
GET    /v1/workflows          - List workflows
GET    /v1/workflows/{id}     - Get workflow details
PATCH  /v1/workflows/{id}     - Update workflow
DELETE /v1/workflows/{id}     - Cancel workflow
GET    /v1/workflows/{id}/tasks - Get workflow tasks
GET    /v1/workflows/{id}/cost  - Get workflow cost
```

#### Tasks

```
GET    /v1/tasks/{id}         - Get task details
GET    /v1/tasks/{id}/output  - Get task output
```

#### Agents

```
GET    /v1/agents             - List agents
GET    /v1/agents/{id}        - Get agent details
GET    /v1/agents/{id}/performance - Get performance metrics
```

#### Approvals

```
GET    /v1/approvals          - List pending approvals
POST   /v1/approvals/{id}/approve  - Approve
POST   /v1/approvals/{id}/reject   - Reject
```

See [API Specification](schemas/api/orchestrator.yaml) for OpenAPI docs.

---

## 🎨 Architecture Diagrams

Comprehensive Mermaid diagrams available:

1. **System Architecture Overview** - High-level component view
2. **Agent Interaction Flow** - Communication patterns
3. **Workflow Execution Sequence** - State machine
4. **Deployment Architecture** - Kubernetes topology
5. **Data Flow** - Data pipeline
6. **Security Architecture** - Security layers
7. **Cost Optimization Flow** - Model routing

View all diagrams: [ARCHITECTURE_DIAGRAMS.md](docs/diagrams/ARCHITECTURE_DIAGRAMS.md)

---

## 💰 Cost Management

### Model Routing Strategy

The platform automatically selects cost-effective models:

| Task Type            | Preferred Model | Fallback      | Cost/1M Tokens |
| -------------------- | --------------- | ------------- | -------------- |
| Simple Code          | DeepSeek-V3     | Qwen-2.5      | $0.14          |
| Standard Code        | GPT-4o          | Claude Sonnet | $2.50          |
| Complex Architecture | Claude Opus     | GPT-4         | $15.00         |
| Code Review          | Qwen-2.5-Coder  | GPT-4o        | $0.27          |

### Budget Controls

- **Soft Limits**: Notify owner when approaching budget
- **Hard Limits**: Pause workflow and require approval
- **Per-Tenant Quotas**: Isolated cost tracking
- **Real-Time Monitoring**: Langfuse cost dashboard

---

## 📈 Scalability

### Horizontal Scaling

- **Agents**: Stateless, scale to hundreds via HPA
- **Orchestrator**: 3+ instances with leader election
- **Event Bus**: NATS cluster with 3+ nodes
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster mode

### Performance Targets

- **Workflow Creation**: < 100ms
- **Agent Response**: < 2s for simple tasks, < 30s for complex
- **Event Latency**: < 1ms
- **API Latency**: P95 < 200ms
- **Throughput**: 1000+ concurrent workflows

---

## 🧪 Testing Strategy

### Test Pyramid

```
        /\
       /E2E\       10% - End-to-end tests
      /------\
     / Integ. \    30% - Integration tests
    /----------\
   /  Unit Tests  \ 60% - Unit tests
  /----------------\
```

### Test Coverage

- Unit tests for all agent logic
- Integration tests for service interactions
- E2E tests for complete workflows
- Performance tests for scalability
- Security tests for vulnerabilities
- Chaos engineering for resilience

---

## 📚 Documentation

### Available Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete system architecture
- [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - Project organization
- [ARCHITECTURE_DIAGRAMS.md](docs/diagrams/ARCHITECTURE_DIAGRAMS.md) - Visual diagrams
- [API Reference](schemas/api/orchestrator.yaml) - OpenAPI specification
- [Database Schema](schemas/database/001_initial_schema.sql) - DDL and data model
- [Event Schemas](schemas/events/) - Event specifications
- [OPA Policies](policies/) - Governance policies

---

## 🤝 Contributing

### Development Workflow

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Run test suite (`./scripts/testing/run-all-tests.sh`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Code Standards

- **Python**: Black formatter, type hints, Pydantic models
- **TypeScript**: ESLint, Prettier, strict mode
- **Documentation**: Docstrings for all public APIs
- **Testing**: Minimum 80% code coverage
- **Security**: No secrets in code, SAST scanning

---

## 📋 Roadmap

### Phase 1: Foundation (Current)

- ✅ Core architecture design
- ✅ Base agent implementation
- ✅ Database schema
- ✅ Event schemas
- ✅ API contracts
- ✅ Infrastructure configs

### Phase 2: Agent Implementation (Next)

- ⏳ Complete all 9 agent types
- ⏳ Model router implementation
- ⏳ Sandbox service
- ⏳ Memory service

### Phase 3: Observability & Governance

- ⏳ Langfuse integration
- ⏳ OPA policy enforcement
- ⏳ NeMo guardrails
- ⏳ Audit logging

### Phase 4: Production Hardening

- ⏳ Performance optimization
- ⏳ Security hardening
- ⏳ Disaster recovery
- ⏳ Multi-region deployment

### Phase 5: Advanced Features

- ⏳ Multi-language support expansion
- ⏳ Advanced model routing with A/B testing
- ⏳ Agent learning and improvement
- ⏳ Custom agent creation SDK

---

## 📞 Support & Contact

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: platform@multi-agent.com

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:

- [Temporal.io](https://temporal.io) - Workflow orchestration
- [NATS](https://nats.io) - Event bus
- [Open Policy Agent](https://openpolicyagent.org) - Policy engine
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) - LLM guardrails
- [Langfuse](https://langfuse.com) - LLM observability
- [LangChain](https://langchain.com) - LLM framework
- [gVisor](https://gvisor.dev) - Container security
- [PostgreSQL](https://postgresql.org) - Primary database
- [Redis](https://redis.io) - Caching and state
- [Kubernetes](https://kubernetes.io) - Container orchestration

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-18  
**Status**: Production-Ready Design

# multi-agent
