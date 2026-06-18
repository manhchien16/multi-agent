# Multi-Agent Platform - Architecture Diagrams

This directory contains visual representations of the system architecture using Mermaid diagrams.

## Diagrams

1. **System Architecture Overview** - High-level view of all components
2. **Agent Interaction Flow** - How agents communicate and coordinate
3. **Workflow Execution Sequence** - Step-by-step workflow execution
4. **Deployment Architecture** - Kubernetes deployment structure
5. **Data Flow** - How data flows through the system
6. **Security Architecture** - Security layers and controls

---

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "External"
        USER[User/Client]
        GIT[Git Repository]
        LLM[LLM Providers<br/>OpenAI, Anthropic, Google]
    end
    
    subgraph "API Gateway Layer"
        APIGW[API Gateway<br/>Kong]
        AUTH[Authentication<br/>JWT/OAuth2]
    end
    
    subgraph "Orchestration Layer"
        ORCH[Orchestrator<br/>Temporal.io]
        STATE[State Manager<br/>PostgreSQL]
    end
    
    subgraph "Governance Layer"
        OPA[Policy Engine<br/>OPA]
        GUARD[Guardrails<br/>NeMo]
    end
    
    subgraph "Agent Layer"
        SPEC[Spec Agent]
        PLAN[Planner Agent]
        ROUTER[Model Router]
        CODE[Coding Agents]
        REV[Review Agent]
        TEST[Test Agent]
        EVAL[Evaluation Agent]
        APPR[Approval Agent]
    end
    
    subgraph "Execution Layer"
        SANDBOX[Sandboxes<br/>Docker + gVisor]
        TOOLS[Tool Execution]
    end
    
    subgraph "Infrastructure Layer"
        NATS[Event Bus<br/>NATS]
        REDIS[Short-term Memory<br/>Redis]
        PG[Long-term Memory<br/>PostgreSQL]
        S3[Artifact Storage<br/>S3]
        PROM[Observability<br/>Langfuse + Prometheus]
    end
    
    USER --> APIGW
    APIGW --> AUTH
    AUTH --> ORCH
    
    ORCH --> OPA
    ORCH --> GUARD
    ORCH --> SPEC
    ORCH --> PLAN
    
    PLAN --> ROUTER
    ROUTER --> CODE
    ROUTER --> REV
    ROUTER --> TEST
    
    CODE --> EVAL
    REV --> EVAL
    TEST --> EVAL
    
    EVAL --> APPR
    
    SPEC -.-> NATS
    PLAN -.-> NATS
    CODE -.-> NATS
    REV -.-> NATS
    TEST -.-> NATS
    EVAL -.-> NATS
    APPR -.-> NATS
    
    CODE --> SANDBOX
    TEST --> SANDBOX
    
    SANDBOX --> TOOLS
    TOOLS --> GIT
    
    CODE --> LLM
    SPEC --> LLM
    REV --> LLM
    
    ORCH --> STATE
    SPEC --> PG
    EVAL --> PG
    
    CODE --> REDIS
    ORCH --> REDIS
    
    CODE --> S3
    SPEC --> S3
    
    ORCH --> PROM
    CODE --> PROM
    REV --> PROM
    
    style APIGW fill:#e1f5ff
    style ORCH fill:#fff3e0
    style OPA fill:#ffebee
    style GUARD fill:#ffebee
    style NATS fill:#f3e5f5
    style SANDBOX fill:#e8f5e9
```

---

## 2. Agent Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant API as API Gateway
    participant Orch as Orchestrator
    participant Spec as Spec Agent
    participant Plan as Planner Agent
    participant Router as Model Router
    participant Code as Coding Agent
    participant Rev as Review Agent
    participant Test as Test Agent
    participant Eval as Evaluation Agent
    participant Appr as Approval Agent
    participant NATS as Event Bus
    
    User->>API: Create Workflow (PRD)
    API->>Orch: Initialize Workflow
    Orch->>NATS: workflow.started
    
    Orch->>Spec: Generate Specification
    Spec->>Router: Request Model
    Router-->>Spec: Claude Opus
    Spec->>Spec: Generate Spec
    Spec->>NATS: spec.completed
    Spec-->>Orch: Specification
    
    Orch->>Plan: Create Task Plan
    Plan->>Plan: Build DAG
    Plan->>NATS: plan.completed
    Plan-->>Orch: Task Graph
    
    loop For Each Task
        Orch->>Router: Route Task
        Router-->>Orch: Model Selection
        
        Orch->>Code: Execute Task
        Code->>Code: Generate Code
        Code->>NATS: task.completed
        Code-->>Orch: Code + Artifacts
        
        Orch->>Rev: Review Code
        Rev->>Rev: Security + Quality Check
        Rev->>NATS: review.completed
        Rev-->>Orch: Review Result
        
        alt Review Failed
            Rev-->>Orch: Reject
            Orch->>Code: Retry Task
        end
        
        Orch->>Test: Generate Tests
        Test->>Test: Create + Execute Tests
        Test->>NATS: test.completed
        Test-->>Orch: Test Results
        
        Orch->>Eval: Evaluate Output
        Eval->>Eval: Score Quality
        Eval->>NATS: eval.completed
        Eval-->>Orch: Evaluation Score
    end
    
    Orch->>Appr: Request Deployment Approval
    Appr->>User: Notification
    User->>Appr: Approve
    Appr->>NATS: approval.granted
    Appr-->>Orch: Approved
    
    Orch->>Code: Deploy
    Code->>Code: Execute Deployment
    Orch->>NATS: workflow.completed
    Orch-->>API: Workflow Result
    API-->>User: Success
```

---

## 3. Workflow Execution Sequence (Detailed)

```mermaid
stateDiagram-v2
    [*] --> WorkflowCreated
    
    WorkflowCreated --> SpecificationGeneration: Start
    
    SpecificationGeneration --> PlanningTasks: Spec Complete
    SpecificationGeneration --> Failed: Error
    
    PlanningTasks --> TaskExecution: Plan Ready
    PlanningTasks --> Failed: Error
    
    state TaskExecution {
        [*] --> ModelRouting
        ModelRouting --> Coding
        Coding --> Review
        Review --> Testing: Approved
        Review --> Coding: Rejected (Retry)
        Testing --> Evaluation
        Evaluation --> [*]: Task Complete
    }
    
    TaskExecution --> MoreTasks: Tasks Remaining
    TaskExecution --> AllTasksComplete: No More Tasks
    
    MoreTasks --> TaskExecution
    
    AllTasksComplete --> ApprovalRequired: Production Deploy
    AllTasksComplete --> WorkflowComplete: Auto-deploy
    
    ApprovalRequired --> PendingApproval
    PendingApproval --> Approved: Human Approval
    PendingApproval --> Rejected: Human Rejection
    PendingApproval --> Timeout: Approval Timeout
    
    Approved --> Deployment
    Rejected --> Failed
    Timeout --> Failed
    
    Deployment --> WorkflowComplete: Success
    Deployment --> Failed: Deploy Error
    
    WorkflowComplete --> [*]
    Failed --> [*]
```

---

## 4. Deployment Architecture (Kubernetes)

```mermaid
graph TB
    subgraph "Ingress"
        LB[Load Balancer]
        INGRESS[Ingress Controller]
    end
    
    subgraph "Control Plane Nodes"
        direction TB
        ORCH1[Orchestrator Pod 1]
        ORCH2[Orchestrator Pod 2]
        ORCH3[Orchestrator Pod 3]
        APIGW1[API Gateway Pod]
        ROUTER1[Model Router Pod]
    end
    
    subgraph "Execution Plane Nodes"
        direction TB
        SPEC1[Spec Agent Pod]
        SPEC2[Spec Agent Pod]
        CODE1[Coding Agent Pod 1]
        CODE2[Coding Agent Pod 2]
        CODE3[Coding Agent Pod N]
        REV1[Review Agent Pod]
        TEST1[Test Agent Pod]
    end
    
    subgraph "Data Plane Nodes"
        direction TB
        PG1[PostgreSQL Primary]
        PG2[PostgreSQL Replica]
        REDIS1[Redis Master]
        REDIS2[Redis Replica]
        NATS1[NATS Node 1]
        NATS2[NATS Node 2]
        NATS3[NATS Node 3]
    end
    
    subgraph "Observability"
        PROM[Prometheus]
        GRAF[Grafana]
        LANG[Langfuse]
    end
    
    LB --> INGRESS
    INGRESS --> APIGW1
    
    APIGW1 --> ORCH1
    APIGW1 --> ORCH2
    APIGW1 --> ORCH3
    
    ORCH1 --> ROUTER1
    ORCH2 --> ROUTER1
    
    ROUTER1 --> SPEC1
    ROUTER1 --> CODE1
    ROUTER1 --> CODE2
    ROUTER1 --> CODE3
    ROUTER1 --> REV1
    ROUTER1 --> TEST1
    
    SPEC1 --> NATS1
    CODE1 --> NATS2
    CODE2 --> NATS2
    REV1 --> NATS3
    
    ORCH1 --> PG1
    ORCH2 --> PG1
    ORCH3 --> PG1
    PG1 --> PG2
    
    CODE1 --> REDIS1
    CODE2 --> REDIS1
    REDIS1 --> REDIS2
    
    ORCH1 --> PROM
    CODE1 --> LANG
    REV1 --> LANG
    
    PROM --> GRAF
    
    style LB fill:#e3f2fd
    style INGRESS fill:#e3f2fd
    style ORCH1 fill:#fff3e0
    style ORCH2 fill:#fff3e0
    style ORCH3 fill:#fff3e0
    style CODE1 fill:#e8f5e9
    style CODE2 fill:#e8f5e9
    style CODE3 fill:#e8f5e9
    style PG1 fill:#f3e5f5
    style REDIS1 fill:#f3e5f5
    style NATS1 fill:#f3e5f5
```

---

## 5. Data Flow Architecture

```mermaid
flowchart LR
    subgraph "Inputs"
        PRD[Product Requirements]
        FIGMA[Figma Designs]
        API_SPEC[API Documentation]
        REPO[Existing Codebase]
    end
    
    subgraph "Processing"
        PARSE[Parse & Extract]
        EMBED[Generate Embeddings]
        ANALYZE[Analyze Context]
        GEN[Generate Artifacts]
    end
    
    subgraph "Storage"
        VECTOR[(Vector DB<br/>Embeddings)]
        RELATIONAL[(Relational DB<br/>Structured Data)]
        CACHE[(Cache<br/>Temp Data)]
        OBJECT[(Object Store<br/>Artifacts)]
    end
    
    subgraph "Outputs"
        SPEC[Technical Spec]
        CODE[Source Code]
        TESTS[Test Suites]
        DOCS[Documentation]
        DEPLOY[Deployment Artifacts]
    end
    
    PRD --> PARSE
    FIGMA --> PARSE
    API_SPEC --> PARSE
    REPO --> PARSE
    
    PARSE --> EMBED
    PARSE --> ANALYZE
    
    EMBED --> VECTOR
    ANALYZE --> RELATIONAL
    ANALYZE --> GEN
    
    VECTOR --> ANALYZE
    RELATIONAL --> ANALYZE
    CACHE --> ANALYZE
    
    GEN --> OBJECT
    
    GEN --> SPEC
    GEN --> CODE
    GEN --> TESTS
    GEN --> DOCS
    GEN --> DEPLOY
    
    SPEC --> OBJECT
    CODE --> OBJECT
    TESTS --> OBJECT
    DOCS --> OBJECT
    DEPLOY --> OBJECT
    
    style PARSE fill:#e1f5ff
    style EMBED fill:#f3e5f5
    style ANALYZE fill:#fff3e0
    style GEN fill:#e8f5e9
```

---

## 6. Security Architecture

```mermaid
graph TB
    subgraph "Perimeter Security"
        WAF[Web Application Firewall]
        DDOS[DDoS Protection]
        TLS[TLS 1.3 Termination]
    end
    
    subgraph "Authentication & Authorization"
        OAUTH[OAuth 2.0 / OIDC]
        JWT[JWT Validation]
        RBAC[Role-Based Access Control]
    end
    
    subgraph "Policy Layer"
        OPA[Open Policy Agent]
        POLICIES[Policy Repository]
        AUDIT[Audit Logger]
    end
    
    subgraph "Guardrails Layer"
        INPUT_GUARD[Input Guardrails]
        OUTPUT_GUARD[Output Guardrails]
        OPERATIONAL_GUARD[Operational Guardrails]
    end
    
    subgraph "Execution Security"
        SANDBOX[Sandboxed Containers]
        GVISOR[gVisor Runtime]
        NETPOL[Network Policies]
        SECCOMP[Seccomp Profiles]
    end
    
    subgraph "Data Security"
        ENCRYPT_REST[Encryption at Rest<br/>AES-256]
        ENCRYPT_TRANSIT[Encryption in Transit<br/>mTLS]
        VAULT[Secrets Management<br/>HashiCorp Vault]
        DLP[Data Loss Prevention]
    end
    
    subgraph "Monitoring & Response"
        SIEM[Security Information<br/>& Event Management]
        IDS[Intrusion Detection]
        INCIDENT[Incident Response]
    end
    
    WAF --> TLS
    TLS --> OAUTH
    OAUTH --> JWT
    JWT --> RBAC
    
    RBAC --> OPA
    OPA --> POLICIES
    OPA --> AUDIT
    
    OPA --> INPUT_GUARD
    INPUT_GUARD --> OUTPUT_GUARD
    OUTPUT_GUARD --> OPERATIONAL_GUARD
    
    OPERATIONAL_GUARD --> SANDBOX
    SANDBOX --> GVISOR
    SANDBOX --> NETPOL
    SANDBOX --> SECCOMP
    
    SANDBOX --> ENCRYPT_REST
    SANDBOX --> ENCRYPT_TRANSIT
    SANDBOX --> VAULT
    SANDBOX --> DLP
    
    AUDIT --> SIEM
    DLP --> SIEM
    IDS --> SIEM
    SIEM --> INCIDENT
    
    style WAF fill:#ffebee
    style OPA fill:#ffebee
    style SANDBOX fill:#e8f5e9
    style ENCRYPT_REST fill:#e3f2fd
    style SIEM fill:#fff3e0
```

---

## 7. Cost Tracking & Optimization Flow

```mermaid
flowchart TD
    START[Task Execution Start]
    
    START --> ROUTER{Model Router}
    
    ROUTER --> ANALYZE[Analyze Task<br/>- Category<br/>- Context Size<br/>- Latency Req<br/>- Budget]
    
    ANALYZE --> SELECT[Select Optimal Model]
    
    SELECT --> CHEAP{Cost-Effective<br/>Model Available?}
    
    CHEAP -->|Yes| USE_CHEAP[Use Cheaper Model<br/>DeepSeek, Qwen]
    CHEAP -->|No, Need Quality| USE_PREMIUM[Use Premium Model<br/>Claude, GPT-4]
    
    USE_CHEAP --> EXECUTE[Execute Task]
    USE_PREMIUM --> EXECUTE
    
    EXECUTE --> TRACK[Track Usage<br/>- Tokens<br/>- Cost<br/>- Latency]
    
    TRACK --> CHECK_BUDGET{Budget<br/>Exceeded?}
    
    CHECK_BUDGET -->|No| CONTINUE[Continue]
    CHECK_BUDGET -->|Soft Limit| NOTIFY[Notify Owner]
    CHECK_BUDGET -->|Hard Limit| PAUSE[Pause Workflow]
    
    NOTIFY --> CONTINUE
    PAUSE --> APPROVAL{Request<br/>Approval}
    
    APPROVAL -->|Approved| CONTINUE
    APPROVAL -->|Rejected| STOP[Stop Workflow]
    
    CONTINUE --> STORE[Store Metrics<br/>- PostgreSQL<br/>- TimescaleDB]
    
    STORE --> ANALYZE_PERF[Analyze Performance<br/>- Success Rate<br/>- Cost Efficiency<br/>- Quality Score]
    
    ANALYZE_PERF --> UPDATE_ROUTING[Update Routing<br/>Decisions]
    
    UPDATE_ROUTING --> END[End]
    STOP --> END
    
    style ROUTER fill:#fff3e0
    style SELECT fill:#e8f5e9
    style TRACK fill:#e3f2fd
    style CHECK_BUDGET fill:#ffebee
```

---

## Diagram Rendering

These Mermaid diagrams can be rendered in:
- GitHub README files (native support)
- VS Code with Mermaid extensions
- Online tools like [Mermaid Live Editor](https://mermaid.live/)
- Documentation sites (GitBook, MkDocs, etc.)
- Exported to PNG/SVG using Mermaid CLI

---

## Updating Diagrams

When updating diagrams:
1. Edit the Mermaid syntax in this file
2. Validate syntax in Mermaid Live Editor
3. Update version/date in commit message
4. Link to diagrams from main documentation

---

**Last Updated:** 2026-06-18  
**Version:** 1.0.0
