# Multi-Agent Platform - Folder Structure

This document defines the complete folder structure for the Multi-Agent Software Engineering Platform.

---

## Root Directory Structure

```
multi-agent-platform/
├── README.md
├── ARCHITECTURE.md
├── FOLDER_STRUCTURE.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore
├── .github/
│   └── workflows/
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── poetry.lock
│
├── agents/                     # Agent implementations
├── orchestrator/               # Workflow orchestration service
├── infrastructure/             # IaC and deployment configs
├── services/                   # Shared services
├── policies/                   # OPA policies
├── guardrails/                 # Guardrail configurations
├── schemas/                    # Data schemas and contracts
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── tests/                      # Integration and E2E tests
└── monitoring/                 # Observability configurations
```

---

## Detailed Structure

### 1. Agents Directory

```
agents/
├── README.md
├── shared/                     # Shared agent utilities
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── llm_client.py          # LLM client wrapper
│   ├── memory_client.py       # Memory system client
│   ├── event_client.py        # Event bus client
│   ├── policy_client.py       # Policy engine client
│   ├── observability.py       # Tracing and logging
│   ├── sandbox.py             # Sandbox utilities
│   └── tools/                 # Shared tools
│       ├── file_operations.py
│       ├── git_operations.py
│       ├── code_analysis.py
│       └── semantic_search.py
│
├── spec_agent/                # Specification Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py           # Entry point
│   │   ├── agent.py          # Core agent logic
│   │   ├── parsers/          # Document parsers
│   │   │   ├── prd_parser.py
│   │   │   ├── figma_parser.py
│   │   │   └── openapi_parser.py
│   │   ├── generators/       # Output generators
│   │   │   ├── spec_generator.py
│   │   │   ├── schema_generator.py
│   │   │   └── architecture_generator.py
│   │   ├── prompts/          # Prompt templates
│   │   │   ├── system_prompt.txt
│   │   │   ├── spec_generation.txt
│   │   │   └── risk_analysis.txt
│   │   └── models/           # Data models
│   │       ├── specification.py
│   │       ├── user_story.py
│   │       └── schema.py
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── planner_agent/             # Planning Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── task_decomposer.py
│   │   ├── dependency_analyzer.py
│   │   ├── complexity_estimator.py
│   │   ├── graph_builder.py
│   │   ├── optimizer.py
│   │   ├── prompts/
│   │   └── models/
│   │       ├── task.py
│   │       ├── task_graph.py
│   │       └── estimate.py
│   └── tests/
│
├── model_router/              # Model Router Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── router.py         # Core routing logic
│   │   ├── model_registry.py # Model catalog
│   │   ├── scoring_engine.py # Model scoring
│   │   ├── performance_tracker.py
│   │   ├── cost_calculator.py
│   │   ├── fallback_handler.py
│   │   ├── config/
│   │   │   └── models.yaml   # Model configurations
│   │   └── models/
│   │       ├── model_config.py
│   │       ├── routing_decision.py
│   │       └── performance_metrics.py
│   └── tests/
│
├── coding_agents/             # Coding Agents
│   ├── shared/                # Shared coding utilities
│   │   ├── code_generator.py
│   │   ├── code_validator.py
│   │   ├── linter.py
│   │   └── formatter.py
│   │
│   ├── backend_agent/        # Backend Coding Agent
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── agent.py
│   │   │   ├── generators/
│   │   │   │   ├── api_generator.py
│   │   │   │   ├── business_logic_generator.py
│   │   │   │   └── database_access_generator.py
│   │   │   ├── templates/    # Code templates
│   │   │   └── prompts/
│   │   └── tests/
│   │
│   ├── frontend_agent/       # Frontend Coding Agent
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── main.ts
│   │   │   ├── agent.ts
│   │   │   ├── generators/
│   │   │   │   ├── component_generator.ts
│   │   │   │   ├── state_generator.ts
│   │   │   │   └── style_generator.ts
│   │   │   └── templates/
│   │   └── tests/
│   │
│   ├── devops_agent/         # DevOps Coding Agent
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── agent.py
│   │   │   ├── generators/
│   │   │   │   ├── terraform_generator.py
│   │   │   │   ├── docker_generator.py
│   │   │   │   └── cicd_generator.py
│   │   │   └── templates/
│   │   └── tests/
│   │
│   └── database_agent/       # Database Agent
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── src/
│       │   ├── main.py
│       │   ├── agent.py
│       │   ├── schema_designer.py
│       │   ├── migration_generator.py
│       │   ├── query_optimizer.py
│       │   └── templates/
│       └── tests/
│
├── review_agent/             # Review Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── reviewers/
│   │   │   ├── security_reviewer.py
│   │   │   ├── performance_reviewer.py
│   │   │   ├── architecture_reviewer.py
│   │   │   └── standards_reviewer.py
│   │   ├── analyzers/
│   │   │   ├── static_analyzer.py
│   │   │   ├── complexity_analyzer.py
│   │   │   └── vulnerability_scanner.py
│   │   ├── report_generator.py
│   │   ├── prompts/
│   │   └── models/
│   │       ├── review_result.py
│   │       └── issue.py
│   └── tests/
│
├── test_agent/               # Test Generation Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── generators/
│   │   │   ├── unit_test_generator.py
│   │   │   ├── integration_test_generator.py
│   │   │   └── e2e_test_generator.py
│   │   ├── test_executor.py
│   │   ├── coverage_analyzer.py
│   │   ├── prompts/
│   │   └── models/
│   │       ├── test_suite.py
│   │       └── coverage_report.py
│   └── tests/
│
├── evaluation_agent/         # Evaluation Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── evaluators/
│   │   │   ├── accuracy_evaluator.py
│   │   │   ├── completeness_evaluator.py
│   │   │   ├── security_evaluator.py
│   │   │   ├── maintainability_evaluator.py
│   │   │   └── performance_evaluator.py
│   │   ├── scoring_engine.py
│   │   ├── report_generator.py
│   │   ├── prompts/
│   │   └── models/
│   │       ├── evaluation_result.py
│   │       └── metrics.py
│   └── tests/
│
└── approval_agent/           # Human Approval Agent
    ├── Dockerfile
    ├── pyproject.toml
    ├── README.md
    ├── src/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── agent.py
    │   ├── approval_manager.py
    │   ├── notifier.py
    │   ├── timeout_handler.py
    │   ├── ui/               # Approval dashboard
    │   │   ├── frontend/
    │   │   └── backend/
    │   └── models/
    │       ├── approval_request.py
    │       └── approval_decision.py
    └── tests/
```

### 2. Orchestrator Directory

```
orchestrator/
├── Dockerfile
├── pyproject.toml
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point
│   ├── server.py             # HTTP server
│   ├── workflow_engine.py    # Core workflow logic
│   ├── state_manager.py      # Workflow state management
│   ├── event_handler.py      # Event processing
│   ├── task_scheduler.py     # Task assignment
│   ├── executor.py           # Workflow execution
│   ├── api/                  # REST API
│   │   ├── __init__.py
│   │   ├── workflows.py      # Workflow endpoints
│   │   ├── tasks.py          # Task endpoints
│   │   ├── agents.py         # Agent endpoints
│   │   └── status.py         # Status endpoints
│   ├── workflows/            # Workflow definitions
│   │   ├── software_development.yaml
│   │   ├── bug_fix.yaml
│   │   └── feature_development.yaml
│   ├── temporal/             # Temporal.io integration
│   │   ├── activities.py
│   │   ├── workflows.py
│   │   └── worker.py
│   └── models/
│       ├── workflow.py
│       ├── task.py
│       └── execution_context.py
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### 3. Infrastructure Directory

```
infrastructure/
├── README.md
├── terraform/                # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   ├── modules/
│   │   ├── kubernetes/
│   │   │   ├── main.tf
│   │   │   ├── cluster.tf
│   │   │   ├── node_pools.tf
│   │   │   └── networking.tf
│   │   ├── database/
│   │   │   ├── main.tf
│   │   │   ├── postgresql.tf
│   │   │   ├── redis.tf
│   │   │   └── backup.tf
│   │   ├── messaging/
│   │   │   ├── main.tf
│   │   │   └── nats.tf
│   │   ├── networking/
│   │   │   ├── main.tf
│   │   │   ├── vpc.tf
│   │   │   ├── load_balancer.tf
│   │   │   └── dns.tf
│   │   ├── monitoring/
│   │   │   ├── main.tf
│   │   │   ├── prometheus.tf
│   │   │   ├── grafana.tf
│   │   │   └── langfuse.tf
│   │   └── security/
│   │       ├── main.tf
│   │       ├── vault.tf
│   │       └── opa.tf
│   └── environments/
│       ├── dev/
│       │   ├── main.tf
│       │   └── terraform.tfvars
│       ├── staging/
│       │   ├── main.tf
│       │   └── terraform.tfvars
│       └── production/
│           ├── main.tf
│           └── terraform.tfvars
│
├── helm/                     # Kubernetes deployments
│   ├── charts/
│   │   ├── agents/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   │       ├── deployment.yaml
│   │   │       ├── service.yaml
│   │   │       ├── hpa.yaml
│   │   │       ├── configmap.yaml
│   │   │       └── secrets.yaml
│   │   ├── orchestrator/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   ├── data-stores/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   ├── observability/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   └── security/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       └── templates/
│   └── values/
│       ├── dev.yaml
│       ├── staging.yaml
│       └── production.yaml
│
├── kubernetes/               # Raw Kubernetes manifests
│   ├── namespaces/
│   ├── rbac/
│   ├── network-policies/
│   ├── pod-security-policies/
│   └── service-mesh/
│       └── istio/
│
└── docker/                   # Docker configurations
    ├── base-images/
    │   ├── python-agent/
    │   │   └── Dockerfile
    │   └── node-agent/
    │       └── Dockerfile
    └── docker-compose/
        ├── dev.yml
        ├── local.yml
        └── test.yml
```

### 4. Services Directory

```
services/
├── api_gateway/              # API Gateway service
│   ├── kong/
│   │   ├── kong.yml
│   │   └── plugins/
│   └── config/
│
├── policy_engine/            # Policy enforcement service
│   ├── Dockerfile
│   ├── src/
│   │   ├── main.py
│   │   ├── policy_enforcer.py
│   │   ├── decision_cache.py
│   │   └── audit_logger.py
│   └── tests/
│
├── guardrails_service/       # Guardrails service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── src/
│   │   ├── main.py
│   │   ├── input_guardrails.py
│   │   ├── output_guardrails.py
│   │   ├── operational_guardrails.py
│   │   ├── detectors/
│   │   │   ├── prompt_injection.py
│   │   │   ├── pii_detector.py
│   │   │   ├── secret_scanner.py
│   │   │   └── infinite_loop_detector.py
│   │   └── config/
│   │       └── guardrails.yaml
│   └── tests/
│
├── memory_service/           # Memory management service
│   ├── Dockerfile
│   ├── src/
│   │   ├── main.py
│   │   ├── memory_manager.py
│   │   ├── long_term_memory.py
│   │   ├── short_term_memory.py
│   │   ├── embeddings_manager.py
│   │   └── retrieval_engine.py
│   └── tests/
│
├── sandbox_service/          # Sandbox management
│   ├── Dockerfile
│   ├── src/
│   │   ├── main.py
│   │   ├── sandbox_manager.py
│   │   ├── container_pool.py
│   │   ├── resource_limiter.py
│   │   └── cleanup_service.py
│   └── tests/
│
└── notification_service/     # Notifications
    ├── Dockerfile
    ├── src/
    │   ├── main.py
    │   ├── notifier.py
    │   ├── channels/
    │   │   ├── email.py
    │   │   ├── slack.py
    │   │   └── webhook.py
    │   └── templates/
    └── tests/
```

### 5. Policies Directory

```
policies/
├── README.md
├── agent_policies/           # Agent behavior policies
│   ├── file_operations.rego
│   ├── git_operations.rego
│   ├── api_calls.rego
│   ├── resource_limits.rego
│   └── tool_usage.rego
│
├── deployment_policies/      # Deployment policies
│   ├── approval_requirements.rego
│   ├── environment_restrictions.rego
│   ├── change_windows.rego
│   └── rollback_requirements.rego
│
├── security_policies/        # Security policies
│   ├── authentication.rego
│   ├── authorization.rego
│   ├── data_access.rego
│   ├── encryption.rego
│   └── audit_logging.rego
│
├── cost_policies/            # Cost control policies
│   ├── budget_limits.rego
│   ├── token_limits.rego
│   └── resource_quotas.rego
│
└── tests/                    # Policy tests
    ├── agent_policies_test.rego
    ├── deployment_policies_test.rego
    ├── security_policies_test.rego
    └── cost_policies_test.rego
```

### 6. Guardrails Directory

```
guardrails/
├── README.md
├── config/
│   ├── guardrails.yaml      # Main configuration
│   ├── input_rules.yaml
│   ├── output_rules.yaml
│   └── operational_rules.yaml
│
├── rails/                    # NeMo Guardrails configurations
│   ├── input_rails.co
│   ├── output_rails.co
│   ├── dialog_rails.co
│   └── retrieval_rails.co
│
├── models/                   # ML models for detection
│   ├── prompt_injection/
│   ├── pii_detection/
│   └── toxicity_detection/
│
└── tests/
    ├── test_input_guardrails.py
    ├── test_output_guardrails.py
    └── test_operational_guardrails.py
```

### 7. Schemas Directory

```
schemas/
├── README.md
├── api/                      # API contracts
│   ├── openapi/
│   │   ├── orchestrator.yaml
│   │   ├── agents.yaml
│   │   └── services.yaml
│   └── grpc/
│       ├── orchestrator.proto
│       ├── agents.proto
│       └── services.proto
│
├── events/                   # Event schemas
│   ├── workflow_events.json
│   ├── task_events.json
│   ├── agent_events.json
│   ├── approval_events.json
│   └── system_events.json
│
├── database/                 # Database schemas
│   ├── migrations/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_add_evaluations.sql
│   │   └── ...
│   ├── models/
│   │   ├── workflows.sql
│   │   ├── tasks.sql
│   │   ├── agents.sql
│   │   ├── evaluations.sql
│   │   └── audit_logs.sql
│   └── indexes/
│       └── performance_indexes.sql
│
└── data_models/              # Shared data models
    ├── python/
    │   ├── workflow.py
    │   ├── task.py
    │   ├── agent.py
    │   └── evaluation.py
    └── typescript/
        ├── workflow.ts
        ├── task.ts
        ├── agent.ts
        └── evaluation.ts
```

### 8. Documentation Directory

```
docs/
├── README.md
├── getting-started/
│   ├── installation.md
│   ├── quick-start.md
│   ├── configuration.md
│   └── first-workflow.md
│
├── architecture/
│   ├── overview.md
│   ├── agent-topology.md
│   ├── event-bus.md
│   ├── memory-architecture.md
│   ├── security.md
│   └── diagrams/
│       ├── system-architecture.mmd
│       ├── agent-interaction.mmd
│       ├── deployment.mmd
│       └── sequence-diagrams/
│
├── agents/                   # Agent documentation
│   ├── spec-agent.md
│   ├── planner-agent.md
│   ├── model-router.md
│   ├── coding-agents.md
│   ├── review-agent.md
│   ├── test-agent.md
│   ├── evaluation-agent.md
│   └── approval-agent.md
│
├── api/                      # API documentation
│   ├── rest-api.md
│   ├── webhooks.md
│   └── authentication.md
│
├── operations/               # Operational docs
│   ├── deployment.md
│   ├── monitoring.md
│   ├── troubleshooting.md
│   ├── disaster-recovery.md
│   ├── scaling.md
│   └── runbooks/
│       ├── incident-response.md
│       ├── rollback.md
│       └── data-recovery.md
│
├── development/              # Developer docs
│   ├── contributing.md
│   ├── coding-standards.md
│   ├── testing.md
│   ├── debugging.md
│   └── agent-development.md
│
└── security/                 # Security docs
    ├── security-model.md
    ├── threat-model.md
    ├── penetration-testing.md
    └── compliance.md
```

### 9. Scripts Directory

```
scripts/
├── README.md
├── setup/                    # Setup scripts
│   ├── install-dependencies.sh
│   ├── setup-local-env.sh
│   └── create-secrets.sh
│
├── deployment/               # Deployment scripts
│   ├── deploy-dev.sh
│   ├── deploy-staging.sh
│   ├── deploy-production.sh
│   └── rollback.sh
│
├── database/                 # Database scripts
│   ├── migrate.sh
│   ├── seed-data.sh
│   ├── backup.sh
│   └── restore.sh
│
├── testing/                  # Testing scripts
│   ├── run-unit-tests.sh
│   ├── run-integration-tests.sh
│   ├── run-e2e-tests.sh
│   └── generate-coverage.sh
│
├── utilities/                # Utility scripts
│   ├── generate-api-docs.sh
│   ├── lint-all.sh
│   ├── format-all.sh
│   └── security-scan.sh
│
└── monitoring/               # Monitoring scripts
    ├── health-check.sh
    ├── collect-metrics.sh
    └── generate-report.sh
```

### 10. Tests Directory

```
tests/
├── README.md
├── integration/              # Integration tests
│   ├── test_workflow_execution.py
│   ├── test_agent_communication.py
│   ├── test_event_bus.py
│   └── test_policy_enforcement.py
│
├── e2e/                      # End-to-end tests
│   ├── test_software_development_workflow.py
│   ├── test_bug_fix_workflow.py
│   ├── test_feature_development.py
│   └── scenarios/
│       ├── simple_api.yaml
│       ├── fullstack_app.yaml
│       └── microservice.yaml
│
├── performance/              # Performance tests
│   ├── load_test.py
│   ├── stress_test.py
│   └── scalability_test.py
│
├── security/                 # Security tests
│   ├── penetration_tests.py
│   ├── policy_validation.py
│   └── vulnerability_scan.py
│
├── fixtures/                 # Test fixtures
│   ├── sample_prd.md
│   ├── sample_openapi.yaml
│   └── sample_code.py
│
└── utils/                    # Test utilities
    ├── test_helpers.py
    ├── mock_services.py
    └── assertions.py
```

### 11. Monitoring Directory

```
monitoring/
├── README.md
├── prometheus/               # Prometheus config
│   ├── prometheus.yml
│   ├── alerts/
│   │   ├── agents.yml
│   │   ├── infrastructure.yml
│   │   ├── security.yml
│   │   └── cost.yml
│   └── recording_rules/
│       ├── agent_rules.yml
│       └── workflow_rules.yml
│
├── grafana/                  # Grafana dashboards
│   ├── dashboards/
│   │   ├── system-overview.json
│   │   ├── agent-performance.json
│   │   ├── workflow-metrics.json
│   │   ├── cost-tracking.json
│   │   ├── security-monitoring.json
│   │   └── llm-usage.json
│   └── provisioning/
│       ├── datasources.yml
│       └── dashboards.yml
│
├── langfuse/                 # Langfuse configuration
│   ├── config.yaml
│   └── dashboards/
│
├── elasticsearch/            # Log management
│   ├── index-templates/
│   ├── pipelines/
│   └── ilm-policies/
│
└── alertmanager/             # Alert routing
    ├── alertmanager.yml
    └── templates/
        ├── email.tmpl
        └── slack.tmpl
```

---

## File Organization Principles

### 1. **Separation of Concerns**
- Each agent is self-contained with its own dependencies
- Shared utilities are extracted to `agents/shared/`
- Services are independent and loosely coupled

### 2. **Discoverability**
- Clear naming conventions
- README in every major directory
- Documentation co-located with code

### 3. **Scalability**
- Modular structure allows independent scaling
- Clear boundaries between components
- Easy to add new agents without refactoring

### 4. **Testability**
- Tests co-located with code (`tests/` in each module)
- Integration tests at top level
- Clear separation of test types

### 5. **Deployability**
- Each agent has its own Dockerfile
- Helm charts for Kubernetes deployment
- Environment-specific configurations

### 6. **Maintainability**
- Consistent structure across agents
- Infrastructure as Code for reproducibility
- Comprehensive documentation

---

## Development Workflow

### Local Development Structure

```
# Developer workspace layout
workspace/
├── multi-agent-platform/     # Main repository
│   └── [all directories above]
│
└── sandboxes/                # Local sandboxes for testing
    ├── sandbox-1/
    ├── sandbox-2/
    └── ...
```

### Environment Variables

Store in `.env` files (not committed):

```
.env.dev
.env.staging
.env.production
```

### Configuration Management

Configuration hierarchy:
1. Default configs in code
2. Environment-specific configs (dev/staging/prod)
3. Secrets from Vault (production)
4. Environment variables (override all)

---

## Naming Conventions

### Files
- Python: `snake_case.py`
- TypeScript: `camelCase.ts` or `PascalCase.tsx` (React components)
- Config files: `kebab-case.yaml`
- Shell scripts: `kebab-case.sh`

### Directories
- All lowercase with underscores: `agent_name/`
- No spaces in directory names

### Docker Images
- Format: `registry/component:version`
- Example: `agents/coding:2.1.0`

### Helm Charts
- Format: `chart-name`
- Example: `multi-agent-orchestrator`

---

## Summary

This folder structure provides:

✅ **Clear Separation**: Each component is independent  
✅ **Scalability**: Easy to add new agents or services  
✅ **Maintainability**: Consistent structure across the platform  
✅ **Deployability**: Ready for containerization and Kubernetes  
✅ **Testability**: Tests at unit, integration, and E2E levels  
✅ **Observability**: Built-in monitoring and logging  
✅ **Security**: Policies and guardrails baked in  
✅ **Documentation**: Comprehensive docs for all components  

The structure supports production-grade operations with hundreds of concurrent agents while maintaining developer productivity and code quality.
